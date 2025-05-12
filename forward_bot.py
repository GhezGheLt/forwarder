import os
import logging
from pyrogram import Client, filters
from flask import Flask
from waitress import serve
import threading

# تنظیمات لاگینگ
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(name)

# Flask App
app = Flask(name)

@app.route('/health')
def health_check():
    return "OK", 200

def run_server():
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
async def handle_message(client, message):
    try:
        dest_channel = int(os.getenv("DEST_CHANNEL"))
        
        # ساخت کپشن جدید
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
            
        logger.info(f"پیام {message.id} با موفقیت ارسال شد")
        
    except Exception as e:
        logger.error(f"خطا در ارسال پیام: {str(e)}")

if name == "main":
    # راه اندازی سرور در تابع جداگانه
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # راه اندازی ربات
    logger.info("ربات در حال راه اندازی...")
    bot.run()
