import spotipy
import json
import tele
import os
import re
import time
from spotipy.oauth2 import SpotifyOAuth
from requests.exceptions import ReadTimeout, ConnectionError
from spotipy.exceptions import SpotifyException

from tele import TELEGRAM_CACHE

scope = 'playlist-modify-public'
username = os.environ['USERNAME']
playlist_id = os.environ['PLAYLIST_ID']

# Increase timeout and configure retry settings
auth_manager=SpotifyOAuth(scope=scope)
spotify = spotipy.Spotify(
    auth_manager=auth_manager,
    requests_timeout=30,  # Increase timeout to 30 seconds
    retries=3,  # Enable built-in retries
    status_forcelist=(429, 500, 502, 503, 504),  # Retry on these status codes
    backoff_factor=1  # Exponential backoff: 1s, 2s, 4s
)

unfound = []
SPOTIFY_CACHE = "spotify.json"

# Rate limiting: track last request time to avoid hitting 30-second rolling window
_last_request_time = 0
_request_delay = 0.1  # 100ms delay between requests to stay well under rate limit

def spotify_api_call_with_retry(func, *args, max_retries=5, initial_delay=1, **kwargs):
    """
    Wrapper for Spotify API calls with exponential backoff retry logic.
    Handles timeouts, connection errors, and rate limiting (429).
    Includes proactive throttling to avoid hitting rate limits.
    """
    global _last_request_time

    # Proactive rate limiting: add delay between requests
    time_since_last = time.time() - _last_request_time
    if time_since_last < _request_delay:
        time.sleep(_request_delay - time_since_last)

    delay = initial_delay
    last_exception = None

    for attempt in range(max_retries):
        try:
            _last_request_time = time.time()
            return func(*args, **kwargs)
        except (ReadTimeout, ConnectionError) as e:
            last_exception = e
            if attempt < max_retries - 1:
                print(f"  Timeout/connection error (attempt {attempt + 1}/{max_retries}), retrying in {delay}s...")
                time.sleep(delay)
                delay *= 2  # Exponential backoff
            else:
                print(f"  Failed after {max_retries} attempts due to timeout/connection error")
        except SpotifyException as e:
            last_exception = e
            if e.http_status == 429:  # Rate limit error
                retry_after = int(e.headers.get('Retry-After', delay))
                print(f"  Rate limited (429), waiting {retry_after}s before retry...")
                time.sleep(retry_after)
                delay = retry_after
            elif attempt < max_retries - 1:
                print(f"  Spotify API error (attempt {attempt + 1}/{max_retries}), retrying in {delay}s...")
                time.sleep(delay)
                delay *= 2
            else:
                print(f"  Failed after {max_retries} attempts due to Spotify API error")
        except Exception as e:
            # Unexpected error - don't retry
            print(f"  Unexpected error: {type(e).__name__}: {e}")
            raise

    # If we exhausted all retries, raise the last exception
    if last_exception:
        raise last_exception


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
    try:
        results = spotify_api_call_with_retry(
            lambda: spotify.search(q=query, type="track", market="US", limit=1)['tracks']['items']
        )
        if results:
            return results[0]
    except Exception as e:
        print(f"  Strategy 1 failed: {e}")

    # Strategy 2: Try with normalized features
    normalized_song = normalize_features(clean_song)
    if normalized_song != clean_song:
        query = f"track:{normalized_song} artist:{clean_artist}"
        try:
            results = spotify_api_call_with_retry(
                lambda: spotify.search(q=query, type="track", market="US", limit=1)['tracks']['items']
            )
            if results:
                return results[0]
        except Exception as e:
            print(f"  Strategy 2 failed: {e}")

    # Strategy 3: Try without filters (more lenient)
    query = f"{clean_song} {clean_artist}"
    try:
        results = spotify_api_call_with_retry(
            lambda: spotify.search(q=query, type="track", market="US", limit=5)['tracks']['items']
        )
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
    except Exception as e:
        print(f"  Strategy 3/4 failed: {e}")

    return None

if auth_manager:
    tracks = []
    tracks_in_playlist = []
    tracks_found = 0
    tracks_missing = 0

    playlist_name = spotify_api_call_with_retry(
        lambda: spotify.playlist(playlist_id, fields='name')['name']
    )
    page_size = 100  # Use fixed page size for pagination

    print(f"Getting the list of track URIs from playlist [{playlist_name}].")

    paginate = 0
    while True:
        print(f"Fetching track URIs starting from offset {paginate}...")
        response = spotify_api_call_with_retry(
            lambda: spotify.playlist_items(playlist_id, fields='items(track(uri))', limit=page_size, offset=paginate)
        )
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
        spotify_api_call_with_retry(
            lambda: spotify.playlist_add_items(playlist_id, paged_tracks)
        )

    print(f"Clearing local Spotify and Telegram cache.")
    if os.path.exists(SPOTIFY_CACHE):
        os.remove(SPOTIFY_CACHE)
    if os.path.exists(TELEGRAM_CACHE):
        os.remove(TELEGRAM_CACHE)
