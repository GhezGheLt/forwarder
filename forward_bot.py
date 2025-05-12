import os
import logging
import urllib.request
import socket
from pyrogram import Client, filters
from flask import Flask, jsonify
from waitress import serve
import threading
import time

# ======= تنظیمات پیشرفته لاگینگ =======
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ======= اعتبارسنجی متغیرهای محیطی =======
REQUIRED_ENV_VARS = ["API_ID", "API_HASH", "BOT_TOKEN", "SOURCE_CHANNEL", "DEST_CHANNEL"]
missing_vars = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
if missing_vars:
    logger.error(f"خطا: متغیرهای محیطی ضروری وجود ندارد: {', '.join(missing_vars)}")
    exit(1)

try:
    SOURCE_CHANNEL = int(os.getenv("SOURCE_CHANNEL"))
    DEST_CHANNEL = int(os.getenv("DEST_CHANNEL"))
except ValueError:
    logger.error("خطا: شناسه کانال باید عددی باشد (مثال: -1001234567890)")
    exit(1)

# ======= بخش Flask برای مانیتورینگ =======
app = Flask(__name__)

@app.route('/')
def home():
    return "ربات فوروارد فعال است | <a href='/health'>بررسی سلامت</a>"

@app.route('/health')
def health_check():
    bot_status = "running" if 'bot' in globals() and bot.is_connected else "inactive"
    return jsonify({
        "status": "active",
        "server": "Render",
        "bot_status": bot_status,
        "timestamp": int(time.time())
    }), 200

# ======= سیستم Keep-Alive بهینه‌شده =======
def keep_alive():
    while True:
        try:
            socket.setdefaulttimeout(15)
            port = int(os.getenv("PORT", 8080))
            urllib.request.urlopen(f"http://localhost:{port}/health", timeout=20)
            logger.debug("Keep-Alive: سلامت سرور تأیید شد")
        except Exception as e:
            logger.warning(f"خطای موقت در Keep-Alive: {str(e)}")
        time.sleep(300)  # هر 5 دقیقه

# ======= تنظیمات ربات تلگرام =======
bot = Client(
    name="forward_bot",
    api_id=int(os.getenv("API_ID")),
    api_hash=os.getenv("API_HASH"),
    bot_token=os.getenv("BOT_TOKEN"),
    in_memory=True,
    workers=4,
    sleep_threshold=30
)

@bot.on_message(filters.chat(SOURCE_CHANNEL) & ~filters.service)
async def forward_message(client, message):
    try:
        # ساخت کپشن جدید
        caption_template = "\n\n🔞 محتوای داغ 👇\n\nکانال اختصاصی: @CamHot"
        original_caption = message.caption or ""
        new_caption = f"{original_caption.splitlines()[0]}{caption_template}"[:1024]

        # ارسال پیام
        if message.media:
            await message.copy(
                chat_id=DEST_CHANNEL,
                caption=new_caption,
                parse_mode="html"
            )
        else:
            await client.send_message(
                chat_id=DEST_CHANNEL,
                text=new_caption,
                disable_web_page_preview=True
            )
        
        logger.info(f"پیام {message.id} با موفقیت فوروارد شد")

    except Exception as e:
        logger.error(f"خطا در فوروارد پیام: {str(e)}", exc_info=True)

# ======= راه‌اندازی سرویس‌ها =======
if __name__ == "__main__":
    # راه‌اندازی Keep-Alive فقط در محیط غیر-Render
    if not os.getenv("RENDER"):
        threading.Thread(target=keep_alive, daemon=True).start()

    # تنظیمات سرور
    PORT = int(os.getenv("PORT", 8080))
    
    # راه‌اندازی ربات در ریسمان جداگانه
    bot_thread = threading.Thread(target=bot.start, daemon=True)
    bot_thread.start()

    # راه‌اندازی سرور Flask
    logger.info(f"راه‌اندازی سرور روی پورت {PORT}")
    serve(
        app,
        host="0.0.0.0",
        port=PORT,
        threads=8,
        channel_timeout=60
    )
