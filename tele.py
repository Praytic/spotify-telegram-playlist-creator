import json
import os

from colorama import init
from telethon.sync import TelegramClient
from telethon.tl.types import DocumentAttributeAudio, InputMessagesFilterMusic
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
    count = 0
    total_messages = 0
    offset_id = 0
    batch_size = 100

    while True:
        batch_count = 0
        last_message_id = offset_id

        for message in client.iter_messages(int(chat), filter=InputMessagesFilterMusic, limit=batch_size, offset_id=offset_id):
            batch_count += 1
            total_messages += 1
            last_message_id = message.id

            media = message.media
            if media and hasattr(media, 'document'):
                # Print all document attributes for debugging
                print(f"\n  Message ID: {message.id}")
                print(f"  Document attributes: {media.document.attributes}")

                attributes = media.document.attributes[0]
                if isinstance(attributes, DocumentAttributeAudio):
                    print(f"  Raw audio attributes:")
                    print(f"    - title: '{attributes.title}'")
                    print(f"    - performer: '{attributes.performer}'")
                    print(f"    - duration: {attributes.duration if hasattr(attributes, 'duration') else 'N/A'}")

                    title = attributes.title if attributes.title else ""
                    performer = attributes.performer if attributes.performer else ""

                    # If performer is empty but title contains " - ", try to split it
                    if not performer and title and ' - ' in title:
                        parts = title.split(' - ', 1)
                        if len(parts) == 2:
                            performer = parts[0].strip()
                            title = parts[1].strip()
                            print(f"    ✓ Parsed from title: {title} - {performer}")

                    if not title or not performer:
                        print(f"    ✗ Skipped: missing metadata - title: '{title}', performer: '{performer}'")
                        continue
                    song = (title, performer)
                    if song not in songs:
                        songs.append(song)
                        count += 1
                        print(f"    ✓ Extracted: {title} - {performer}")
                    else:
                        print(f"    = Duplicate: {title} - {performer}")

        if batch_count > 0:
            print(f"  Processed batch: {batch_count} messages, {count} unique tracks total so far...")
            offset_id = last_message_id
        else:
            break

    print(f"Extracted {len(songs)} unique tracks from {total_messages} audio messages from Telegram.")
    with open(TELEGRAM_CACHE, 'w', encoding="utf-8") as f:
        json.dump(songs, f, ensure_ascii=False)
