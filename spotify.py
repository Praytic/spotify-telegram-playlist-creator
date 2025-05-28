from urllib.parse import quote

import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth

import tele

load_dotenv()

scope = 'playlist-modify-public'
username = 'zxop4ta6nk1bm47vu5pewdk67'

auth_manager=SpotifyOAuth(scope=scope)
spotify = spotipy.Spotify(auth_manager=auth_manager)

unfound = []

def user_playlist_get_or_create(username, name):
    print("Getting user [{0}] playlist with name [{1}].".format(username, name))
    all_playlists = spotify.user_playlists(username)
    for playlist in all_playlists['items']:
        if playlist['name'] == name:
            return playlist['id']
    return spotify.user_playlist_create(username, name)['id']


if auth_manager:
    playlist_id = user_playlist_get_or_create(username, tele.playlist_name)
    tracks = []
    for artist, song in tele.songs:
        print(f"Searching for song [{song}] from artist [{artist}].")
        results = spotify.search(q=quote(f"track:{song} artist:{artist}"), type="track", limit=1)['tracks']['items']
        if len(results) > 0:
            first_result = results[0]
            uri = first_result['uri']
            tracks.append(first_result['uri'])
            print("Successfully got song [{0}].".format(song))
        else:
            unfound.append(song)
            print("Failed to get song [{0}].".format(song))
            tele.print_red("Failed to get song %s from spotify " %song)

    print(f"Finished search for songs from telegram export. Stats: found {len(tracks)} tracks, not found {len(unfound)} tracks. Creating Spotify playlist.")
    paginate = 0
    while paginate < len(tracks):
        next_page = paginate + 100
        paged_tracks = tracks[paginate:next_page]
        paginate = next_page
        print("Add [{0}] songs to playlist [{1}].".format(len(paged_tracks), playlist_id))
        spotify.playlist_add_items(playlist_id, paged_tracks)
