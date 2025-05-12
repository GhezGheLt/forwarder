import os
import logging
from pyrogram import Client, filters
from flask import Flask, jsonify
from waitress import serve
import threading

# تنظیمات لاگینگ
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask App
app = Flask(__name__)

@app.route('/health')
def health_check():
    return jsonify({"status": "active"}), 200

def run_flask():
    PORT = int(os.getenv("PORT", 8080))
    serve(app, host="0.0.0.0", port=PORT)

# تنظیمات ربات
bot = Client(
    "forward_bot",
    api_id=int(os.getenv("API_ID")),
    api_hash=os.getenv("API_HASH"),
    bot_token=os.getenv("BOT_TOKEN"),
    in_memory=True
)

@bot.on_message(filters.chat(int(os.getenv("SOURCE_CHANNEL"))))
async def forward_handler(client, message):
    try:
        await message.copy(int(os.getenv("DEST_CHANNEL")))
        logger.info(f"پیام {message.id} فوروارد شد")
    except Exception as e:
        logger.error(f"خطا: {e}")

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    logger.info("ربات در حال راه‌اندازی...")
    bot.run()
