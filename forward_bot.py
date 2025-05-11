from pyrogram import Client, filters

api_id = 8891803
api_hash = "5908205e3e6f563d76e6bd8f87723c1d"
bot_token = "7399010656:AAF6hrFA15MyBoDEfuI2qN_OZgv5fcbwlLA"

app = Client("forward_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

source_channel = -1002650282186
destination_channel = -1002293369181  # آیدی عددی کانال مقصد

@app.on_message(filters.chat(source_channel))
async def forward_and_edit_caption(client, message):
    try:
        # تلاش برای resolve کردن آیدی عددی کانال
        try:
            await client.get_chat(destination_channel)
        except Exception as e:
            print("get_chat error:", e)
            return

        original_caption = message.caption or ""
        first_line = original_caption.split('\n')[0] if original_caption else ""

        new_caption = (
            f"{first_line}\n\n"
            "enjoy hot webcams👙👇\n\n"
            "[CamHot 🔥](https://t.me/+qY4VEKbgX0cxMmEy)"
        )

        if message.photo:
            await client.send_photo(destination_channel, photo=message.photo.file_id, caption=new_caption, parse_mode="Markdown")
        elif message.video:
            await client.send_video(destination_channel, video=message.video.file_id, caption=new_caption, parse_mode="Markdown")
        elif message.document:
            await client.send_document(destination_channel, document=message.document.file_id, caption=new_caption, parse_mode="Markdown")
        elif message.text:
            await client.send_message(destination_channel, text=new_caption, parse_mode="Markdown")
        else:
            print("Unsupported message type.")

    except Exception as e:
        print("Error forwarding and editing caption:", e)

app.run()
