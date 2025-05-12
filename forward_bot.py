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
        
        if channel_type == "مقصد":
            me = await client.get_me()
            member = await client.get_chat_member(channel_id, me.id)
            if not member.can_send_messages:
                logger.error(f"ربات مجوز ارسال پیام در کانال {channel_type} را ندارد")
                return False
        
        return True
    except (ChannelInvalid, ChannelPrivate, PeerIdInvalid) as e:
        logger.error(f"ربات به کانال {channel_type} دسترسی ندارد یا عضو نیست. لطفاً ربات را به کانال اضافه کنید")
        logger.error(f"خطای دقیق: {str(e)}")
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
        
        if message.empty:
            logger.warning("پیام خالی دریافت شد")
            return
            
        await message.copy(env["dest"])
        logger.info(f"پیام {message.id} با موفقیت به کانال مقصد ارسال شد")
    except Exception as e:
        logger.error(f"خطا در پردازش پیام: {str(e)}", exc_info=True)

async def run_bot():
    try:
        await bot.start()
        logger.info("ربات تلگرام راه‌اندازی شد")
        
        if not await verify_channel_access(bot, env["source"], "مبدأ"):
            logger.error("دسترسی به کانال مبدأ ناموفق بود")
            return
            
        if not await verify_channel_access(bot, env["dest"], "مقصد"):
            logger.error("دسترسی به کانال مقصد ناموفق بود")
            return
        
        logger.info("ربات آماده دریافت و فوروارد پیام‌ها است")
        await asyncio.Event().wait()
    except Exception as e:
        logger.error(f"خطای بحرانی در اجرای ربات: {str(e)}", exc_info=True)
    finally:
        await bot.stop()

def start_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_bot())

if __name__ == "__main__":
    # راه‌اندازی سرور Flask
    server_thread = threading.Thread(
        target=lambda: serve(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080))),
        daemon=True
    )
    server_thread.start()
    
    # راه‌اندازی ربات
    bot_thread = threading.Thread(target=start_bot, daemon=True)
    bot_thread.start()
    
    # نگه داشتن برنامه در حال اجرا
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("دریافت سیگنال خاتمه...")
