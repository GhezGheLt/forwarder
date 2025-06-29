import os
import logging
import tempfile
import subprocess
import shutil
import asyncio
from typing import Optional

from pyrogram import Client, filters, utils
from pyrogram.types import Message
from flask import Flask
from waitress import serve
import threading

# === تنظیمات لاگر ===
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# === Monkey Patch برای رفع باگ Peer ID ===
def get_peer_type_new(peer_id: int) -> str:
    peer_id_str = str(peer_id)
    if not peer_id_str.startswith("-"):
        return "user"
    elif peer_id_str.startswith("-100"):
        return "channel"
    else:
        return "chat"

utils.get_peer_type = get_peer_type_new
# === پایان Monkey Patch ===

app = Flask(__name__)

@app.route('/health')
def health():
    return "OK", 200

def run_server():
    try:
        serve(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
    except Exception as e:
        logger.error(f"خطا در اجرای سرور: {e}")

async def extract_thumbnail(video_path: str, output_path: str) -> bool:
    """استخراج تامبنیل از ویدیو با ffmpeg"""
    try:
        cmd = [
            "ffmpeg", "-y",
            "-ss", "00:00:01",
            "-i", video_path,
            "-frames:v", "1",
            "-q:v", "2",
            "-vf", "scale=640:-1",
            output_path
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        _, stderr = await proc.communicate()
        
        if proc.returncode != 0:
            logger.error(f"خطا در ffmpeg: {stderr.decode()}")
            return False
        return True
    except Exception as e:
        logger.error(f"خطا در استخراج تامبنیل: {e}")
        return False

async def process_large_video(client: Client, message: Message, dest: int, new_caption: Optional[str]):
    """پردازش ویدیوهای بزرگ بدون دانلود کامل"""
    try:
        temp_dir = tempfile.mkdtemp(prefix="videothumb_")
        thumb_path = os.path.join(temp_dir, "thumbnail.jpg")
        
        # اگر ویدیو تامبنیل دارد، از آن استفاده می‌کنیم
        if message.video.thumbs:
            thumb = message.video.thumbs[0]
            thumb_file_id = thumb.file_id
            
            # دانلود تامبنیل
            thumb_path = await client.download_media(
                thumb_file_id,
                file_name=thumb_path
            )
            
            if thumb_path and os.path.exists(thumb_path):
                await client.send_photo(
                    chat_id=dest,
                    photo=thumb_path,
                    caption="Preview of the video"
                )
        else:
            # اگر تامبنیل وجود ندارد، یک فریم تصادفی از ویدیو استخراج می‌کنیم
            # با استفاده از Pyrogram بدون دانلود کامل ویدیو
            video_path = os.path.join(temp_dir, "temp_video.mp4")
            
            # دانلود بخش کوچکی از ویدیو برای استخراج تامبنیل
            try:
                await client.download_media(
                    message.video.file_id,
                    file_name=video_path,
                    progress=lambda c, t: c > 5*1024*1024 and 1/0  # بعد از 5MB قطع می‌کند
                )
            except:
                pass
            
            if os.path.exists(video_path):
                if await extract_thumbnail(video_path, thumb_path):
                    await client.send_photo(
                        chat_id=dest,
                        photo=thumb_path,
                        caption="Video preview"
                    )
    except Exception as e:
        logger.error(f"خطا در پردازش ویدیوی بزرگ: {e}")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

try:
    # بررسی وجود متغیرهای محیطی ضروری
    required_env_vars = ['API_ID', 'API_HASH', 'BOT_TOKEN', 'SOURCE_CHANNEL', 'DEST_CHANNEL']
    for var in required_env_vars:
        if not os.getenv(var):
            raise ValueError(f"متغیر محیطی {var} تعریف نشده است")

    bot = Client(
        "forward_bot",
        api_id=int(os.getenv("API_ID")),
        api_hash=os.getenv("API_HASH"),
        bot_token=os.getenv("BOT_TOKEN"),
        in_memory=True,
        workers=4
    )

    @bot.on_message(filters.chat(int(os.getenv("SOURCE_CHANNEL"))))
    async def handle_message(client: Client, message: Message):
        try:
            dest = int(os.getenv("DEST_CHANNEL"))
            logger.info(f"پیام دریافت شده (ID: {message.id})")

            if message.empty:
                logger.warning("پیام خالی دریافت شد")
                return

            # آماده‌سازی کپشن جدید
            new_caption = None
            if message.caption:
                first_line = message.caption.split('\n')[0]
                new_caption = (
                    f"{first_line}\n\n"
                    "enjoy hot webcams👙👇\n\n"
                    "CamHot 🔥 ( @CamHotVIP )"
                )

            # پردازش ویدیوها
            if message.video:
                file_size_mb = message.video.file_size / (1024 * 1024)
                logger.info(f"ویدیو تشخیص داده شد - سایز: {file_size_mb:.2f}MB")
                
                if file_size_mb > 100:  # برای ویدیوهای خیلی بزرگ
                    await process_large_video(client, message, dest, new_caption)
                else:
                    # برای ویدیوهای کوچک از روش قبلی استفاده می‌کنیم
                    temp_dir = tempfile.mkdtemp(prefix="vidshot_")
                    try:
                        video_path = await client.download_media(
                            message.video.file_id,
                            file_name=os.path.join(temp_dir, "video.mp4")
                        )
                        if video_path:
                            thumb_path = os.path.join(temp_dir, "thumbnail.jpg")
                            if await extract_thumbnail(video_path, thumb_path):
                                await client.send_photo(
                                    chat_id=dest,
                                    photo=thumb_path
                                )
                    except Exception as e:
                        logger.error(f"خطا در پردازش ویدیو: {e}")
                    finally:
                        shutil.rmtree(temp_dir, ignore_errors=True)

            # ارسال پیام اصلی
            await message.copy(
                dest,
                caption=new_caption if new_caption else None
            )
            logger.info(f"پیام {message.id} با موفقیت ارسال شد")

        except Exception as e:
            logger.error(f"خطای بحرانی در handle_message: {e}", exc_info=True)

    if __name__ == "__main__":
        try:
            threading.Thread(target=run_server, daemon=True).start()
            logger.info("Starting bot...")
            bot.run()
        except Exception as e:
            logger.error(f"خطا در اجرای ربات: {e}")
            raise

except Exception as e:
    logger.critical(f"خطای راه‌اندازی: {e}")
    raise
