import os
import logging
import threading
import time
from pyrogram import Client, filters
from flask import Flask, jsonify
from waitress import serve
import urllib.request

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

# ======= بخش Flask =======
app = Flask(__name__)

@app.route('/')
def home():
    return "ربات فعال است | <a href='/health'>بررسی سلامت</a>"

@app.route('/health')
def health_check():
    return jsonify({"status": "active", "time": time.time()}), 200

# ======= سیستم Keep-Alive بهینه‌شده =======
def keep_alive():
    while True:
        try:
            url = f"https://{os.getenv('RENDER_EXTERNAL_URL', 'forwarder-go16.onrender.com')}/health"
            urllib.request.urlopen(url)
            logger.info("Keep-Alive: درخواست سلامت ارسال شد")
        except Exception as e:
            logger.error(f"Keep-Alive خطا: {str(e)}")
        time.sleep(240)  # هر 4 دقیقه

# ======= تنظیمات ربات =======
bot = Client(
    "forward_bot",
    api_id=int(os.getenv("API_ID")),
    api_hash=os.getenv("API_HASH"),
    bot_token=os.getenv("BOT_TOKEN"),
    in_memory=True,
    workers=2
)

@bot.on_message(filters.chat(int(os.getenv("SOURCE_CHANNEL"))))
async def forward_message(client, message):
    try:
        dest = int(os.getenv("DEST_CHANNEL", "-1002293369181"))  # مقدار پیش‌فرض
        await message.copy(dest)
        logger.info(f"پیام {message.id} با موفقیت ارسال شد")
    except Exception as e:
        logger.error(f"خطا در ارسال پیام: {str(e)}")

# ======= راه‌اندازی سرویس‌ها =======
if __name__ == "__main__":
    # راه‌اندازی Keep-Alive
    threading.Thread(target=keep_alive, daemon=True).start()
    
    # راه‌اندازی سرور
    PORT = int(os.getenv("PORT", 8080))
    serve(app, host="0.0.0.0", port=PORT)
    
    # راه‌اندازی ربات
    logger.info("ربات در حال راه‌اندازی...")
    bot.run()
