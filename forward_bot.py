import os
import logging
from pyrogram import Client, filters
from flask import Flask
from waitress import serve
import threading

# تنظیمات لاگینگ
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# اعتبارسنجی متغیرها
SOURCE_CHANNEL = int(os.getenv("SOURCE_CHANNEL"))
DEST_CHANNEL = int(os.getenv("DEST_CHANNEL"))

app = Flask(__name__)

@app.route('/')
def home():
    return "ربات فعال است"

# تنظیمات ربات
bot = Client(
    "forward_bot",
    api_id=int(os.getenv("API_ID")),
    api_hash=os.getenv("API_HASH"),
    bot_token=os.getenv("BOT_TOKEN"),
    in_memory=True
)

@bot.on_message(filters.chat(SOURCE_CHANNEL) & ~filters.service)
async def forward_handler(client, message):
    try:
        # لاگ محتوای پیام برای دیباگ
        logger.info(f"پیام دریافتی: {message.id} | نوع: {message.media or 'text'}")

        # فوروارد پیام
        await message.copy(DEST_CHANNEL)
        logger.info(f"پیام {message.id} با موفقیت فوروارد شد")
        
    except Exception as e:
        logger.error(f"خطا در فوروارد: {str(e)}")

def run_bot():
    bot.run()

if __name__ == "__main__":
    # راه‌اندازی ربات در ریسمان جداگانه
    threading.Thread(target=run_bot, daemon=True).start()
    
    # راه‌اندازی سرور
    serve(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
