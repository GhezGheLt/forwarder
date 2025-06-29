import os
import logging
import tempfile
import subprocess
from flask import Flask, jsonify
from threading import Thread

from pyrogram import Client, filters, utils

# ——— Monkey-patch برای باگ Peer ID در Pyrogram ———
original_get_peer_type = utils.get_peer_type
def patched_get_peer_type(peer):
    if isinstance(peer, int):
        return "user" if peer > 0 else "channel"
    return original_get_peer_type(peer)
utils.get_peer_type = patched_get_peer_type

# ——— تنظیمات لاگ‌گیری ———
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# لاگ در فایل
file_handler = logging.FileHandler("bot.log", encoding="utf-8")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# لاگ در کنسول
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# ——— بارگذاری متغیرهای محیطی ———
API_ID        = int(os.getenv("API_ID"))
API_HASH      = os.getenv("API_HASH")
BOT_TOKEN     = os.getenv("BOT_TOKEN")
SOURCE_CHANNEL = int(os.getenv("SOURCE_CHANNEL"))
DEST_CHANNEL   = int(os.getenv("DEST_CHANNEL"))

# ——— راه‌اندازی کلاینت Pyrogram ———
bot = Client(
    "forward_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)

def is_video_message(msg) -> bool:
    """
    بررسی اینکه پیام حاوی video یا video document باشد.
    """
    return bool(
        (msg.video and msg.video.mime_type.startswith("video/")) or
        (msg.document and msg.document.mime_type.startswith("video/"))
    )

@bot.on_message(filters.chat(SOURCE_CHANNEL))
async def handle_message(client, message):
    dest = DEST_CHANNEL

    # ۱. آماده‌سازی caption جدید
    original_caption = message.caption or ""
    first_line = original_caption.split("\n", 1)[0]
    new_caption = (
        first_line
        + "\n\n"
        + "enjoy hot webcams👙👇\n\nCamHot 🔥 ( @CamHotVIP )"
    )

    # ۲. اگر پیام ویدیو هست
    if is_video_message(message):
        logger.info(f"دریافت ویدیو (message_id={message.id})، در حال ساخت پیش‌نمایش…")

        # تعیین آبجکت رسانه (video یا document)
        media = message.video or message.document

        # ۳. پیمایش async generator برای دریافت File object واقعی
        file_obj = None
        async for f in client.get_file(media):
            file_obj = f

        if not file_obj or not file_obj.file_path:
            logger.error("خطا: نشد file_path را از Telegram بگیریم")
            # فوروارد بدون پیش‌نمایش
            await message.copy(dest, caption=new_caption)
            return

        # ۴. ساخت URL مستقیم به فایل
        file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_obj.file_path}"
        logger.info(f"لینک مستقیم فایل: {file_url}")

        # ۵. آماده‌سازی فایل موقت برای پیش‌نمایش
        tmp_preview = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        tmp_preview_path = tmp_preview.name
        tmp_preview.close()

        # ۶. اجرای FFmpeg برای برش ۶۰ ثانیهٔ اول (بدون دانلود کامل)
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-ss", "0", "-t", "60",
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
            stderr = proc.stderr.decode(errors="ignore")
            logger.error(f"FFmpeg خطا: {stderr}")
        else:
            # ۷. ارسال ویدیوی پیش‌نمایش
            await client.send_video(
                chat_id=dest,
                video=tmp_preview_path,
                caption="📺 Preview (First minute)",
                supports_streaming=True
            )
            logger.info("پیش‌نمایش با موفقیت ارسال شد")

        # ۸. حذف فایل موقت پیش‌نمایش
        try:
            os.remove(tmp_preview_path)
        except OSError:
            pass

        # ۹. فوروارد ویدیوی کامل بدون دانلود مجدد
        await message.copy(dest, caption=new_caption)
        logger.info(f"ویدیوی کامل (message_id={message.id}) فوروارد شد")

    else:
        # سایر پیام‌ها
        await message.copy(dest, caption=new_caption)
        logger.info(f"پیام (message_id={message.id}) فوروارد شد")

# ——— Flask برای Health Check ———
app = Flask(__name__)

@app.route("/healthz")
def healthz():
    return jsonify(status="ok")

def run_healthz():
    app.run(host="0.0.0.0", port=8080)

if __name__ == "__main__":
    # اجرای سرور Health Check در پس‌زمینه
    Thread(target=run_healthz, daemon=True).start()
    logger.info("Health check در http://0.0.0.0:8080/healthz در حال اجراست")
    # اجرای ربات تلگرام
    bot.run()
