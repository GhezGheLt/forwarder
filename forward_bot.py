from pyrogram import Client, filters
from flask import Flask
import os
import threading

# --- Flask for Render keep-alive ---
app = Flask(__name__)

@app.route('/')
def index():
    return "Bot is running!"

def run_flask():
    app.run(host="0.0.0.0", port=8080)

threading.Thread(target=run_flask).start()

# --- Environment Variables ---
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# --- Your Channel IDs ---
SOURCE_CHANNEL = -1002650282186  # جایگزین با آیدی واقعی کانال مبدأ
DEST_CHANNEL = -1002293369181    # جایگزین با آیدی واقعی کانال مقصد

# --- Pyrogram Bot ---
bot = Client("forward_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@bot.on_message(filters.chat(SOURCE_CHANNEL))
async def forward_or_copy(client, message):
    print("Message received!")
    try:
        if message.forward_from_chat or message.forward_from:
            await message.forward(DEST_CHANNEL)
        elif message.text:
            await client.send_message(chat_id=DEST_CHANNEL, text=message.text)
        elif message.photo:
            await client.send_photo(chat_id=DEST_CHANNEL, photo=message.photo.file_id, caption=message.caption)
        elif message.video:
            await client.send_video(chat_id=DEST_CHANNEL, video=message.video.file_id, caption=message.caption)
        else:
            print("Unsupported message type.")
    except Exception as e:
        print(f"Error while forwarding message: {e}")

bot.run()
