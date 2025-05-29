# spotify-telegram-playlist-creator

Project consists of Python scripts that extract audio files from a specified [Telegram](https://telegram.org/) chat or group and search for them on [Spotify](spotify.com) to later add to a playlist. Be aware that some tracks may not exist on Spotify — the logs will show how many tracks weren’t uploaded. The script is capable of updating the playlist with new tracks if it is not empty. Make sure to follow the instructions in this README precisely.

### How to set up the project?

1. First you need create  [Telegram](https://my.telegram.org/) and [Spotify](https://developer.spotify.com/) developer accounts.
    1. From Telegram you should get **API ID** and **API Hash** of your app
    2. From Spotify you should get **Client ID** and **Client Secret** of your app.

2. Install [python](https://www.python.org/) and [pip](https://pip.pypa.io/en/stable/installation/)

3. Download or `git clone` this project

4. Execute `pip install -r requirements.txt` inside project directory to install script dependencies

5. Create `.env` file with the following environment variables:

   | Name                  | What is it                                                   | How to get                                                   |
      | --------------------- | ------------------------------------------------------------ | ------------------------------------------------------------ |
   | SPOTIPY_CLIENT_ID     | **Client ID** of your Spotify app                            | From the [Spotify developer dashboard](https://developer.spotify.com/dashboard) |
   | SPOTIPY_CLIENT_SECRET | **Client Secret** of your Spotify app                        | From the [Spotify developer dashboard](https://developer.spotify.com/dashboard) |
   | TELEGRAM_API_ID       | **API ID** of your Telegram app                              | From the [Telegram developer dashboard](https://my.telegram.org/apps) |
   | TELEGRAM_API_HASH     | **API Hash** of your Telegram app                            | From the [Telegram developer dashboard](https://my.telegram.org/apps) |
   | SPOTIPY_REDIRECT_URI  | Redirect URI is used to get an access token for your Spotify API calls | Open [Spotify developer dashboard](https://developer.spotify.com/dashboard) and add `http://localhost:8000/spotify/callback` to Redirect URIs field. The same value should be set to this environment variable. |
   | BOT_NAME              | Name of your Telegram bot that you've given to [@BotFather](https://t.me/botfather) during step 1 of this guide | Example: `PrayticSpotifyBot`                                 |
   | USERNAME              | Name of your [Spotify profile](https://www.spotify.com/uk/account/profile/) |                                                              |
   | TELEGRAM_CHAT_ID      | ID of the Telegram chat or group that you want to extract audio files from | You have to be a member of this chat or group to be able to extract audio files from it. To retrieve its ID, use [@getidsbot](https://t.me/getidsbot) bot: forward any message with text from the chat to this bot. It will answer you with information about this chat, including **Origin chat ID**. This is your value. It should look like this: `-1001794544163` |
   | PLAYLIST_ID           | ID of the Spotify playlist where you want to add Telegram tracks | Open your Spotify playlist in the [web version](https://open.spotify.com/) and copy ID from the URL. For example, this playlist `https://open.spotify.com/playlist/0jTPnlGCRkROwvbQtd5eBp` has **ID**: `0jTPnlGCRkROwvbQtd5eBp` |

   The format of the `.env` should match the following template:

   ```
   SPOTIPY_CLIENT_ID=
   SPOTIPY_CLIENT_SECRET=
   SPOTIPY_REDIRECT_URI=
   TELEGRAM_API_ID=
   TELEGRAM_API_HASH=
   TELEGRAM_CHAT_ID=
   BOT_NAME=
   USERNAME=
   PLAYLIST_ID=
   ```

You are all set up to run the script!

### How to run the project?

1. From the project directory run `python spotify.py` command.
2. Script will prompt you to log in with Spotify and Telegram. Follow their instructions.
3. Upon successful authentication, you will see application logs:

```
Extracting tracks from Telegram chat with ID [-1051094814341]
Total items in playlist [My Playlist #18]: 0.
Searching among [712] tracks that were extracted from Telegram and don't exist in Spotify playlist.
Finished searching for songs from Telegram export. Stats: found 285 tracks, missing - 427, new to playlist - 285.
Updating Spotify playlist with 285 tracks.
Adding [50] tracks to playlist [My Playlist #18].
Adding [50] tracks to playlist [My Playlist #18].
Adding [50] tracks to playlist [My Playlist #18].
Adding [50] tracks to playlist [My Playlist #18].
Adding [50] tracks to playlist [My Playlist #18].
Adding [35] tracks to playlist [My Playlist #18].
Clearing local Spotify and Telegram cache.
```

4. Check your Spotify playlist, it should have new tracks in it.
