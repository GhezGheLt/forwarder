from pyrogram import Client, filters
from flask import Flask, jsonify
from waitress import serve
import os
import threading
import logging
import time

# ======= تنظیمات پیشرفته لاگینگ =======
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log')
    ]
)
logger = logging.getLogger(__name__)

# ======= بخش Flask برای مانیتورینگ =======
app = Flask(__name__)

@app.route('/')
def home():
    return """
    <h1>ربات فوروارد فعال است</h1>
    <p>وضعیت: <a href='/health'>بررسی سلامت</a></p>
    <p>آخرین بررسی: {}</p>
    """.format(time.ctime())

@app.route('/health')
def health_check():
    return jsonify({
        "status": "active",
        "timestamp": time.time(),
        "service": "Telegram Forwarder"
    }), 200

def run_flask():
    PORT = int(os.environ.get("PORT", 8080))
    logger.info(f"سرور مانیتورینگ روی پورت {PORT} راه‌اندازی شد")
    serve(app, host="0.0.0.0", port=PORT)

# ======= بخش اصلی ربات =======
try:
    API_ID = int(os.environ["API_ID"])
    API_HASH = os.environ["API_HASH"]
    BOT_TOKEN = os.environ["BOT_TOKEN"]
    SOURCE_CHANNEL = int(os.environ["SOURCE_CHANNEL"])
    DEST_CHANNEL = int(os.environ["DEST_CHANNEL"])
except (KeyError, ValueError) as e:
    logger.error(f"خطا در دریافت متغیرهای محیطی: {str(e)}")
    exit(1)

bot = Client(
    "forward_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    in_memory=True,
    workers=2
)

@bot.on_message(filters.chat(SOURCE_CHANNEL))
async def handle_message(client, message):
    try:
        logger.info(f"دریافت پیام جدید با ID: {message.id}")
        await message.copy(DEST_CHANNEL)
        logger.info(f"پیام {message.id} با موفقیت فوروارد شد")
    except Exception as e:
        logger.error(f"خطا در فوروارد پیام: {str(e)}")

# ======= راه‌اندازی سرویس‌ها =======
if __name__ == "__main__":
    # راه‌اندازی Flask در تابع جداگانه
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # راه‌اندازی ربات تلگرام
    logger.info("در حال راه‌اندازی ربات تلگرام...")
    bot.run()
