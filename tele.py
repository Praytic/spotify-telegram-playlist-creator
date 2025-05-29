import json
import os

from colorama import init
from telethon.sync import TelegramClient
from telethon.tl.types import DocumentAttributeAudio
from dotenv import load_dotenv

init()
load_dotenv()

api_id = os.environ['TELEGRAM_API_ID']
api_hash = os.environ['TELEGRAM_API_HASH']
name = os.environ['BOT_NAME']
chat = os.environ['TELEGRAM_CHAT_ID']
songs = []

TELEGRAM_CACHE = 'tele.json'

if os.path.exists(TELEGRAM_CACHE):
    with open(TELEGRAM_CACHE, 'r', encoding="utf-8") as f:
        songs = [tuple(item) for item in json.load(f)]
else:
    songs = []

with TelegramClient(name, api_id, api_hash) as client:
    print(f"Extracting tracks from Telegram chat with ID [{chat}]")
    for message in client.iter_messages(int(chat)):
        media = message.media
        if media:
            if hasattr(media, 'document'):
                attributes = media.document.attributes[0]
                if isinstance(attributes, DocumentAttributeAudio):
                    song = (attributes.title, attributes.performer)
                    if song not in songs:
                        songs.append(song)
    with open(TELEGRAM_CACHE, 'w', encoding="utf-8") as f:
        json.dump(songs, f, ensure_ascii=False)
