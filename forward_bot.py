import os
import logging
import tempfile
import subprocess
import aiohttp

from pyrogram import Client, filters, utils
from flask import Flask, jsonify
from threading import Thread

# ——— Monkey-patch برای باگ Peer ID ———
original = utils.get_peer_type
def patched(peer):
    if isinstance(peer, int):
        return "user" if peer > 0 else "channel"
    return original(peer)
utils.get_peer_type = patched

# ——— Logging ———
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ——— Env vars ———
API_ID         = int(os.getenv("API_ID"))
API_HASH       = os.getenv("API_HASH")
BOT_TOKEN      = os.getenv("BOT_TOKEN")
SOURCE_CHANNEL = int(os.getenv("SOURCE_CHANNEL"))
DEST_CHANNEL   = int(os.getenv("DEST_CHANNEL"))

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

async def fetch_file_path(file_id: str) -> str | None:
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getFile?file_id={file_id}"
    async with aiohttp.ClientSession() as sess:
        async with sess.get(url) as resp:
            j = await resp.json()
    if not j.get("ok"):
        logger.error(f"getFile error: {j}")
        return None
    return j["result"]["file_path"]

@bot.on_message(filters.chat(SOURCE_CHANNEL))
async def handle_message(c: Client, m):
    dest = DEST_CHANNEL
    # کپشن جدید
    first = (m.caption or "").split("\n",1)[0]
    new_cap = f"{first}\n\nenjoy hot webcams👙👇\n\nCamHot 🔥 ( @CamHotVIP )"

    if is_video_message(m):
        logger.info(f"video msg_id={m.id}, building preview…")
        media = m.video or m.document
        file_id = media.file_id

        # ۱) گرفتن file_path
        fp = await fetch_file_path(file_id)
        if not fp:
            await m.copy(dest, caption=new_cap)
            return

        file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{fp}"
        logger.info(f"direct URL: {file_url}")

        # ۲) دانلود بخش ابتدایی (برای جلوگیری از دانلود کامل)
        partial = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        part_path = partial.name
        partial.close()

        # این عدد را بسته به فرمت ویدیو دست‌کم ۲۰۰–۳۰۰ مگابایت انتخاب کنید
        range_bytes = "0-300000000"
        curl_cmd = [
            "curl", "-s", "-L",
            "-H", f"Range: bytes={range_bytes}",
            file_url, "-o", part_path
        ]
        logger.info("curl cmd: " + " ".join(curl_cmd))
        subprocess.run(curl_cmd, check=False)

        # ۳) برش ۶۰ ثانیهٔ اول با FFmpeg
        preview_path = part_path + ".preview.mp4"
        ff_cmd = [
            "ffmpeg", "-y",
            "-ss", "0", "-t", "60",
            "-i", part_path,
            "-c", "copy",
            preview_path
        ]
        logger.info("ffmpeg cmd: " + " ".join(ff_cmd))
        proc = subprocess.run(ff_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if proc.returncode != 0:
            logger.error("ffmpeg error: " + proc.stderr.decode(errors="ignore"))
        else:
            # ۴) ارسال پیش‌نمایش
            await c.send_video(
                chat_id=dest,
                video=preview_path,
                caption="📺 Preview (First minute)",
                supports_streaming=True
            )
            logger.info("preview sent")

        # ۵) پاک‌سازی موقت‌ها
        for p in (part_path, preview_path):
            try: os.remove(p)
            except: pass

        # ۶) فوروارد کامل
        await m.copy(dest, caption=new_cap)
        logger.info("full video forwarded")

    else:
        await m.copy(dest, caption=new_cap)
        logger.info(f"msg_id={m.id} forwarded")

# Health check
app = Flask(__name__)
@app.route("/healthz")
def healthz(): return jsonify(status="ok")
def run_healthz(): app.run(host="0.0.0.0", port=8080)

if __name__ == "__main__":
    Thread(target=run_healthz, daemon=True).start()
    bot.run()
