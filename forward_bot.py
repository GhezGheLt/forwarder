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
logger = logging.getLogger(name)

app = Flask(name)

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
            
        await message.copy(dest)
        logger.info(f"پیام {message.id} با موفقیت ارسال شد")
    except Exception as e:
        logger.error(f"خطای بحرانی: {e}", exc_info=True)

if name == "main":
    threading.Thread(target=run_server, daemon=True).start()
    logger.info("Starting bot...")
    bot.run()
