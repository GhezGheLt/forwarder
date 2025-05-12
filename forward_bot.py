from pyrogram import Client, filters
from flask import Flask
import os
import threading
from waitress import serve

# Flask App
app = Flask(__name__)

@app.route('/')
def index():
    return "Bot is running!"

def run_flask():
    PORT = int(os.environ.get("PORT", 8080))
    serve(app, host="0.0.0.0", port=PORT)

# Start Flask in a thread
threading.Thread(target=run_flask, daemon=True).start()

# Pyrogram Bot
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

SOURCE_CHANNEL = -1002650282186
DEST_CHANNEL = -1002293369181

bot = Client("forward_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@bot.on_message(filters.chat(SOURCE_CHANNEL))
async def forward_or_copy(client, message):
    print(f"New message: {message.id}")
    try:
        if message.forward_from_chat or message.forward_from:
            await message.forward(DEST_CHANNEL)
        elif message.text:
            await client.send_message(DEST_CHANNEL, text=message.text)
        elif message.media:
            await message.copy(DEST_CHANNEL)
    except Exception as e:
        print(f"Error: {e}")

print("Bot is starting...")
bot.run()
