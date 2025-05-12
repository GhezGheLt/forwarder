import os
import logging
import urllib.request
import socket
from pyrogram import Client, filters
from flask import Flask, jsonify
from waitress import serve
import threading
import time

# تنظیمات پیشرفته لاگینگ
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
    return jsonify({"status": "active", "server": "Render", "timestamp": time.time()}), 200

# ======= سیستم Keep-Alive بهبود یافته =======
def keep_alive():
    while True:
        try:
            # تنظیم timeout برای جلوگیری از hang شدن
            socket.setdefaulttimeout(10)
            url = f"https://{os.getenv('RENDER_EXTERNAL_URL')}/health" if os.getenv('RENDER_EXTERNAL_URL') else "http://localhost:8080/health"
            urllib.request.urlopen(url)
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
async def forward_and_edit_caption(client, message):
    try:
        dest_channel = int(os.getenv("DEST_CHANNEL"))
        
        # ساخت کپشن جدید طبق درخواست شما
        caption_template = "\nenjoy hot webcams👙👇\n\nCamHot 🔥 (https://t.me/+qY4VEKbgX0cxMmEy)"
        
        if message.caption:
            first_line = message.caption.split('\n')[0]
            new_caption = f"{first_line}{caption_template}"
        else:
            new_caption = f"🔞{caption_template}"
        
        # ارسال پیام با کپشن تغییر یافته
        if message.media:
            await message.copy(
                dest_channel,
                caption=new_caption[:1024]  # محدودیت کاراکتر تلگرام
            )
        elif message.text:
            await client.send_message(
                dest_channel,
                text=new_caption
            )
            
        logger.info(f"پیام {message.id} با کپشن تغییر یافته ارسال شد")
        
    except Exception as e:
        logger.error(f"خطا در ارسال پیام: {str(e)}")

# ======= راه‌اندازی سرویس‌ها =======
if __name__ == "__main__":
    # راه‌اندازی Keep-Alive در پس‌زمینه
    threading.Thread(target=keep_alive, daemon=True).start()
    
    # راه‌اندازی سرور Flask
    PORT = int(os.getenv("PORT", 8080))
    logger.info(f"سرور در حال راه‌اندازی روی پورت {PORT}")
    serve(app, host="0.0.0.0", port=PORT)
    
    # راه‌اندازی ربات تلگرام
    logger.info("ربات تلگرام در حال راه‌اندازی...")
    bot.run()
