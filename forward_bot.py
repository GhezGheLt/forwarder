import os
import logging
import asyncio
from pyrogram import Client, filters
from pyrogram.errors import PeerIdInvalid, ChannelInvalid, ChannelPrivate
from flask import Flask
from waitress import serve
import threading
import time

# تنظیمات پیشرفته لاگینگ
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# اعتبارسنجی متغیرهای محیطی
def validate_env():
    required_vars = ["API_ID", "API_HASH", "BOT_TOKEN", "SOURCE_CHANNEL", "DEST_CHANNEL"]
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        logger.error(f"متغیرهای محیطی ضروری وجود ندارد: {', '.join(missing)}")
        exit(1)
    
    try:
        return {
            "api_id": int(os.getenv("API_ID")),
            "api_hash": os.getenv("API_HASH"),
            "bot_token": os.getenv("BOT_TOKEN"),
            "source": int(os.getenv("SOURCE_CHANNEL")),
            "dest": int(os.getenv("DEST_CHANNEL"))
        }
    except ValueError as e:
        logger.error(f"خطا در مقادیر محیطی: {str(e)}")
        exit(1)

env = validate_env()

app = Flask(__name__)

@app.route('/health')
def health():
    return "OK", 200

async def verify_channel_access(client, channel_id, channel_type):
    """بررسی دسترسی به کانال با مدیریت بهتر خطاها"""
    try:
        chat = await client.get_chat(channel_id)
        logger.info(f"کانال {channel_type} شناسایی شد: {chat.title} (ID: {chat.id})")
        return True
    except (ChannelInvalid, ChannelPrivate, PeerIdInvalid) as e:
        logger.error(f"خطا: ربات به کانال {channel_type} دسترسی ندارد")
        logger.error(f"لطفاً مطمئن شوید:")
        logger.error(f"1. ربات @{client.me.username} به کانال اضافه شده است")
        logger.error(f"2. شناسه کانال صحیح است: {channel_id}")
        logger.error(f"3. ربات محدود نشده است")
        return False
    except Exception as e:
        logger.error(f"خطای ناشناخته در بررسی کانال {channel_type}: {str(e)}", exc_info=True)
        return False

bot = Client(
    "forward_bot",
    api_id=env["api_id"],
    api_hash=env["api_hash"],
    bot_token=env["bot_token"],
    in_memory=True,
    workers=4
)

@bot.on_message(filters.chat(env["source"]))
async def handle_message(client, message):
    try:
        logger.debug(f"پیام دریافت شده از کانال مبدأ: {message.id}")
        await message.copy(env["dest"])
        logger.info(f"پیام {message.id} با موفقیت ارسال شد")
    except Exception as e:
        logger.error(f"خطا در پردازش پیام: {str(e)}", exc_info=True)

async def run_bot():
    try:
        await bot.start()
        logger.info(f"ربات فعال شد: @{bot.me.username}")
        
        if not await verify_channel_access(bot, env["source"], "مبدأ"):
            return
            
        if not await verify_channel_access(bot, env["dest"], "مقصد"):
            return
            
        logger.info("آماده دریافت و فوروارد پیام‌ها...")
        await asyncio.Event().wait()
        
    except Exception as e:
        logger.error(f"خطای بحرانی: {str(e)}", exc_info=True)
    finally:
        if bot.is_connected:
            await bot.stop()

def start_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run_bot())
    finally:
        loop.close()

if __name__ == "__main__":
    # راه‌اندازی سرور Flask
    threading.Thread(
        target=lambda: serve(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080))),
        daemon=True
    ).start()
    
    # راه‌اندازی ربات
    threading.Thread(target=start_bot, daemon=True).start()
    
    # نگه داشتن برنامه در حال اجرا
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("خاتمه برنامه...")
