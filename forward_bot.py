from pyrogram import Client, filters
from flask import Flask
import os
import threading
import logging
from waitress import serve

# تنظیمات لاگینگ
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask App
app = Flask(__name__)

@app.route('/')
def index():
    return "Bot is running!"

@app.route('/ping')
def ping():
    return "pong"

def run_flask():
    PORT = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting Flask server on port {PORT}")
    serve(app, host="0.0.0.0", port=PORT)

# Start Flask in a thread
flask_thread = threading.Thread(target=run_flask)
flask_thread.daemon = True
flask_thread.start()

# Pyrogram Bot
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

SOURCE_CHANNEL = -1002650282186
DEST_CHANNEL = -1002293369181

bot = Client(
    "forward_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    in_memory=True,
    workers=2
)

@bot.on_message(filters.chat(SOURCE_CHANNEL))
async def forward_message(client, message):
    try:
        logger.info(f"Processing message {message.id}")
        await message.copy(DEST_CHANNEL)
        logger.info(f"Message {message.id} forwarded successfully")
    except Exception as e:
        logger.error(f"Error forwarding message {message.id}: {str(e)}")

if __name__ == "__main__":
    logger.info("Starting bot...")
    bot.run()
