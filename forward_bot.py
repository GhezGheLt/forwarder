from pyrogram import Client, filters

api_id = 8891803
api_hash = "5908205e3e6f563d76e6bd8f87723c1d"
bot_token = "7399010656:AAF6hrFA15MyBoDEfuI2qN_OZgv5fcbwlLA"

app = Client("forward_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

source_channel = -1002650282186
destination_channel = -1002293369181

@app.on_message(filters.chat(source_channel))
async def forward_post(client, message):
    caption = message.caption
    if caption:
        # گرفتن فقط خط اول
        first_line = caption.split('\n')[0]
        # ساختن کپشن جدید
        new_caption = f"{first_line}\n\nenjoy hot webcams👙👇\n\nCamHot 🔥 (https://t.me/+qY4VEKbgX0cxMmEy)"
        # ارسال با مدیا (عکس، ویدیو و ...)
        if message.photo:
            await client.send_photo(destination_channel, photo=message.photo.file_id, caption=new_caption)
        elif message.video:
            await client.send_video(destination_channel, video=message.video.file_id, caption=new_caption)
        elif message.document:
            await client.send_document(destination_channel, document=message.document.file_id, caption=new_caption)
        else:
            # اگر فقط متنی باشه
            await client.send_message(destination_channel, new_caption)
    else:
        # اگر کپشن نداشت، مستقیم فروارد کن
        await message.forward(destination_channel)

app.run()
