import os
import logging
import asyncio
from pyrogram import Client, filters
from pyrogram.errors import PeerIdInvalid, ChannelInvalid, ChannelPrivate
from flask import Flask
from waitress import serve
import threading

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

async def check_channel_access(client):
    """بررسی دسترسی به کانال‌ها"""
    try:
        # بررسی کانال مبدأ
        try:
            source_chat = await client.get_chat(env["source"])
            logger.info(f"کانال مبدأ: {source_chat.title} (ID: {source_chat.id})")
        except (ChannelInvalid, ChannelPrivate, PeerIdInvalid) as e:
            logger.error(f"خطا در دسترسی به کانال مبدأ: {str(e)}")
            return False

        # بررسی کانال مقصد
        try:
            dest_chat = await client.get_chat(env["dest"])
            logger.info(f"کانال مقصد: {dest_chat.title} (ID: {dest_chat.id})")
            
            # بررسی دسترسی ارسال پیام
            me = await client.get_me()
            member = await client.get_chat_member(env["dest"], me.id)
            if not member.can_send_messages:
                logger.error("ربات مجوز ارسال پیام در کانال مقصد را ندارد")
                return False
                
        except (ChannelInvalid, ChannelPrivate, PeerIdInvalid) as e:
            logger.error(f"خطا در دسترسی به کانال مقصد: {str(e)}")
            return False

        return True
    except Exception as e:
        logger.error(f"خطای ناشناخته در بررسی کانال‌ها: {str(e)}", exc_info=True)
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
        logger.debug(f"پیام دریافت شده: {message.id} | نوع: {message.media or 'text'}")
        
        if message.empty:
            logger.warning("پیام خالی دریافت شد")
            return
            
        await message.copy(env["dest"])
        logger.info(f"پیام {message.id} با موفقیت ارسال شد")
    except Exception as e:
        logger.error(f"خطا در پردازش پیام: {str(e)}", exc_info=True)

async def run_bot():
    await bot.start()
    logger.info("ربات تلگرام راه‌اندازی شد")
    
    if await check_channel_access(bot):
        logger.info("آماده دریافت و فوروارد پیام‌ها...")
        await asyncio.Event().wait()  # اجرای نامحدود
    else:
        await bot.stop()

def start_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_bot())

if __name__ == "__main__":
    # راه‌اندازی سرور Flask در ریسمان جداگانه
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
