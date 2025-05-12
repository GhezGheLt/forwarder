import os
import logging
from pyrogram import Client, filters
from flask import Flask
from waitress import serve
import threading
import time

# تنظیمات پیشرفته لاگینگ
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('debug.log'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/health')
def health():
    return "OK", 200

def run_server():
    serve(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))

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
        dest = int(os.getenv("DEST_CHANNEL"))
        logger.debug(f"پیام دریافت شده: {message}")
        
        if message.empty:
            logger.warning("پیام خالی دریافت شد")
            return
        
        # پردازش کپشن
        new_caption = ""
        if message.caption:
            # گرفتن خط اول کپشن قبلی
            first_line = message.caption.split('\n')[0]
            # ساخت کپشن جدید
            new_caption = f"{first_line}\n\nenjoy hot webcams👙👇\n\nCamHot 🔥 ( https://t.me/+qY4VEKbgX0cxMmEy )"
        
        # ارسال پیام با کپشن جدید
        await message.copy(
            dest,
            caption=new_caption if new_caption else None
        )
        logger.info(f"پیام {message.id} با موفقیت ارسال شد")
    except Exception as e:
        logger.error(f"خطای بحرانی: {e}", exc_info=True)

if __name__ == "__main__":
    threading.Thread(target=run_server, daemon=True).start()
    logger.info("Starting bot...")
    bot.run()
