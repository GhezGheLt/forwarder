import os
import logging
import tempfile
import subprocess
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

def is_video_message(message):
    if message.video:
        return True
    if message.document and message.document.mime_type.startswith("video"):
        return True
    return False

try:
    # بررسی متغیرهای محیطی
    required_env_vars = ['API_ID', 'API_HASH', 'BOT_TOKEN', 'SOURCE_CHANNEL', 'DEST_CHANNEL']
    for var in required_env_vars:
        if not os.getenv(var):
            raise ValueError(f"متغیر محیطی {var} تعریف نشده است")

    BOT_TOKEN = os.getenv("BOT_TOKEN")
    bot = Client(
        "forward_bot",
        api_id=int(os.getenv("API_ID")),
        api_hash=os.getenv("API_HASH"),
        bot_token=BOT_TOKEN,
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

            # ساخت کپشن جدید
            new_caption = None
            if message.caption:
                first_line = message.caption.split('\n')[0]
                new_caption = (f"{first_line}\n\n"
                               "enjoy hot webcams👙👇\n\n"
                               "CamHot 🔥 ( @CamHotVIP )")

            # اگر پیام ویدیو باشد
            if is_video_message(message):
                # 1. دریافت file_id
                file_id = message.video.file_id if message.video else message.document.file_id

                # 2. پیمایش async generator برای گرفتن file_path
                file_obj = None
                async for f in client.get_file(file_id):
                    file_obj = f
                if not file_obj or not file_obj.file_path:
                    logger.error("نشد file_path را از Telegram بگیریم")
                else:
                    # 3. ساخت URL مستقیم
                    file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_obj.file_path}"
                    logger.info(f"لینک مستقیم فایل: {file_url}")

                    # 4. آماده‌سازی فایل پیش‌نمایش
                    tmp_preview = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
                    tmp_preview_path = tmp_preview.name
                    tmp_preview.close()

                    # 5. برش یک دقیقهٔ اول با FFmpeg (بدون دانلود کامل)
                    ffmpeg_cmd = [
                        "ffmpeg",
                        "-y",
                        "-ss", "0",
                        "-t", "60",
                        "-i", file_url,
                        "-c", "copy",
                        tmp_preview_path
                    ]
                    logger.info(f"اجرا FFmpeg: {' '.join(ffmpeg_cmd)}")
                    proc = subprocess.run(
                        ffmpeg_cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                    if proc.returncode != 0:
                        logger.error(f"FFmpeg خطا: {proc.stderr.decode()}")
                    else:
                        # 6. ارسال پیش‌نمایش
                        logger.info(f"ارسال پیش‌نمایش به {dest}")
                        await client.send_video(
                            chat_id=dest,
                            video=tmp_preview_path,
                            caption="📺 Preview (First minute)",
                            supports_streaming=True
                        )

                    # 7. حذف فایل موقت پیش‌نمایش
                    try:
                        os.remove(tmp_preview_path)
                    except Exception as e_rm:
                        logger.warning(f"حذف فایل موقت خطا داد: {e_rm}")

                # 8. در ادامه، فوروارد کامل ویدیو بدون دانلود
                await message.copy(
                    dest,
                    caption=new_caption
                )
                logger.info(f"ویدیوی کامل (ID={message.id}) با موفقیت فوروارد شد")

            else:
                # برای پیام‌های غیر ویدیو همان رفتار قبلی
                await message.copy(
                    dest,
                    caption=new_caption
                )
                logger.info(f"پیام {message.id} با موفقیت ارسال شد")

        except Exception as e:
            logger.error(f"خطای بحرانی در handle_message: {e}", exc_info=True)

    if __name__ == "__main__":
        threading.Thread(target=run_server, daemon=True).start()
        logger.info("Starting bot...")
        bot.run()

except Exception as e:
    logger.critical(f"خطای راه‌اندازی: {e}")
    raise
