import sys

from colorama import init
from telethon.sync import TelegramClient
from telethon.tl.types import DocumentAttributeAudio
from termcolor import cprint

init()

args = sys.argv[1:]
api_id = args[0]
api_hash = args[1]
name = 'Praytic Telegram Client'
chat = args[2]
songs = []
performer = 'artist'
title = 'track'
test = 0
broken_songs = []
playlist_name = 'Счастье'

print_red_onwhite = lambda x: cprint(x, 'red', 'on_white')
print_green_onwhite = lambda x: cprint(x, 'green', 'on_white')
print_red = lambda x: cprint(x, 'red')

with TelegramClient(name, api_id, api_hash) as client:
    for message in client.iter_messages(int(chat)):
        media = message.media
        if media:
            if hasattr(media, 'document'):
                attributes = media.document.attributes[0]
                if isinstance(attributes, DocumentAttributeAudio):
                    songs.append((attributes.title, attributes.performer))
