import os
import logging
import urllib.request
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

# ======= سیستم Keep-Alive داخلی =======
def keep_alive():
    while True:
        try:
            urllib.request.urlopen(f"https://{os.getenv('RENDER_EXTERNAL_URL', 'your-app-name.onrender.com')}/health")
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
        if message.caption:
            first_line = message.caption.split('\n')[0]
            new_caption = f"{first_line}\nenjoy hot webcams👙👇\n\nCamHot 🔥 (https://t.me/+qY4VEKbgX0cxMmEy)"
        else:
            new_caption = "enjoy hot webcams👙👇\n\nCamHot 🔥 (https://t.me/+qY4VEKbgX0cxMmEy)"
        
        # ارسال پیام با کپشن تغییر یافته
        if message.media:
            await message.copy(
                dest_channel,
                caption=new_caption
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
    serve(app, host="0.0.0.0", port=PORT)
    
    # راه‌اندازی ربات تلگرام
    logger.info("ربات در حال راه‌اندازی...")
    bot.run()
