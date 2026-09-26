import os
from pyrogram import Client, filters
from pytgcalls import PyTgCalls
from pytgcalls.types import AudioPiped
import yt_dlp

# BotFather က ရထားတဲ့ Token နဲ့ API တွေကို ဒီမှာ ထည့်မယ် (Environment Variables ကနေ ယူသုံးမှာပါ)
API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

app = Client(
    "MusicBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

call_py = PyTgCalls(app)

@app.on_message(filters.command("start"))
async def start_command(client, message):
    await message.reply_text("မင်္ဂလာပါ! ငါက မင်းရဲ့ Music Bot ပါ။ /play [YouTube Link] လို့ ရိုက်ပြီး သီချင်းဖွင့်လို့ရပါတယ်။")

@app.on_message(filters.command("play"))
async def play_music(client, message):
    if len(message.command) < 2:
        await message.reply_text("ကျေးဇူးပြု၍ YouTube Link ထည့်ပေးပါ။ ဥပမာ: /play [Link]")
        return
        
    query = message.command[1]
    msg = await message.reply_text("သီချင်း ရှာနေပါတယ်...")

    ydl_opts = {'format': 'bestaudio', 'wohner': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            audio_url = info['url']
            title = info['title']
            
        await call_py.join_group_call(
            message.chat.id,
            AudioPiped(audio_url)
        )
        await msg.edit_text(f"ယခု ဖွင့်နေသည်: **{title}**")
    except Exception as e:
        await msg.edit_text(f"အမှားအယွင်း ဖြစ်သွား습니다: {e}")

app.start()
call_py.start()
print("Bot အလုပ်စလုပ်နေပါပြီ...")
from pyrogram import idle
idle()
