from pyrogram import Client, filters
from flask import Flask
from waitress import serve
import os
import threading
import logging

# ================== تنظیمات لاگینگ ==================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ================== بخش Flask ==================
app = Flask(__name__)

@app.route('/')
def home():
    return """
    <h1>ربات فوروارد فعال است!</h1>
    <p>وضعیت ربات: <a href='/health'>بررسی سلامت</a></p>
    """

@app.route('/health')
def health_check():
    logger.info("درخواست بررسی سلامت دریافت شد")
    return "OK", 200

def run_flask():
    PORT = int(os.environ.get("PORT", 8080))
    logger.info(f"سرور Flask روی پورت {PORT} راه‌اندازی شد")
    serve(app, host="0.0.0.0", port=PORT)

# اجرای Flask در یک تابع جداگانه
flask_thread = threading.Thread(target=run_flask)
flask_thread.daemon = True
flask_thread.start()

# ================== بخش Pyrogram ==================
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

SOURCE_CHANNEL = -1002650282186  # آیدی کانال مبدأ
DEST_CHANNEL = -1002293369181    # آیدی کانال مقصد

bot = Client(
    "forward_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    in_memory=True
)

@bot.on_message(filters.chat(SOURCE_CHANNEL))
async def forward_message(client, message):
    try:
        logger.info(f"دریافت پیام جدید با ID: {message.id}")
        await message.copy(DEST_CHANNEL)
        logger.info(f"پیام {message.id} با موفقیت فوروارد شد")
    except Exception as e:
        logger.error(f"خطا در فوروارد پیام: {str(e)}")

if __name__ == "__main__":
    logger.info("ربات در حال راه‌اندازی...")
    bot.run()
