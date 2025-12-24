import spotipy
import json
import tele
import os
import re
from spotipy.oauth2 import SpotifyOAuth

from tele import TELEGRAM_CACHE

scope = 'playlist-modify-public'
username = os.environ['USERNAME']
playlist_id = os.environ['PLAYLIST_ID']

auth_manager=SpotifyOAuth(scope=scope)
spotify = spotipy.Spotify(auth_manager=auth_manager)

unfound = []
SPOTIFY_CACHE = "spotify.json"

def clean_metadata(text):
    """Remove extra metadata like [tags], file extensions, etc."""
    if not text:
        return ""
    # Remove content in square brackets like [toastermag]
    text = re.sub(r'\[.*?\]', '', text)
    # Remove file extensions
    text = re.sub(r'\.(mp3|m4a|flac|wav)$', '', text, flags=re.IGNORECASE)
    # Remove extra whitespace
    text = ' '.join(text.split())
    return text.strip()

def normalize_features(title):
    """Normalize different feature formats for more lenient matching"""
    if not title:
        return ""
    # Convert different feature formats to a simpler form
    # (feat. X) -> with X
    # (ft. X) -> with X
    title = re.sub(r'\(feat\.\s*([^)]+)\)', r'with \1', title, flags=re.IGNORECASE)
    title = re.sub(r'\(ft\.\s*([^)]+)\)', r'with \1', title, flags=re.IGNORECASE)
    return title

def search_track_with_fallback(song, artist):
    """Search for a track using multiple strategies with fallback"""
    clean_song = clean_metadata(song)
    clean_artist = clean_metadata(artist)

    # Strategy 1: Strict search with track: and artist: filters
    query = f"track:{clean_song} artist:{clean_artist}"
    results = spotify.search(q=query, type="track", market="US", limit=1)['tracks']['items']
    if results:
        return results[0]

    # Strategy 2: Try with normalized features
    normalized_song = normalize_features(clean_song)
    if normalized_song != clean_song:
        query = f"track:{normalized_song} artist:{clean_artist}"
        results = spotify.search(q=query, type="track", market="US", limit=1)['tracks']['items']
        if results:
            return results[0]

    # Strategy 3: Try without filters (more lenient)
    query = f"{clean_song} {clean_artist}"
    results = spotify.search(q=query, type="track", market="US", limit=5)['tracks']['items']
    # Find best match in top 5 results
    for result in results:
        result_title_lower = result['name'].lower()
        result_artists_lower = [a['name'].lower() for a in result['artists']]
        clean_song_lower = clean_song.lower().split('(')[0].strip()  # Remove everything after (
        if clean_song_lower in result_title_lower and any(clean_artist.lower() in ra for ra in result_artists_lower):
            return result

    # Strategy 4: Very lenient - just return first result if it's close
    if results:
        return results[0]

    return None

if auth_manager:
    tracks = []
    tracks_in_playlist = []
    tracks_found = 0
    tracks_missing = 0

    playlist_name = spotify.playlist(playlist_id, fields='name')['name']
    page_size = 100  # Use fixed page size for pagination

    print(f"Getting the list of track URIs from playlist [{playlist_name}].")

    paginate = 0
    while True:
        print(f"Fetching track URIs starting from offset {paginate}...")
        response = spotify.playlist_items(playlist_id, fields='items(track(uri))', limit=page_size, offset=paginate)
        items_in_playlist = response['items']

        if not items_in_playlist:
            break

        for track in items_in_playlist:
            if track['track'] and track['track']['uri']:
                tracks_in_playlist.append(track['track']['uri'])
        print(f"  Added {len(items_in_playlist)} URIs to list.")
        paginate += page_size

    print(f"Got [{len(tracks_in_playlist)}] track URIs from playlist [{playlist_name}].")

    if os.path.exists(SPOTIFY_CACHE):
        print(f"Spotify cache exists, getting track URIs from it.")

        with open(SPOTIFY_CACHE, 'r', encoding="utf-8") as f:
            tracks = json.load(f)

        print(f"Got [{len(tracks)}] tracks from cache.")
    else:
        print(f"Searching among [{len(tele.songs)}] tracks that were extracted from Telegram and don't exist in Spotify playlist.")

        for idx, (song, artist) in enumerate(tele.songs, 1):
            print(f"\nSearching [{idx}/{len(tele.songs)}]: {song} - {artist}")
            print(f"  Initial query: track:{song} artist:{artist}")

            result = search_track_with_fallback(song, artist)

            if result:
                uri = result['uri']
                result_title = result['name']
                result_artists = ', '.join([a['name'] for a in result['artists']])
                print(f"  Found: {result_title} by {result_artists}")
                if uri not in tracks_in_playlist:
                    tracks.append(uri)
                    tracks_found += 1
                    print(f"  ✓ Added to queue (URI: {uri})")
                else:
                    print(f"  Already in playlist")
            else:
                tracks_missing += 1
                print(f"  ✗ Not found on Spotify")

        print(f"Finished searching for songs from Telegram export. "
              f"Stats: found {tracks_found} tracks, missing - {tracks_missing}, new to playlist - {len(tracks)}.")


    with open(SPOTIFY_CACHE, 'w', encoding="utf-8") as f:
        json.dump(tracks, f, ensure_ascii=False)

    print(f"Updating Spotify playlist with {len(tracks)} tracks.")

    paginate = 0
    while paginate < len(tracks):
        next_page = paginate + 50
        paged_tracks = tracks[paginate:next_page]
        paginate = next_page
        print(f"Adding [{len(paged_tracks)}] tracks to playlist [{playlist_name}].")
        spotify.playlist_add_items(playlist_id, paged_tracks)

    print(f"Clearing local Spotify and Telegram cache.")
    if os.path.exists(SPOTIFY_CACHE):
        os.remove(SPOTIFY_CACHE)
    if os.path.exists(TELEGRAM_CACHE):
        os.remove(TELEGRAM_CACHE)
