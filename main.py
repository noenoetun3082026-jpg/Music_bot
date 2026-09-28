import os
import random
import logging

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

TOKEN = os.getenv("BOT_TOKEN")

# Telegram sticker set
STICKER_SET_NAME = "Playing_Cards"

MAX_PLAYERS = 5

games = {}

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


# =========================================================
# SHAN KOE MEE CARDS
# =========================================================

SUITS = ["♠", "♥", "♦", "♣"]

RANKS = [
    "A",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "10",
    "J",
    "Q",
    "K",
]


def create_deck():
    deck = []

    for suit in SUITS:
        for rank in RANKS:
            deck.append(rank + suit)

    random.shuffle(deck)

    return deck


# =========================================================
# SHAN KOE MEE SCORE
# =========================================================

def card_value(card):

    rank = card[:-1]

    if rank == "A":
        return 1

    if rank in ["10", "J", "Q", "K"]:
        return 0

    return int(rank)


def calculate_score(hand):

    total = sum(
        card_value(card)
        for card in hand
    )

    return total % 10


def is_auto_shan(hand):

    return (
        len(hand) == 2
        and calculate_score(hand) in [8, 9]
    )


# =========================================================
# STICKER SET
# =========================================================

async def load_card_stickers(bot):

    sticker_set = await bot.get_sticker_set(
        name=STICKER_SET_NAME
    )

    stickers = sticker_set.stickers

    if len(stickers) < 52:
        raise RuntimeError(
            f"{STICKER_SET_NAME} မှာ "
            f"{len(stickers)} ချပ်ပဲရှိပါတယ်။ "
            "52 ချပ်လိုပါတယ်။"
        )

    return stickers[:52]


# =========================================================
# CREATE STICKER MAP
# =========================================================

async def create_sticker_map(bot):

    stickers = await load_card_stickers(bot)

    # IMPORTANT:
    # Playing_Cards sticker set ထဲက order ကို
    # A♠ -> 2♠ -> ... -> K♠
    # A♥ -> ... -> K♥
    # A♦ -> ... -> K♦
    # A♣ -> ... -> K♣
    # လို့သတ်မှတ်ထားပါတယ်။

    cards = [
        rank + suit
        for suit in SUITS
        for rank in RANKS
    ]

    mapping = {}

    for card, sticker in zip(cards, stickers):
        mapping[card] = sticker.file_id

    return mapping


# =========================================================
# PLAYER NAME
# =========================================================

def player_name(user):

    if user.username:
        return "@" + user.username

    return user.first_name or "Player"


# =========================================================
# LOBBY
# =========================================================

def lobby_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🎴 ဝင်ကစားရန်",
                    callback_data="join_game",
                )
            ],
            [
                InlineKeyboardButton(
                    "▶️ ဂိမ်းစရန်",
                    callback_data="start_game",
                )
            ],
        ]
    )


def draw_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🃏 တတိယကဒ်ယူရန်",
                    callback_data="draw_card",
                )
            ]
        ]
    )


def lobby_text(game):

    text = (
        "🃏 <b>SHAN KOE MEE</b>\n\n"
        f"👤 အခန်းဖွင့်သူ: "
        f"<b>{game['creator_name']}</b>\n"
        f"👥 ကစားသမား: "
        f"<b>{len(game['players'])}/{MAX_PLAYERS}</b>\n\n"
    )

    for i, user in enumerate(
        game["players"],
        1,
    ):
        text += (
            f"{i}. "
            f"{player_name(user)}\n"
        )

    text += "\n🎴 ဝင်ကစားရန် ခလုတ်နှိပ်ပါ။"

    return text


# =========================================================
# START
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    await update.message.reply_text(
        "🃏 <b>SHAN KOE MEE BOT</b>\n\n"
        "/game — ဂိမ်းဖွင့်ရန်\n"
        "/help — အသုံးပြုနည်း\n"
        "/testcards — Playing Cards စစ်ရန်",
        parse_mode="HTML",
    )


# =========================================================
# HELP
# =========================================================

async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    await update.message.reply_text(
        "🃏 <b>SHAN KOE MEE</b>\n\n"
        "🎮 /game — အခန်းဖွင့်ရန်\n"
        "🧪 /testcards — ဖဲ Sticker စမ်းရန်\n\n"
        "🅰️ A = 1 မှတ်\n"
        "2–9 = မူရင်းအမှတ်\n"
        "10/J/Q/K = 0 မှတ်\n"
        "✨ 8 / 9 = Auto Shan / Koe Mee\n\n"
        "👥 Player အများဆုံး 5 ယောက်",
        parse_mode="HTML",
    )


# =========================================================
# TEST STICKERS
# =========================================================

async def test_cards(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    try:

        stickers = await load_card_stickers(
            context.bot
        )

    except Exception as e:

        logging.error(
            "Sticker error: %s",
            e,
        )

        await update.message.reply_text(
            "❌ Playing_Cards sticker set ကို "
            "ဖတ်မရပါ။\n\n"
            f"Error: {e}"
        )

        return

    await update.message.reply_text(
        f"🃏 Playing_Cards\n"
        f"Sticker: {len(stickers)} ချပ်\n\n"
        "ပထမ 5 ချပ်ကို စမ်းပြမယ်။"
    )

    for sticker in stickers[:5]:

        await context.bot.send_sticker(
            chat_id=update.effective_chat.id,
            sticker=sticker.file_id,
        )


# =========================================================
# GAME
# =========================================================

async def game_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    chat = update.effective_chat
    user = update.effective_user

    if chat.type not in [
        "group",
        "supergroup",
    ]:

        await update.message.reply_text(
            "❌ Group ထဲမှာပဲ /game သုံးပါ။"
        )

        return

    if chat.id in games:

        await update.message.reply_text(
            "⚠️ ဒီ Group မှာ ဂိမ်းရှိပြီးသားပါ။"
        )

        return

    # Test sticker set before opening game
    try:

        sticker_map = await create_sticker_map(
            context.bot
        )

    except Exception as e:

        await update.message.reply_text(
            "❌ Playing_Cards sticker set "
            "မရသေးပါ။\n\n"
            f"{e}"
        )

        return

    games[chat.id] = {
        "creator_id": user.id,
        "creator_name": player_name(user),
        "players": [user],
        "deck": [],
        "hands": {},
        "sticker_map": sticker_map,
        "started": False,
    }

    game = games[chat.id]

    await update.message.reply_text(
        lobby_text(game),
        reply_markup=lobby_keyboard(),
        parse_mode="HTML",
    )


# =========================================================
# SEND CARD STICKER
# =========================================================

async def send_card(
    bot,
    chat_id,
    card,
    sticker_map,
):

    sticker_id = sticker_map.get(card)

    if not sticker_id:

        await bot.send_message(
            chat_id=chat_id,
            text=f"❌ {card} sticker မတွေ့ပါ။",
        )

        return

    await bot.send_sticker(
        chat_id=chat_id,
        sticker=sticker_id,
    )


# =========================================================
# BUTTON
# =========================================================

async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    await query.answer()

    chat = query.message.chat
    user = query.from_user

    game = games.get(chat.id)

    if not game:

        await query.answer(
            "❌ ဂိမ်းမရှိတော့ပါ။",
            show_alert=True,
        )

        return

    # =====================================================
    # JOIN
    # =====================================================

    if query.data == "join_game":

        if game["started"]:

            await query.answer(
                "❌ ဂိမ်းစပြီးပါပြီ။",
                show_alert=True,
            )

            return

        if any(
            p.id == user.id
            for p in game["players"]
        ):

            await query.answer(
                "✅ ဝင်ထားပြီးသားပါ။",
                show_alert=True,
            )

            return

        if len(game["players"]) >= MAX_PLAYERS:

            await query.answer(
                "❌ Player 5 ယောက်ပြည့်ပါပြီ။",
                show_alert=True,
            )

            return

        game["players"].append(user)

        await query.edit_message_text(
            lobby_text(game),
            reply_markup=lobby_keyboard(),
            parse_mode="HTML",
        )

        return

    # =====================================================
    # START GAME
    # =====================================================

    if query.data == "start_game":

        if game["started"]:

            await query.answer(
                "⚠️ ဂိမ်းစပြီးသားပါ။",
                show_alert=True,
            )

            return

        if user.id != game["creator_id"]:

            await query.answer(
                "❌ အခန်းဖွင့်သူပဲ စနိုင်ပါတယ်။",
                show_alert=True,
            )

            return

        game["started"] = True
        game["deck"] = create_deck()
        game["hands"] = {}

        await query.edit_message_text(
            "🃏 <b>SHAN KOE MEE — GAME START</b>\n\n"
            "🎴 ဖဲကဒ်များ ဝေပြီးပါပြီ။",
            parse_mode="HTML",
        )

        # =================================================
        # DEAL TWO CARDS
        # =================================================

        for player in game["players"]:

            hand = [
                game["deck"].pop(),
                game["deck"].pop(),
            ]

            game["hands"][player.id] = hand

            score = calculate_score(hand)

            # Card 1
            await send_card(
                context.bot,
                chat.id,
                hand[0],
                game["sticker_map"],
            )

            # Card 2
            await send_card(
                context.bot,
                chat.id,
                hand[1],
                game["sticker_map"],
            )

            # Result
            if is_auto_shan(hand):

                result = (
                    "✨ <b>AUTO SHAN / KOE MEE!</b> ✨\n\n"
                    f"👤 {player_name(player)}\n"
                    f"🔢 အမှတ်: <b>{score}</b>"
                )

            else:

                result = (
                    f"👤 <b>{player_name(player)}</b>\n"
                    f"🔢 အမှတ်: <b>{score}</b>\n\n"
                    "တတိယကဒ်လိုရင် Button နှိပ်ပါ။"
                )

            await context.bot.send_message(
                chat_id=chat.id,
                text=result,
                reply_markup=draw_keyboard(),
                parse_mode="HTML",
            )

        return

    # =====================================================
    # THIRD CARD
    # =====================================================

    if query.data == "draw_card":

        if not game["started"]:

            await query.answer(
                "❌ ဂိမ်းမစသေးပါ။",
                show_alert=True,
            )

            return

        if user.id not in game["hands"]:

            await query.answer(
                "❌ ဒီဂိမ်းမှာ မပါပါ။",
                show_alert=True,
            )

            return

        hand = game["hands"][user.id]

        if len(hand) >= 3:

            await query.answer(
                "⚠️ တတိယကဒ် ရပြီးသားပါ။",
                show_alert=True,
            )

            return

        if is_auto_shan(hand):

            await query.answer(
                "✨ 8 / 9 ဖြစ်ပြီးသားမို့ Auto Shan ပါ။",
                show_alert=True,
            )

            return

        third = game["deck"].pop()

        hand.append(third)

        score = calculate_score(hand)

        await send_card(
            context.bot,
            chat.id,
            third,
            game["sticker_map"],
        )

        if score in [8, 9]:

            text = (
                "✨ <b>KOE MEE!</b> ✨\n\n"
                f"👤 {player_name(user)}\n"
                f"🔢 အမှတ်: <b>{score}</b>"
            )

        else:

            text = (
                f"👤 <b>{player_name(user)}</b>\n"
                f"🔢 အမှတ်: <b>{score}</b>"
            )

        await context.bot.send_message(
            chat_id=chat.id,
            text=text,
            parse_mode="HTML",
        )

        return


# =========================================================
# ERROR
# =========================================================

async def error_handler(
    update,
    context,
):

    logging.error(
        "Bot error: %s",
        context.error,
    )


# =========================================================
# MAIN
# =========================================================

def main():

    if not TOKEN:

        raise RuntimeError(
            "BOT_TOKEN ENV မတွေ့ပါ။"
        )

    app = (
        Application.builder()
        .token(TOKEN)
        .build()
    )

    app.add_handler(
        CommandHandler(
            "start",
            start,
        )
    )

    app.add_handler(
        CommandHandler(
            "help",
            help_command,
        )
    )

    app.add_handler(
        CommandHandler(
            "game",
            game_command,
        )
    )

    app.add_handler(
        CommandHandler(
            "testcards",
            test_cards,
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            button_handler
        )
    )

    app.add_error_handler(
        error_handler
    )

    print(
        "🃏 SHAN KOE MEE BOT RUNNING..."
    )

    app.run_polling()


if __name__ == "__main__":
    main()
