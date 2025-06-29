import os
import logging
import tempfile
import subprocess
from flask import Flask, jsonify
from threading import Thread

from pyrogram import Client, filters, utils
from pyrogram.file_id import FileId  # ← اضافه شد

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
file_handler = logging.FileHandler("bot.log", encoding="utf-8")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# ——— بارگذاری متغیرهای محیطی ———
API_ID         = int(os.getenv("API_ID"))
API_HASH       = os.getenv("API_HASH")
BOT_TOKEN      = os.getenv("BOT_TOKEN")
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
    return bool(
        (msg.video    and msg.video.mime_type.startswith("video/")) or
        (msg.document and msg.document.mime_type.startswith("video/"))
    )

@bot.on_message(filters.chat(SOURCE_CHANNEL))
async def handle_message(client, message):
    dest = DEST_CHANNEL

    # ساخت کپشن جدید
    orig = message.caption or ""
    first_line = orig.split("\n", 1)[0]
    new_caption = (
        first_line
        + "\n\n"
        + "enjoy hot webcams👙👇\n\nCamHot 🔥 ( @CamHotVIP )"
    )

    # اگر ویدیوست
    if is_video_message(message):
        logger.info(f"دریافت ویدیو (message_id={message.id})، در حال ساخت پیش‌نمایش…")

        # ۱) گرفتن رشته‌ی file_id
        media = message.video or message.document
        file_id_str = media.file_id  # رشته

        # ۲) دیکُد کردن به FileId
        try:
            file_id_obj = FileId.decode(file_id_str)
        except Exception as e:
            logger.error(f"دیکد FileId ناموفق بود: {e}")
            await message.copy(dest, caption=new_caption)
            return

        # ۳) پیمایش async generator برای دریافت File (که شامل file_path است)
        file_obj = None
        async for f in client.get_file(file_id_obj):
            file_obj = f
            break  # فقط اولین چانک برای file_path کافی است

        if not file_obj or not file_obj.file_path:
            logger.error("خطا: نشد file_path را از Telegram بگیریم")
            await message.copy(dest, caption=new_caption)
            return

        # ۴) ساخت URL مستقیم
        file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_obj.file_path}"
        logger.info(f"لینک مستقیم فایل: {file_url}")

        # ۵) فایل موقت برای پیش‌نمایش
        tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        preview_path = tmp.name
        tmp.close()

        # ۶) برش دقیقه‌ی اول با FFmpeg
        cmd = [
            "ffmpeg", "-y",
            "-ss", "0", "-t", "60",
            "-i", file_url,
            "-c", "copy",
            preview_path
        ]
        logger.info("اجرا FFmpeg: " + " ".join(cmd))
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if proc.returncode != 0:
            err = proc.stderr.decode(errors="ignore")
            logger.error(f"FFmpeg خطا: {err}")
        else:
            # ۷) ارسال پیش‌نمایش
            await client.send_video(
                chat_id=dest,
                video=preview_path,
                caption="📺 Preview (First minute)",
                supports_streaming=True
            )
            logger.info("پیش‌نمایش ارسال شد")

        # ۸) پاک‌کردن فایل موقت
        try:
            os.remove(preview_path)
        except OSError:
            pass

        # ۹) فوروارد کامل ویدیو
        await message.copy(dest, caption=new_caption)
        logger.info(f"ویدیوی کامل (message_id={message.id}) فوروارد شد")

    else:
        # پیام‌های غیر ویدیو
        await message.copy(dest, caption=new_caption)
        logger.info(f"پیام (message_id={message.id}) فوروارد شد")

# ——— Health Check با Flask ———
app = Flask(__name__)

@app.route("/healthz")
def healthz():
    return jsonify(status="ok")

def run_healthz():
    app.run(host="0.0.0.0", port=8080)

if __name__ == "__main__":
    Thread(target=run_healthz, daemon=True).start()
    logger.info("Health check در http://0.0.0.0:8080/healthz در حال اجراست")
    bot.run()
