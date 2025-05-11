from pyrogram import Client, filters

api_id = 8891803  # عددی که از my.telegram.org گرفتی
api_hash = "5908205e3e6f563d76e6bd8f87723c1d"
bot_token = "7399010656:AAF6hrFA15MyBoDEfuI2qN_OZgv5fcbwlLA"

app = Client("forward_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

source_channel = -1002650282186     # آی‌دی کانال مبدأ
destination_channel = -1002293369181 # آی‌دی کانال مقصد

@app.on_message(filters.chat(source_channel))
async def forward_post(client, message):
    await message.forward(destination_channel)

app.run()
