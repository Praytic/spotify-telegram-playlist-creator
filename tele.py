import asyncio
import json
import os

from colorama import init
from telethon import TelegramClient
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

async def main():
    async with TelegramClient(name, api_id, api_hash) as client:
        print(f"Extracting tracks from Telegram chat with ID [{chat}]")
        count = 0
        total_messages = 0
        offset_id = 0
        batch_size = 100

        while True:
            batch_count = 0
            last_message_id = offset_id

            async for message in client.iter_messages(int(chat), filter=InputMessagesFilterMusic, limit=batch_size, offset_id=offset_id):
                batch_count += 1
                total_messages += 1
                last_message_id = message.id

                # Use message.audio property and iterate through all attributes
                if message.audio:
                    # Print all document attributes for debugging
                    print(f"\n  Message ID: {message.id}")
                    print(f"  Document attributes: {message.audio.attributes}")

                    title = ""
                    performer = ""

                    # Iterate through all attributes to find DocumentAttributeAudio
                    for attr in message.audio.attributes:
                        if isinstance(attr, DocumentAttributeAudio):
                            print(f"  Raw audio attributes:")
                            print(f"    - title: '{attr.title}'")
                            print(f"    - performer: '{attr.performer}'")
                            print(f"    - duration: {attr.duration if hasattr(attr, 'duration') else 'N/A'}")

                            title = attr.title if attr.title else ""
                            performer = attr.performer if attr.performer else ""

                            # If performer is empty but title contains " - ", try to split it
                            if not performer and title and ' - ' in title:
                                parts = title.split(' - ', 1)
                                if len(parts) == 2:
                                    performer = parts[0].strip()
                                    title = parts[1].strip()
                                    print(f"    ✓ Parsed from title metadata: {title} - {performer}")

                            # Break after processing the first DocumentAttributeAudio found
                            break

                    # Fallback: If still missing metadata, try to parse from file_name
                    if (not title or not performer) and hasattr(message.audio, 'attributes'):
                        file_name = getattr(message.audio, 'file_name', None)
                        if file_name:
                            print(f"  File name: '{file_name}'")
                            # Remove file extension
                            name_without_ext = file_name.rsplit('.', 1)[0] if '.' in file_name else file_name

                            # Try to parse "Artist - Title" format from filename
                            if ' - ' in name_without_ext:
                                parts = name_without_ext.split(' - ', 1)
                                if len(parts) == 2:
                                    if not performer:
                                        performer = parts[0].strip()
                                    if not title:
                                        title = parts[1].strip()
                                    print(f"    ✓ Parsed from file_name: {title} - {performer}")

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

if __name__ == '__main__':
    asyncio.run(main())
