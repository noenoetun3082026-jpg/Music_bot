import os
import random
from dataclasses import dataclass, field

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

TOKEN = os.getenv("BOT_TOKEN")

MAX_PLAYERS = 5


@dataclass
class Player:
    user_id: int
    name: str
    cards: list = field(default_factory=list)


@dataclass
class Game:
    chat_id: int
    owner_id: int
    owner_name: str
    players: dict = field(default_factory=dict)
    started: bool = False


games = {}


def card_value(card):
    rank = card[:-1]

    if rank == "A":
        return 1

    if rank in ["10", "J", "Q", "K"]:
        return 0

    return int(rank)


def hand_score(cards):
    return sum(card_value(c) for c in cards) % 10


def make_deck():
    suits = ["♠", "♥", "♦", "♣"]
    ranks = [
        "A", "2", "3", "4", "5", "6", "7",
        "8", "9", "10", "J", "Q", "K"
    ]

    deck = [f"{rank}{suit}" for suit in suits for rank in ranks]
    random.shuffle(deck)
    return deck


def game_text(game):
    players = list(game.players.values())

    if players:
        player_text = "\n".join(
            f"{i}. {p.name}"
            for i, p in enumerate(players, 1)
        )
    else:
        player_text = "မရှိသေးပါ"

    status = "🟢 ကစားနေပါပြီ" if game.started else "🟡 စောင့်နေသည်"

    return (
        "🃏 <b>SHAN KOE MEE</b>\n\n"
        f"👑 အခန်းဖွင့်သူ/ဘဏ်တိုက်: <b>{game.owner_name}</b>\n"
        f"👥 ကစားသမား: <b>{len(players)}/{MAX_PLAYERS}</b>\n\n"
        f"{player_text}\n\n"
        f"{status}"
    )


def lobby_keyboard(game):
    buttons = []

    if not game.started:
        buttons.append([
            InlineKeyboardButton(
                "🎴 ဝင်ကစားရန်",
                callback_data="join"
            )
        ])

        if game.players:
            buttons.append([
                InlineKeyboardButton(
                    "▶️ ဂိမ်းစရန်",
                    callback_data="start"
                )
            ])

    return InlineKeyboardMarkup(buttons)


def result_text(name, cards):
    score = hand_score(cards)

    if len(cards) == 2 and score in (8, 9):
        special = " ⭐ AUTO SHAN"
    else:
        special = ""

    return (
        f"🎴 <b>{name}</b>\n"
        f"ဖဲ: {' '.join(cards)}\n"
        f"အမှတ်: <b>{score}</b>{special}"
    )


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🃏 <b>ရှမ်းကိုးမီး အပျော်တမ်း Bot</b>\n\n"
        "/game — GP ထဲမှာ အခန်းဖွင့်ရန်\n"
        "/help — စည်းမျဉ်းကြည့်ရန်",
        parse_mode="HTML"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 <b>ရှမ်းကိုးမီး အခြေခံစည်းမျဉ်း</b>\n\n"
        "🅰️ A = 1 မှတ်\n"
        "2–9 = မျက်နှာတန်ဖိုးအတိုင်း\n"
        "10/J/Q/K = 0 မှတ်\n\n"
        "🔢 စုစုပေါင်း၏ နောက်ဆုံးဂဏန်းကို အမှတ်အဖြစ်ယူသည်။\n"
        "⭐ ဖဲ ၂ ရွက်နဲ့ 8 သို့မဟုတ် 9 ရပါက Auto Shan ဖြစ်သည်။\n\n"
        "⚠️ ဤ Bot သည် ငွေလောင်းကြေးမပါသော အပျော်တမ်းကစားရန်သာ ဖြစ်သည်။",
        parse_mode="HTML"
    )


async def game_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    if chat.type not in ["group", "supergroup"]:
        await update.message.reply_text(
            "❌ /game ကို GP ထဲမှာပဲ အသုံးပြုပါ။"
        )
        return

    if chat.id in games:
        await update.message.reply_text(
            "⚠️ ဒီ GP မှာ Game တစ်ပွဲရှိပြီးသားပါ။"
        )
        return

    game = Game(
        chat_id=chat.id,
        owner_id=user.id,
        owner_name=user.full_name
    )

    games[chat.id] = game

    await update.message.reply_text(
        game_text(game),
        parse_mode="HTML",
        reply_markup=lobby_keyboard(game)
    )


async def callback_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id
    user = query.from_user

    game = games.get(chat_id)

    if not game:
        await query.answer(
            "❌ ဒီ Game မရှိတော့ပါ။ /game ပြန်လုပ်ပါ။",
            show_alert=True
        )
        return

    if query.data == "join":

        if game.started:
            await query.answer(
                "❌ Game စပြီးပါပြီ။",
                show_alert=True
            )
            return

        if user.id in game.players:
            await query.answer(
                "✅ သင်ဝင်ပြီးသားပါ။",
                show_alert=True
            )
            return

        if len(game.players) >= MAX_PLAYERS:
            await query.answer(
                "❌ Player 5 ယောက်ပြည့်နေပါပြီ။",
                show_alert=True
            )
            return

        game.players[user.id] = Player(
            user_id=user.id,
            name=user.full_name
        )

        await query.edit_message_text(
            game_text(game),
            parse_mode="HTML",
            reply_markup=lobby_keyboard(game)
        )
        return

    if query.data == "start":

        if user.id != game.owner_id:
            await query.answer(
                "❌ အခန်းဖွင့်သူပဲ Game စနိုင်ပါတယ်။",
                show_alert=True
            )
            return

        if not game.players:
            await query.answer(
                "❌ အနည်းဆုံး Player 1 ယောက် ဝင်ရပါမယ်။",
                show_alert=True
            )
            return

        game.started = True

        deck = make_deck()

        # Player တစ်ယောက်စီကို ဖဲ ၂ ရွက်ဝေ
        for player in game.players.values():
            player.cards = [deck.pop(), deck.pop()]

        results = [
            result_text(p.name, p.cards)
            for p in game.players.values()
        ]

        await query.edit_message_text(
            "🃏 <b>SHAN KOE MEE — GAME START!</b>\n\n"
            + "\n\n".join(results),
            parse_mode="HTML"
        )
        return


async def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN မတွေ့ပါ။ Deployka ENV မှာထည့်ပါ။")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("game", game_command))

    app.add_handler(
        CallbackQueryHandler(callback_handler)
    )

    print("🃏 Shan Koe Mee Bot is running...")
    await app.run_polling()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
