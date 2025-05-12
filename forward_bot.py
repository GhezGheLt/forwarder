import os
import logging
import asyncio
from pyrogram import Client, filters
from pyrogram.errors import ChannelInvalid, ChannelPrivate
from flask import Flask
from waitress import serve

# تنظیمات پیشرفته لاگینگ
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# اعتبارسنجی متغیرهای محیطی
SOURCE_CHANNEL = int(os.getenv("SOURCE_CHANNEL", "-1001234567890"))
DEST_CHANNEL = int(os.getenv("DEST_CHANNEL", "-1009876543210"))

app = Flask(__name__)

@app.route('/')
def home():
    return "ربات فوروارد فعال است"

# تنظیمات ربات
bot = Client(
    "forward_bot",
    api_id=int(os.getenv("API_ID")),
    api_hash=os.getenv("API_HASH"),
    bot_token=os.getenv("BOT_TOKEN"),
    in_memory=True,
    workers=12
)

async def check_channel_access():
    """بررسی دسترسی به کانال‌ها"""
    try:
        source_chat = await bot.get_chat(SOURCE_CHANNEL)
        dest_chat = await bot.get_chat(DEST_CHANNEL)
        logger.info(f"دسترسی به کانال مبدأ تأیید شد: {source_chat.title}")
        logger.info(f"دسترسی به کانال مقصد تأیید شد: {dest_chat.title}")
        return True
    except ChannelInvalid:
        logger.error("خطا: کانال نامعتبر است یا ربات عضو نیست")
    except ChannelPrivate:
        logger.error("خطا: کانال خصوصی است یا ربات دسترسی ندارد")
    except Exception as e:
        logger.error(f"خطای ناشناخته در بررسی کانال‌ها: {str(e)}")
    return False

@bot.on_message(filters.chat(SOURCE_CHANNEL) & ~filters.service)
async def forward_handler(client, message):
    try:
        logger.info(f"پیام جدید دریافت شد از کانال {message.chat.id}")
        await message.copy(DEST_CHANNEL)
        logger.info(f"پیام {message.id} با موفقیت فوروارد شد")
    except Exception as e:
        logger.error(f"خطا در فوروارد پیام: {str(e)}", exc_info=True)

async def run_bot():
    await bot.start()
    if await check_channel_access():
        logger.info("ربات آماده دریافت و فوروارد پیام‌ها است")
        await asyncio.Event().wait()  # اجرای نامحدود
    else:
        logger.error("ربات به کانال‌ها دسترسی ندارد. لطفاً تنظیمات را بررسی کنید")

def start_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_bot())

if __name__ == "__main__":
    # راه‌اندازی ربات در یک thread جداگانه
    import threading
    threading.Thread(target=start_bot, daemon=True).start()
    
    # راه‌اندازی سرور Flask
    PORT = int(os.getenv("PORT", 8080))
    logger.info(f"سرور Flask در حال راه‌اندازی روی پورت {PORT}")
    serve(app, host="0.0.0.0", port=PORT)
