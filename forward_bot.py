from pyrogram import Client, filters
import os
from dotenv import load_dotenv

# بارگذاری متغیرهای محیطی
load_dotenv()

api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
bot_token = os.getenv("BOT_TOKEN")

app = Client("forward_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# آیدی عددی کانال‌ها
SOURCE_CHANNEL = int(os.getenv("SOURCE_CHANNEL"))
DEST_CHANNEL = int(os.getenv("DEST_CHANNEL"))

@app.on_message(filters.chat(SOURCE_CHANNEL))
async def forward_and_edit_caption(client, message):
    try:
        original_caption = message.caption or ""
        first_line = original_caption.split('\n')[0] if original_caption else ""

        new_caption = (
            f"{first_line}\n\n"
            "enjoy hot webcams👙👇\n\n"
            "[CamHot 🔥](https://t.me/+qY4VEKbgX0cxMmEy)"
        )

        if message.photo:
            await client.send_photo(DEST_CHANNEL, photo=message.photo.file_id, caption=new_caption, parse_mode="Markdown")
        elif message.video:
            await client.send_video(DEST_CHANNEL, video=message.video.file_id, caption=new_caption, parse_mode="Markdown")
        elif message.document:
            await client.send_document(DEST_CHANNEL, document=message.document.file_id, caption=new_caption, parse_mode="Markdown")
        elif message.text:
            await client.send_message(DEST_CHANNEL, text=new_caption, parse_mode="Markdown")
        else:
            print("Unsupported message type.")

    except Exception as e:
        print("Error:", e)

app.run()
