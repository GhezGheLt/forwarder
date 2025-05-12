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

# ======= بخش Flask برای مانیتورینگ =======
app = Flask(__name__)

@app.route('/')
def home():
    return "ربات فوروارد فعال است | <a href='/health'>بررسی سلامت</a>"

@app.route('/health')
def health_check():
    return jsonify({
        "status": "active",
        "server": "Render",
        "timestamp": time.time()
    }), 200

# ======= سیستم Keep-Alive داخلی =======
def keep_alive():
    while True:
        try:
            urllib.request.urlopen(f"https://{os.getenv('RENDER_EXTERNAL_URL', 'forwarder-go16.onrender.com')}/health")
            logger.info("Keep-Alive: درخواست سلامت ارسال شد")
        except Exception as e:
            logger.error(f"Keep-Alive خطا: {str(e)}")
        time.sleep(240)  # هر 4 دقیقه

# ======= تنظیمات ربات تلگرام =======
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
        await message.copy(int(os.getenv("DEST_CHANNEL")))
        logger.info(f"پیام {message.id} با موفقیت فوروارد شد")
    except Exception as e:
        logger.error(f"خطا در فوروارد: {str(e)}")

# ======= راه‌اندازی سرویس‌ها =======
if __name__ == "__main__":
    # راه‌اندازی Keep-Alive در پس‌زمینه
    threading.Thread(target=keep_alive, daemon=True).start()
    
    # راه‌اندازی سرور Flask
    PORT = int(os.getenv("PORT", 8080))
    threading.Thread(
        target=serve,
        args=(app,),
        kwargs={'host': '0.0.0.0', 'port': PORT},
        daemon=True
    ).start()
    
    # راه‌اندازی ربات تلگرام
    logger.info("در حال راه‌اندازی سرویس‌ها...")
    bot.run()
