import os
import random
import logging

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# =========================================================
# SETTINGS
# =========================================================

TOKEN = os.getenv("BOT_TOKEN")

MAX_PLAYERS = 5

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# Active games
games = {}


# =========================================================
# CARD SYSTEM
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

SUIT_API = {
    "♠": "S",
    "♥": "H",
    "♦": "D",
    "♣": "C",
}


def create_deck():
    """
    Create a normal 52-card deck.
    """
    deck = []

    for suit in SUITS:
        for rank in RANKS:
            deck.append(rank + suit)

    random.shuffle(deck)

    return deck


def card_value(card):
    """
    Shan Koe Mee card value.
    """

    rank = card[:-1]

    if rank == "A":
        return 1

    if rank in ["10", "J", "Q", "K"]:
        return 0

    return int(rank)


def calculate_score(hand):
    """
    Last digit of total.
    """

    total = sum(card_value(card) for card in hand)

    return total % 10


def is_auto_shan(hand):
    """
    Two-card 8 or 9.
    """

    if len(hand) != 2:
        return False

    return calculate_score(hand) in [8, 9]


def card_image_url(card):
    """
    Convert card to Deck of Cards API image URL.

    Example:
    AS = Ace of Spades
    7H = Seven of Hearts
    0S = Ten of Spades
    """

    rank = card[:-1]
    suit = card[-1]

    if rank == "10":
        api_rank = "0"
    else:
        api_rank = rank

    api_suit = SUIT_API[suit]

    return f"https://deckofcardsapi.com/static/img/{api_rank}{api_suit}.png"


# =========================================================
# GAME HELPERS
# =========================================================

def get_game(chat_id):
    return games.get(chat_id)


def player_name(user):
    if user.username:
        return f"@{user.username}"

    return user.first_name or "Player"


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


def game_keyboard():
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
    creator = game["creator_name"]

    players = game["players"]

    text = (
        "🃏 <b>SHAN KOE MEE</b>\n\n"
        f"👤 အခန်းဖွင့်သူ: <b>{creator}</b>\n"
        f"👥 ကစားသမား: <b>{len(players)}/{MAX_PLAYERS}</b>\n\n"
    )

    if not players:
        text += "မရှိသေးပါ\n\n"

    else:
        for i, user in enumerate(players, 1):
            text += f"{i}. {player_name(user)}\n"

        text += "\n"

    text += "🎴 ဝင်ကစားရန် ခလုတ်နှိပ်ပါ။"

    return text


# =========================================================
# START
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🎀 <b>SHAN KOE MEE BOT</b>\n\n"
        "🃏 Group ထဲမှာ ကစားနိုင်ပါတယ်။\n\n"
        "🎮 /game — ဂိမ်းစရန်\n"
        "❓ /help — အသုံးပြုနည်း",
        parse_mode="HTML",
    )


# =========================================================
# HELP
# =========================================================

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🎀 <b>SHAN KOE MEE HELP</b>\n\n"
        "🎮 /game\n"
        "ဂိမ်းအခန်းဖွင့်ရန်\n\n"
        "🃏 ကဒ် ၂ ချပ်ရမယ်\n"
        "🔢 10/J/Q/K = 0 မှတ်\n"
        "🅰️ A = 1 မှတ်\n"
        "✨ ၈ / ၉ = Auto Shan / Koe Mee\n"
        "➕ ၈ / ၉ မဟုတ်ရင် တတိယကဒ်ယူနိုင်ပါတယ်။\n\n"
        "👥 Player အများဆုံး ၅ ယောက်",
        parse_mode="HTML",
    )


# =========================================================
# CREATE GAME
# =========================================================

async def game_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat = update.effective_chat
    user = update.effective_user

    # Group only
    if chat.type not in ["group", "supergroup"]:

        await update.message.reply_text(
            "❌ ဒီ command ကို Group ထဲမှာပဲ အသုံးပြုပါ။"
        )

        return

    # Existing game
    if chat.id in games:

        await update.message.reply_text(
            "⚠️ ဒီ Group မှာ ဂိမ်းအခန်းရှိပြီးသားပါ။"
        )

        return

    games[chat.id] = {
        "creator_id": user.id,
        "creator_name": player_name(user),
        "players": [user],
        "deck": [],
        "hands": {},
        "started": False,
        "message_id": None,
    }

    game = games[chat.id]

    message = await update.message.reply_text(
        lobby_text(game),
        reply_markup=lobby_keyboard(),
        parse_mode="HTML",
    )

    game["message_id"] = message.message_id


# =========================================================
# BUTTON HANDLER
# =========================================================

async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    await query.answer()

    chat = query.message.chat
    user = query.from_user

    game = get_game(chat.id)

    if not game:

        await query.answer(
            "❌ ဂိမ်းမရှိတော့ပါ။ /game နဲ့ ပြန်စပါ။",
            show_alert=True,
        )

        return

    # =====================================================
    # JOIN GAME
    # =====================================================

    if query.data == "join_game":

        if game["started"]:

            await query.answer(
                "❌ ဂိမ်းစပြီးပါပြီ။",
                show_alert=True,
            )

            return

        # Already joined
        if any(p.id == user.id for p in game["players"]):

            await query.answer(
                "✅ ဝင်ထားပြီးသားပါ။",
                show_alert=True,
            )

            return

        # Full
        if len(game["players"]) >= MAX_PLAYERS:

            await query.answer(
                "❌ Player ၅ ယောက်ပြည့်သွားပါပြီ။",
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

        # Must be creator
        if user.id != game["creator_id"]:

            await query.answer(
                "❌ အခန်းဖွင့်သူပဲ ဂိမ်းစနိုင်ပါတယ်။",
                show_alert=True,
            )

            return

        if len(game["players"]) < 1:

            await query.answer(
                "❌ Player မရှိသေးပါ။",
                show_alert=True,
            )

            return

        game["started"] = True
        game["deck"] = create_deck()
        game["hands"] = {}

        # Change lobby message
        await query.edit_message_text(
            "🃏 <b>SHAN KOE MEE — GAME START</b>\n\n"
            "🎴 ကဒ်များဝေပြီးပါပြီ။",
            parse_mode="HTML",
        )

        # Deal 2 cards to each player
        for player in game["players"]:

            if len(game["deck"]) < 2:
                break

            hand = [
                game["deck"].pop(),
                game["deck"].pop(),
            ]

            game["hands"][player.id] = hand

            score_value = calculate_score(hand)

            caption = (
                "🃏 <b>SHAN KOE MEE</b>\n\n"
                f"👤 <b>{player_name(player)}</b>\n\n"
                f"🔢 အမှတ်: <b>{score_value}</b>"
            )

            if is_auto_shan(hand):

                caption += (
                    "\n\n"
                    "✨ <b>AUTO SHAN / KOE MEE!</b> ✨"
                )

            else:

                caption += (
                    "\n\n"
                    "➕ တတိယကဒ်လိုရင် Button ကိုနှိပ်ပါ။"
                )

            media = [
                InputMediaPhoto(
                    media=card_image_url(hand[0]),
                    caption=caption,
                    parse_mode="HTML",
                ),
                InputMediaPhoto(
                    media=card_image_url(hand[1])
                ),
            ]

            try:

                await context.bot.send_media_group(
                    chat_id=chat.id,
                    media=media,
                )

            except Exception as e:

                logging.error(
                    "Card image error: %s",
                    e,
                )

                await context.bot.send_message(
                    chat_id=chat.id,
                    text=(
                        f"🃏 {player_name(player)}\n"
                        f"🔢 အမှတ်: {score_value}"
                    ),
                )

        # Third card button
        await context.bot.send_message(
            chat_id=chat.id,
            text=(
                "🎴 <b>တတိယကဒ်လိုတဲ့ Player</b>\n"
                "ကိုယ်တိုင် Button နှိပ်ပါ။"
            ),
            reply_markup=game_keyboard(),
            parse_mode="HTML",
        )

        return

    # =====================================================
    # DRAW THIRD CARD
    # =====================================================

    if query.data == "draw_card":

        if not game["started"]:

            await query.answer(
                "❌ ဂိမ်းမစသေးပါ။",
                show_alert=True,
            )

            return

        # Player must be in game
        if user.id not in game["hands"]:

            await query.answer(
                "❌ ဒီဂိမ်းထဲမှာ မပါပါ။",
                show_alert=True,
            )

            return

        hand = game["hands"][user.id]

        # Already 3 cards
        if len(hand) >= 3:

            await query.answer(
                "⚠️ တတိယကဒ် ရပြီးသားပါ။",
                show_alert=True,
            )

            return

        # Auto Shan cannot draw
        if is_auto_shan(hand):

            await query.answer(
                "✨ ၈/၉ ထွက်ပြီးသားဖြစ်လို့ Auto Shan ဖြစ်ပါတယ်။",
                show_alert=True,
            )

            return

        # No cards
        if not game["deck"]:

            await query.answer(
                "❌ ကဒ်ကုန်သွားပါပြီ။",
                show_alert=True,
            )

            return

        # Draw third card
        third_card = game["deck"].pop()

        hand.append(third_card)

        score_value = calculate_score(hand)

        caption = (
            "🃏 <b>တတိယကဒ်</b>\n\n"
            f"👤 <b>{player_name(user)}</b>\n\n"
            f"🔢 အမှတ်: <b>{score_value}</b>"
        )

        if score_value in [8, 9]:

            caption += (
                "\n\n"
                "✨ <b>KOE MEE!</b> ✨"
            )

        try:

            await context.bot.send_photo(
                chat_id=chat.id,
                photo=card_image_url(third_card),
                caption=caption,
                parse_mode="HTML",
            )

        except Exception as e:

            logging.error(
                "Third card image error: %s",
                e,
            )

            await context.bot.send_message(
                chat_id=chat.id,
                text=caption,
                parse_mode="HTML",
            )

        return


# =========================================================
# ERROR HANDLER
# =========================================================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
):

    logging.error(
        "Telegram error: %s",
        context.error,
    )


# =========================================================
# MAIN
# =========================================================

def main():

    if not TOKEN:

        raise RuntimeError(
            "BOT_TOKEN ENV variable မတွေ့ပါ။"
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
        CallbackQueryHandler(
            button_handler
        )
    )

    app.add_error_handler(
        error_handler
    )

    print("🃏 Shan Koe Mee Bot is running...")

    app.run_polling()


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    main()
