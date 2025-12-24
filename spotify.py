import spotipy
import json
import tele
import os
from spotipy.oauth2 import SpotifyOAuth

from tele import TELEGRAM_CACHE

scope = 'playlist-modify-public'
username = os.environ['USERNAME']
playlist_id = os.environ['PLAYLIST_ID']

auth_manager=SpotifyOAuth(scope=scope)
spotify = spotipy.Spotify(auth_manager=auth_manager)

unfound = []
SPOTIFY_CACHE = "spotify.json"

if auth_manager:
    tracks = []
    tracks_in_playlist = []
    tracks_found = 0
    tracks_missing = 0

    playlist_name = spotify.playlist(playlist_id, fields='name')['name']
    total_items_in_playlist, page_size = spotify.playlist_items(playlist_id, fields='total,limit').values()

    print(f"Total items in playlist [{playlist_name}]: {total_items_in_playlist}.")

    if total_items_in_playlist > 0:
        print(f"Getting the list of track URIs by batches of [{page_size}].")

        paginate = 0
        while paginate < total_items_in_playlist:
            next_page = paginate + page_size
            print(f"Fetching track URIs: {paginate + 1}-{min(next_page, total_items_in_playlist)} of {total_items_in_playlist}...")
            items_in_playlist = spotify.playlist_items(playlist_id, fields='items(track(uri))', limit=page_size, offset=paginate)['items']
            for track in items_in_playlist:
                tracks_in_playlist.append(track['track']['uri'])
            print(f"  Added {len(items_in_playlist)} URIs to list.")
            paginate = next_page

        print(f"Got [{len(tracks_in_playlist)}] track URIs from playlist [{playlist_name}].")

    if os.path.exists(SPOTIFY_CACHE):
        print(f"Spotify cache exists, getting track URIs from it.")

        with open(SPOTIFY_CACHE, 'r', encoding="utf-8") as f:
            tracks = json.load(f)

        print(f"Got [{len(tracks)}] tracks from cache.")
    else:
        print(f"Searching among [{len(tele.songs)}] tracks that were extracted from Telegram and don't exist in Spotify playlist.")

        for idx, (song, artist) in enumerate(tele.songs, 1):
            query = f"track:{song} artist:{artist}"
            print(f"Searching [{idx}/{len(tele.songs)}]: {song} - {artist}")
            results = spotify.search(q=query, type="track", market="US", limit=1)['tracks']['items']
            if len(results) > 0:
                first_result = results[0]
                uri = first_result['uri']
                if uri not in tracks_in_playlist:
                    tracks.append(uri)
                    tracks_found += 1
                    print(f"  Found and added to queue.")
                else:
                    print(f"  Found but already in playlist.")
            else:
                tracks_missing += 1
                print(f"  Not found on Spotify.")

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
    os.remove(SPOTIFY_CACHE)
    os.remove(TELEGRAM_CACHE)
