import os
import logging
import tempfile
import subprocess
import shutil
import aiohttp

from pyrogram import Client, filters, utils
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

async def download_first_5mb_and_screenshot(bot_token: str, file_id: str, temp_dir: str):
    """
    1) با Bot API اطلاعات فایل را می‌گیرد
    2) با هدر Range فقط 5 مگابایت اول را دانلود می‌کند
    3) فریم ~1 ثانیه را با ffmpeg استخراج می‌کند
    """
    # 1) getFile
    api_url = f"https://api.telegram.org/bot{bot_token}/getFile?file_id={file_id}"
    async with aiohttp.ClientSession() as session:
        resp = await session.get(api_url)
        data = await resp.json()
        if not data["ok"]:
            raise RuntimeError(f"getFile failed: {data}")
        file_path = data["result"]["file_path"]

        # 2) download first 5 MB
        download_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
        headers = {"Range": "bytes=0-5242879"}  # 5 * 1024 * 1024 - 1
        resp2 = await session.get(download_url, headers=headers)
        chunk = await resp2.content.read()

    local_video = os.path.join(temp_dir, "partial.mp4")
    with open(local_video, "wb") as f:
        f.write(chunk)

    # 3) extract screenshot (~ثانیه اول)
    screenshot = os.path.join(temp_dir, "screenshot.jpg")
    # -ss برای موقعیت زمانی و -frames:v 1 برای یک فریم
    cmd = [
        "ffmpeg", "-y",
        "-ss", "00:00:01",
        "-i", local_video,
        "-frames:v", "1",
        "-q:v", "2",
        screenshot
    ]
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except Exception as e:
        logger.warning(f"خطا در اجرای ffmpeg: {e}")
        return None

    return screenshot

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

            # آماده‌سازی کپشن جدید
            new_caption = None
            if message.caption:
                first_line = message.caption.split('\n')[0]
                new_caption = (
                    f"{first_line}\n\n"
                    "enjoy hot webcams👙👇\n\n"
                    "CamHot 🔥 ( @CamHotVIP )"
                )

            # اگر پیام ویدیوست، ابتدا 5 مگ اول را دانلود کرده و اسکرین‌شات می‌سازد
            if message.video:
                temp_dir = tempfile.mkdtemp(prefix="vidshot_")
                try:
                    screenshot = await download_first_5mb_and_screenshot(
                        os.getenv("BOT_TOKEN"),
                        message.video.file_id,
                        temp_dir
                    )
                    if screenshot:
                        # ارسال عکس بالای ویدیو
                        await client.send_photo(
                            chat_id=dest,
                            photo=screenshot
                        )
                except Exception as e:
                    logger.error(f"خطا در دانلود/اسکرین‌شات ویدیو: {e}", exc_info=True)
                finally:
                    # پاک‌سازی فایل‌های موقت
                    shutil.rmtree(temp_dir, ignore_errors=True)

            # در نهایت خود ویدیو یا هر نوع پیام دیگری را به صورت Copy ارسال می‌کنیم
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
