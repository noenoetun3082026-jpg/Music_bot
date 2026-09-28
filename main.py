import logging
import random
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

# Logging သတ်မှတ်ခြင်း
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ဖဲချပ်များနှင့် အရောင်များ
suits = ['♠', '♣', '♥', '♦']
ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']

def get_card_value(rank):
    """ဖဲချပ်တစ်ချပ်ချင်းစီ၏ တန်ဖိုးကို တွက်ချက်ခြင်း"""
    if rank in ['J', 'Q', 'K', '10']:
        return 0
    elif rank == 'A':
        return 1
    else:
        return int(rank)

def calculate_score(hand):
    """ဖဲချပ်များ၏ စုစုပေါင်းရမှတ် (၁၀ ဖြင့်စား၍ အကြွင်းယူရန်)"""
    total = sum(get_card_value(card['rank']) for card in hand)
    return total % 10

def create_deck():
    """ဖဲထုပ်အသစ် ဖန်တီးပြီး ရောနှောခြင်း"""
    deck = [{'rank': r, 'suit': s} for s in suits for r in ranks]
    random.shuffle(deck)
    return deck

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bot စတင်အလုပ်လုပ်ချိန် Greeting မက်ဆေ့ချ်"""
    await update.message.reply_text(
        "မင်္ဂလာပါ! 🎴 ရှမ်းကိုးမီး Bot မှ ကြိုဆိုပါတယ်။\n\n"
        "Group ထဲတွင် ရှမ်းကိုးမီး စတင်ကစားရန် `/shankoepee` ဟု ရိုက်နှိပ်ပါ။"
    )

async def play_shan_koe_mee(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ရှမ်းကိုးမီး ကတ်ဝေပေးခြင်းနှင့် ရမှတ်တွက်ချက်ခြင်း"""
    deck = create_deck()
    
    # ကစားသမားအတွက် ကတ် ၂ ချပ် ပေးခြင်း
    player_hand = [deck.pop(), deck.pop()]
    p_score = calculate_score(player_hand)
    
    player_cards_str = " ".join([f"{c['rank']}{c['suit']}" for c in player_hand])
    
    result_text = (
        f"🎴 **ရှမ်းကိုးမီး ကစားပွဲ** 🎴\n\n"
        f"👤 ကစားသူ: {update.effective_user.first_name}\n"
        f"🎴 သင့်လက်ထဲပါလာသော ဖဲချပ်များ: **{player_cards_str}**\n"
        f"📊 ရမှတ်: **{p_score} แต้ม**"
    )
    
    # ရှမ်း (သို့) ကိုးမီး ထွက်ခြင်း ရှိမရှိ စစ်ဆေးခြင်း
    if p_score in [8, 9]:
        result_text += "\n\n✨ **🎉 ဇယားကြီး (Shan / Koe Mee) ထွက်ပါပြီ! 🎉** ✨"
    
    await update.message.reply_text(result_text, parse_mode="Markdown")

def main():
    # Telegram BotFather မှ ရရှိလာသော Token ကို ဤနေရာတွင် ထည့်ပါ
    TOKEN = "YOUR_BOT_TOKEN_HERE"
    
    app = ApplicationBuilder().token(TOKEN).build()
    
    # Command Handlers များကို ချိတ်ဆက်ခြင်း
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("shankoepee", play_shan_koe_mee))
    
    print("Bot စတင်အလုပ်လုပ်နေပါပြီ...")
    app.run_polling()

if __name__ == '__main__':
    main()
