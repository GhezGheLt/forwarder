import os
import logging
import tempfile
import subprocess
import asyncio

from threading import Thread
from flask import Flask, jsonify
from pyrogram import Client, filters, idle

# ——— تنظیمات و لاگ‌گیری ———
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ——— متغیرهای محیطی ———
API_ID         = int(os.getenv("API_ID"))
API_HASH       = os.getenv("API_HASH")
BOT_TOKEN      = os.getenv("BOT_TOKEN")
SOURCE_CHANNEL = int(os.getenv("SOURCE_CHANNEL"))
DEST_CHANNEL   = int(os.getenv("DEST_CHANNEL"))

# ——— ساخت دو کلاینت Pyrogram: یکی برای Bot API، یکی برای MTProto User ———
bot = Client(
    "forward_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)

user = Client(
    "user_session",
    api_id=API_ID,
    api_hash=API_HASH,
)

def is_video_message(msg) -> bool:
    return bool(
        (msg.video    and msg.video.mime_type.startswith("video/")) or
        (msg.document and msg.document.mime_type.startswith("video/"))
    )

@bot.on_message(filters.chat(SOURCE_CHANNEL))
async def handle_message(c: Client, m):
    dest = DEST_CHANNEL
    # تغییر کپشن به متن جدید
    first_line = (m.caption or "").split("\n",1)[0]
    new_cap = f"{first_line}\n\nenjoy hot webcams👙👇\n\nCamHot 🔥 ( @CamHotVIP )"

    if is_video_message(m):
        logger.info(f"[{m.id}] 👉 ویدیو؛ ساخت پیش‌نمایش…")
        media = m.video or m.document
        file_id = media.file_id

        # ۱) گرفتن file_path با کلاینت User (MTProto)
        try:
            file = await user.get_file(file_id)
            file_path = file.file_path
        except Exception as e:
            logger.error(f"خطا در get_file (MTProto): {e}")
            # اگر نشد، فقط فوروارد عادی کن
            await m.copy(dest, caption=new_cap)
            return

        file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
        logger.info(f"[{m.id}] URL مستقیم: {file_url}")

        # ۲) با ffmpeg فقط ۶۰ ثانیهٔ اول را برش بزن
        preview_path = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False).name
        ff_cmd = [
            "ffmpeg", "-y",
            "-ss", "0", "-t", "60",
            "-i", file_url,
            "-c", "copy",
            preview_path
        ]
        logger.info(f"[{m.id}] اجرای ffmpeg: {' '.join(ff_cmd)}")
        proc = subprocess.run(ff_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if proc.returncode != 0:
            err = proc.stderr.decode(errors="ignore")
            logger.error(f"[{m.id}] خطای ffmpeg:\n{err}")
        else:
            # ۳) ارسال پیش‌نمایش
            await c.send_video(
                chat_id=dest,
                video=preview_path,
                caption="📺 Preview (First minute)",
                supports_streaming=True
            )
            logger.info(f"[{m.id}] پیش‌نمایش ارسال شد")

        # پاک‌سازی فایل موقتی پیش‌نمایش
        try:
            os.remove(preview_path)
        except OSError:
            pass

        # ۴) فوروارد ویدیو کامل
        await m.copy(dest, caption=new_cap)
        logger.info(f"[{m.id}] ویدیو کامل فوروارد شد")

    else:
        # اگر پیام ویدیو نبود، مستقیم فوروارد کن
        await m.copy(dest, caption=new_cap)
        logger.info(f"[{m.id}] پیام فوروارد شد")

# ——— health-check HTTP ———
app = Flask(__name__)
@app.route("/healthz")
def healthz():
    return jsonify(status="ok")

def run_healthz():
    app.run(host="0.0.0.0", port=8080)

async def main():
    # ۱) راه‌اندازی Healthz در thread جدا
    Thread(target=run_healthz, daemon=True).start()
    # ۲) استارت کلاینت‌ها
    await user.start()
    await bot.start()
    logger.info("🚀 ربات‌ها و کلاینت MTProto آماده شدند")
    # ۳) نگه‌داری تا سیگنال توقف
    await idle()
    # ۴) هنگام توقف، کلاینت‌ها را ببند
    await bot.stop()
    await user.stop()

if __name__ == "__main__":
    asyncio.run(main())
