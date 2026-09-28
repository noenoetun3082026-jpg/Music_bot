import os
import random

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

TOKEN = os.getenv("BOT_TOKEN")

MAX_PLAYERS = 5

games = {}


def card_value(card):
    rank = card[:-1]

    if rank == "A":
        return 1

    if rank in ("10", "J", "Q", "K"):
        return 0

    return int(rank)


def score(cards):
    return sum(card_value(card) for card in cards) % 10


def create_deck():
    suits = ["♠", "♥", "♦", "♣"]
    ranks = [
        "A", "2", "3", "4", "5", "6", "7",
        "8", "9", "10", "J", "Q", "K"
    ]

    deck = [rank + suit for suit in suits for rank in ranks]
    random.shuffle(deck)
    return deck


def keyboard(game):
    buttons = []

    if not game["started"]:
        buttons.append([
            InlineKeyboardButton(
                "🎴 ဝင်ကစားရန်",
                callback_data="join"
            )
        ])

        if len(game["players"]) > 0:
            buttons.append([
                InlineKeyboardButton(
                    "▶️ ဂိမ်းစရန်",
                    callback_data="start"
                )
            ])

    return InlineKeyboardMarkup(buttons)


def lobby_text(game):
    players = game["players"]

    if players:
        player_list = "\n".join(
            f"{i}. {name}"
            for i, name in enumerate(players.values(), 1)
        )
    else:
        player_list = "မရှိသေးပါ"

    return (
        "🃏 <b>SHAN KOE MEE</b>\n\n"
        f"👑 အခန်းဖွင့်သူ/ဘဏ်တိုက်: "
        f"<b>{game['owner_name']}</b>\n"
        f"👥 ကစားသမား: "
        f"<b>{len(players)}/{MAX_PLAYERS}</b>\n\n"
        f"{player_list}\n\n"
        "ဝင်ကစားရန် ခလုတ်နှိပ်ပါ။"
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🃏 <b>ရှမ်းကိုးမီး အပျော်တမ်း Bot</b>\n\n"
        "/game — GP ထဲမှာ အခန်းဖွင့်ရန်\n"
        "/help — စည်းမျဉ်းကြည့်ရန်",
        parse_mode="HTML"
    )


async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    await update.message.reply_text(
        "📖 <b>ရှမ်းကိုးမီး အခြေခံစည်းမျဉ်း</b>\n\n"
        "A = ၁ မှတ်\n"
        "2–9 = မျက်နှာတန်ဖိုးအတိုင်း\n"
        "10/J/Q/K = ၀ မှတ်\n\n"
        "စုစုပေါင်းရဲ့ နောက်ဆုံးဂဏန်းကို အမှတ်အဖြစ်ယူပါတယ်။\n\n"
        "⭐ ဖဲ ၂ ရွက်နဲ့ ၈ သို့မဟုတ် ၉ ရရင် Auto Shan ဖြစ်ပါတယ်။\n\n"
        "⚠️ ငွေလောင်းကြေးမပါသော အပျော်တမ်းဂိမ်းဖြစ်ပါတယ်။",
        parse_mode="HTML"
    )


async def game_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    chat = update.effective_chat
    user = update.effective_user

    if chat.type not in ("group", "supergroup"):
        await update.message.reply_text(
            "❌ /game ကို GP ထဲမှာ အသုံးပြုပါ။"
        )
        return

    if chat.id in games:
        await update.message.reply_text(
            "⚠️ ဒီ GP မှာ Game တစ်ပွဲရှိပြီးသားပါ။"
        )
        return

    games[chat.id] = {
        "owner_id": user.id,
        "owner_name": user.full_name,
        "players": {},
        "started": False,
    }

    game = games[chat.id]

    await update.message.reply_text(
        lobby_text(game),
        parse_mode="HTML",
        reply_markup=keyboard(game)
    )


async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id
    user = query.from_user

    game = games.get(chat_id)

    if game is None:
        await query.answer(
            "❌ Game မရှိတော့ပါ။ /game ပြန်လုပ်ပါ။",
            show_alert=True
        )
        return

    if query.data == "join":

        if game["started"]:
            await query.answer(
                "❌ Game စပြီးပါပြီ။",
                show_alert=True
            )
            return

        if user.id in game["players"]:
            await query.answer(
                "✅ ဝင်ပြီးသားပါ။",
                show_alert=True
            )
            return

        if len(game["players"]) >= MAX_PLAYERS:
            await query.answer(
                "❌ Player 5 ယောက်ပြည့်နေပါပြီ။",
                show_alert=True
            )
            return

        game["players"][user.id] = user.full_name

        await query.edit_message_text(
            lobby_text(game),
            parse_mode="HTML",
            reply_markup=keyboard(game)
        )
        return

    if query.data == "start":

        if user.id != game["owner_id"]:
            await query.answer(
                "❌ အခန်းဖွင့်သူပဲ ဂိမ်းစနိုင်ပါတယ်။",
                show_alert=True
            )
            return

        if len(game["players"]) == 0:
            await query.answer(
                "❌ Player အနည်းဆုံး ၁ ယောက် ဝင်ရပါမယ်။",
                show_alert=True
            )
            return

        game["started"] = True

        deck = create_deck()

        results = []

        for player_id, name in game["players"].items():
            cards = [
                deck.pop(),
                deck.pop()
            ]

            total = score(cards)

            if total in (8, 9):
                special = " ⭐ AUTO SHAN"
            else:
                special = ""

            results.append(
                f"👤 <b>{name}</b>\n"
                f"🎴 {' '.join(cards)}\n"
                f"🔢 အမှတ်: <b>{total}</b>{special}"
            )

        await query.edit_message_text(
            "🃏 <b>SHAN KOE MEE — GAME START</b>\n\n"
            + "\n\n".join(results),
            parse_mode="HTML"
        )


def main():
    if not TOKEN:
        raise RuntimeError(
            "BOT_TOKEN မတွေ့ပါ။ Deployka ENV မှာ "
            "BOT_TOKEN ထည့်ပါ။"
        )

    app = Application.builder().token(TOKEN).build()

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("help", help_command)
    )

    app.add_handler(
        CommandHandler("game", game_command)
    )

    app.add_handler(
        CallbackQueryHandler(button_handler)
    )

    print("🃏 SHAN KOE MEE BOT STARTED")

    app.run_polling()


if __name__ == "__main__":
    main()
