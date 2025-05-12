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
        "timestamp": time.time(),
        "telegram_bot": "running" if bot.is_connected else "inactive"
    }), 200

# ======= سیستم Keep-Alive بهینه‌شده =======
def keep_alive():
    while True:
        try:
            socket.setdefaulttimeout(10)
            port = int(os.getenv("PORT", 8080))
            urllib.request.urlopen(f"http://localhost:{port}/health")
            logger.debug("Keep-Alive: درخواست سلامت با موفقیت ارسال شد")
        except urllib.error.URLError as e:
            logger.warning(f"خطای موقت در Keep-Alive: {e.reason}")
        except Exception as e:
            logger.error(f"خطای ناشناخته در Keep-Alive: {str(e)}")
        time.sleep(300)  # هر 5 دقیقه

# ======= تنظیمات ربات تلگرام =======
bot = Client(
    name="forward_bot",
    api_id=int(os.getenv("API_ID")),
    api_hash=os.getenv("API_HASH"),
    bot_token=os.getenv("BOT_TOKEN"),
    in_memory=True,
    workers=4
)

@bot.on_message(filters.chat(int(os.getenv("SOURCE_CHANNEL")) & ~filters.service)
async def forward_and_edit_caption(client, message):
    try:
        dest_channel = int(os.getenv("DEST_CHANNEL"))
        caption_template = "\n\n🔞 Enjoy hot webcams 👇\n\n🔥 CamHot: https://t.me/+qY4VEKbgX0cxMmEy"
        
        # پردازش کپشن
        original_caption = message.caption or ""
        first_line = original_caption.split('\n')[0] if original_caption else "🔞"
        new_caption = f"{first_line}{caption_template}"[:1024]  # محدودیت تلگرام
        
        # فوروارد محتوا
        if message.media:
            await message.copy(
                chat_id=dest_channel,
                caption=new_caption,
                parse_mode="html"
            )
        elif message.text:
            await client.send_message(
                chat_id=dest_channel,
                text=new_caption,
                disable_web_page_preview=True
            )
            
        logger.info(f"پیام {message.id} با موفقیت فوروارد شد")

    except Exception as e:
        logger.error(f"خطا در فوروارد پیام: {str(e)}", exc_info=True)

# ======= مدیریت خطاهای ربات =======
@bot.on_error()
async def error_handler(_, update, err):
    logger.error(f"خطای ربات: {str(err)}", exc_info=True)

# ======= راه‌اندازی سرویس‌ها =======
if __name__ == "__main__":
    # غیرفعال کردن Keep-Alive در محیط Render
    if not os.getenv("RENDER"):
        threading.Thread(target=keep_alive, daemon=True).start()
        logger.info("سیستم Keep-Alive فعال شد")
    
    # تنظیمات سرور
    PORT = int(os.getenv("PORT", 8080))
    HOST = "0.0.0.0"
    
    # راه‌اندازی همزمان ربات و سرور
    try:
        # راه‌اندازی ربات در تابع جداگانه
        def run_bot():
            bot.run()
        
        bot_thread = threading.Thread(target=run_bot, daemon=True)
        bot_thread.start()
        
        logger.info(f"سرور Flask در حال راه‌اندازی روی {HOST}:{PORT}")
        serve(
            app,
            host=HOST,
            port=PORT,
            threads=8,
            channel_timeout=120
        )
    except KeyboardInterrupt:
        logger.info("خاموش کردن سرویس...")
    except Exception as e:
        logger.critical(f"خطای بحرانی: {str(e)}", exc_info=True)
