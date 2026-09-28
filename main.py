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

# =========================
# CONFIG
# =========================

TOKEN = os.getenv("BOT_TOKEN")

STICKER_SET_NAME = "Playing_Cards"

MAX_PLAYERS = 5
MIN_PLAYERS = 2

games = {}

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# =========================
# CARD DATA
# =========================

SUITS = [
    "♠",
    "♥",
    "♦",
    "♣",
]

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


# =========================
# CARD FUNCTIONS
# =========================

def create_deck():
    deck = []

    for suit in SUITS:
        for rank in RANKS:
            deck.append(rank + suit)

    random.shuffle(deck)

    return deck


def card_value(card):
    rank = card[:-1]

    if rank == "A":
        return 1

    if rank in ["10", "J", "Q", "K"]:
        return 0

    return int(rank)


def calculate_score(hand):
    total = 0

    for card in hand:
        total += card_value(card)

    return total % 10


def is_auto_shan(hand):
    if len(hand) != 2:
        return False

    return calculate_score(hand) in [8, 9]


def player_name(user):
    if user.username:
        return "@" + user.username

    if user.first_name:
        return user.first_name

    return "Player"


# =========================
# STICKER FUNCTIONS
# =========================

async def load_stickers(bot):

    sticker_set = await bot.get_sticker_set(
        name=STICKER_SET_NAME
    )

    stickers = sticker_set.stickers

    if len(stickers) < 52:
        raise RuntimeError(
            f"{STICKER_SET_NAME} မှာ "
            f"{len(stickers)} ချပ်ပဲရှိပါတယ်။ "
            f"52 ချပ်လိုပါတယ်။"
        )

    return stickers


async def create_sticker_map(bot):

    stickers = await load_stickers(bot)

    cards = []

    for suit in SUITS:
        for rank in RANKS:
            cards.append(rank + suit)

    sticker_map = {}

    # ပထမ 52 ချပ်ကို card 52 ချပ်အဖြစ် အသုံးပြု
    for index in range(52):
        sticker_map[cards[index]] = (
            stickers[index].file_id
        )

    return sticker_map


async def send_card(
    bot,
    chat_id,
    card,
    sticker_map
):

    sticker_id = sticker_map.get(card)

    if not sticker_id:

        await bot.send_message(
            chat_id=chat_id,
            text=f"❌ {card} sticker မတွေ့ပါ။"
        )

        return

    await bot.send_sticker(
        chat_id=chat_id,
        sticker=sticker_id
    )


# =========================
# KEYBOARDS
# =========================

def lobby_keyboard():

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🎴 ဝင်ကစားမယ်",
                callback_data="join"
            )
        ],
        [
            InlineKeyboardButton(
                "▶️ ဂိမ်းစမယ်",
                callback_data="start"
            )
        ],
        [
            InlineKeyboardButton(
                "❌ အခန်းပိတ်မယ်",
                callback_data="cancel"
            )
        ],
    ])


def play_keyboard():

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🃏 ယူမယ်",
                callback_data="draw"
            ),
            InlineKeyboardButton(
                "❌ မယူဘူး",
                callback_data="pass"
            ),
        ],
    ])


def result_keyboard():

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🔄 Game အသစ်",
                callback_data="new_game"
            )
        ],
    ])


# =========================
# LOBBY
# =========================

def lobby_text(game):

    text = (
        "🃏 <b>SHAN KOE MEE</b>\n"
        "━━━━━━━━━━━━━━\n\n"
        f"👑 ဖွင့်သူ : "
        f"<b>{game['creator_name']}</b>\n"
        f"👥 Player : "
        f"<b>{len(game['players'])}/{MAX_PLAYERS}</b>\n\n"
    )

    for index, user in enumerate(
        game["players"],
        start=1
    ):

        text += (
            f"{index}. "
            f"{player_name(user)}\n"
        )

    text += (
        "\n━━━━━━━━━━━━━━\n"
        "🎴 ဝင်ကစားလိုသူ Button နှိပ်ပါ။"
    )

    return text


# =========================
# /START
# =========================

async def start(update, context):

    await update.message.reply_text(
        "🃏 <b>SHAN KOE MEE BOT</b>\n\n"
        "🎮 /game — Game ဖွင့်ရန်\n"
        "ℹ️ /help — အသုံးပြုနည်း\n"
        "🧪 /testcards — Sticker စစ်ရန်",
        parse_mode="HTML"
    )


# =========================
# /HELP
# =========================

async def help_command(update, context):

    await update.message.reply_text(
        "🃏 <b>SHAN KOE MEE</b>\n"
        "━━━━━━━━━━━━━━\n\n"
        "🎮 /game\n"
        "Game အခန်းဖွင့်ရန်\n\n"
        "👥 Player အများဆုံး 5 ယောက်\n"
        "👤 အနည်းဆုံး 2 ယောက်\n\n"
        "🎴 Player တစ်ယောက်ကို "
        "2 ကဒ်ဝေမယ်\n\n"
        "🃏 လိုရင် တတိယကဒ်ယူမယ်\n"
        "❌ မလိုရင် မယူဘူးကိုရွေးမယ်\n\n"
        "✨ 8 / 9 မှတ် = Auto Shan\n\n"
        "🅰️ A = 1\n"
        "2–9 = မူရင်းတန်ဖိုး\n"
        "10/J/Q/K = 0\n\n"
        "🏆 အားလုံးဆုံးဖြတ်ပြီးရင် "
        "Result ထွက်ပါမယ်။",
        parse_mode="HTML"
    )


# =========================
# /TESTCARDS
# =========================

async def test_cards(update, context):

    try:

        stickers = await load_stickers(
            context.bot
        )

    except Exception as error:

        await update.message.reply_text(
            "❌ Sticker set ဖတ်မရပါ။\n\n"
            f"Error: {error}"
        )

        return

    await update.message.reply_text(
        f"🃏 <b>{STICKER_SET_NAME}</b>\n\n"
        f"Sticker အရေအတွက် : "
        f"<b>{len(stickers)}</b>\n\n"
        "ပထမ 5 ချပ် စမ်းပြပါမယ်။",
        parse_mode="HTML"
    )

    for sticker in stickers[:5]:

        await context.bot.send_sticker(
            chat_id=update.effective_chat.id,
            sticker=sticker.file_id
        )


# =========================
# /GAME
# =========================

async def game_command(update, context):

    chat = update.effective_chat
    user = update.effective_user

    if chat.type not in [
        "group",
        "supergroup"
    ]:

        await update.message.reply_text(
            "❌ Group ထဲမှာပဲ /game သုံးပါ။"
        )

        return

    if chat.id in games:

        await update.message.reply_text(
            "⚠️ ဒီ Group မှာ "
            "Game ရှိပြီးသားပါ။"
        )

        return

    try:

        sticker_map = await create_sticker_map(
            context.bot
        )

    except Exception as error:

        await update.message.reply_text(
            "❌ Playing_Cards sticker set "
            "မရပါ။\n\n"
            f"Error: {error}"
        )

        return

    games[chat.id] = {

        "creator_id": user.id,

        "creator_name": player_name(user),

        "players": [user],

        "deck": [],

        "hands": {},

        "scores": {},

        "passed": set(),

        "sticker_map": sticker_map,

        "started": False,

        "finished": False,
    }

    game = games[chat.id]

    await update.message.reply_text(
        lobby_text(game),
        reply_markup=lobby_keyboard(),
        parse_mode="HTML"
    )


# =========================
# CHECK ALL FINISHED
# =========================

def all_players_finished(game):

    for player in game["players"]:

        hand = game["hands"].get(
            player.id,
            []
        )

        # Auto Shan
        if is_auto_shan(hand):
            continue

        # Third card
        if len(hand) >= 3:
            continue

        # Player selected No
        if player.id in game["passed"]:
            continue

        return False

    return True


# =========================
# FINISH GAME
# =========================

async def finish_game(
    bot,
    chat_id,
    game
):

    if game["finished"]:
        return

    game["finished"] = True

    results = []

    for player in game["players"]:

        hand = game["hands"].get(
            player.id,
            []
        )

        score = calculate_score(hand)

        game["scores"][player.id] = score

        results.append({
            "user": player,
            "score": score,
            "hand": hand,
        })

    # Score အမြင့်ဆုံးကနေ အနိမ့်ဆုံး
    results.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    text = (
        "🏆 <b>SHAN KOE MEE RESULT</b>\n"
        "━━━━━━━━━━━━━━\n\n"
    )

    medals = [
        "🥇",
        "🥈",
        "🥉",
    ]

    for index, result in enumerate(results):

        user = result["user"]
        score = result["score"]

        if index < 3:
            medal = medals[index]
        else:
            medal = "🎴"

        text += (
            f"{medal} "
            f"<b>{player_name(user)}</b>"
            f" — <b>{score}</b> မှတ်\n"
        )

    text += (
        "\n━━━━━━━━━━━━━━\n"
        "🎉 <b>Game ပြီးပါပြီ။</b>"
    )

    await bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=result_keyboard(),
        parse_mode="HTML"
    )


# =========================
# BUTTON HANDLER
# =========================

async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    chat = query.message.chat
    user = query.from_user

    game = games.get(chat.id)

    if not game:

        await query.answer(
            "❌ Game မရှိတော့ပါ။",
            show_alert=True
        )

        return

    # =====================
    # JOIN
    # =====================

    if query.data == "join":

        if game["started"]:

            await query.answer(
                "❌ Game စပြီးပါပြီ။",
                show_alert=True
            )

            return

        if any(
            p.id == user.id
            for p in game["players"]
        ):

            await query.answer(
                "✅ ဝင်ထားပြီးသားပါ။",
                show_alert=True
            )

            return

        if len(game["players"]) >= MAX_PLAYERS:

            await query.answer(
                "❌ Player 5 ယောက်ပြည့်ပါပြီ။",
                show_alert=True
            )

            return

        game["players"].append(user)

        await query.edit_message_text(
            lobby_text(game),
            reply_markup=lobby_keyboard(),
            parse_mode="HTML"
        )

        await query.answer(
            "🎴 Game ထဲဝင်ပြီးပါပြီ။"
        )

        return

    # =====================
    # START
    # =====================

    if query.data == "start":

        if user.id != game["creator_id"]:

            await query.answer(
                "❌ Game ဖွင့်သူပဲ "
                "စနိုင်ပါတယ်။",
                show_alert=True
            )

            return

        if game["started"]:

            await query.answer(
                "⚠️ Game စပြီးသားပါ။",
                show_alert=True
            )

            return

        if len(game["players"]) < MIN_PLAYERS:

            await query.answer(
                "❌ အနည်းဆုံး Player "
                "2 ယောက်လိုပါတယ်။",
                show_alert=True
            )

            return

        game["started"] = True
        game["finished"] = False

        game["deck"] = create_deck()

        game["hands"] = {}

        game["scores"] = {}

        game["passed"] = set()

        await query.edit_message_text(
            "🃏 <b>SHAN KOE MEE</b>\n"
            "━━━━━━━━━━━━━━\n\n"
            "🎴 ကဒ်များ ဝေနေပါတယ်...\n"
            "⏳ ခဏစောင့်ပါ။",
            parse_mode="HTML"
        )

        # =================
        # DEAL TWO CARDS
        # =================

        for player in game["players"]:

            hand = [
                game["deck"].pop(),
                game["deck"].pop()
            ]

            game["hands"][player.id] = hand

            score = calculate_score(hand)

            game["scores"][player.id] = score

            # Card 1
            await send_card(
                context.bot,
                chat.id,
                hand[0],
                game["sticker_map"]
            )

            # Card 2
            await send_card(
                context.bot,
                chat.id,
                hand[1],
                game["sticker_map"]
            )

            # =================
            # AUTO SHAN
            # =================

            if is_auto_shan(hand):

                await context.bot.send_message(
                    chat_id=chat.id,
                    text=(
                        "✨ <b>AUTO SHAN!</b> ✨\n\n"
                        f"👤 {player_name(player)}\n"
                        f"🔢 အမှတ် : "
                        f"<b>{score}</b>\n\n"
                        "🃏 တတိယကဒ်မလိုပါ။"
                    ),
                    parse_mode="HTML"
                )

            else:

                await context.bot.send_message(
                    chat_id=chat.id,
                    text=(
                        f"👤 <b>"
                        f"{player_name(player)}"
                        f"</b>\n\n"
                        f"🔢 လက်ရှိအမှတ် : "
                        f"<b>{score}</b>\n\n"
                        "🃏 တတိယကဒ်လိုရင် "
                        "ယူမယ်ကိုနှိပ်ပါ။\n"
                        "❌ မလိုရင် မယူဘူးကိုနှိပ်ပါ။"
                    ),
                    reply_markup=play_keyboard(),
                    parse_mode="HTML"
                )

        await context.bot.send_message(
            chat_id=chat.id,
            text=(
                "🎴 <b>ကဒ်ဝေပြီးပါပြီ။</b>\n\n"
                "🃏 တတိယကဒ်လိုရင် "
                "「ယူမယ်」\n"
                "❌ မလိုရင် "
                "「မယူဘူး」 ကိုနှိပ်ပါ။"
            ),
            parse_mode="HTML"
        )

        return

    # =====================
    # DRAW
    # =====================

    if query.data == "draw":

        if not game["started"]:

            await query.answer(
                "❌ Game မစသေးပါ။",
                show_alert=True
            )

            return

        if game["finished"]:

            await query.answer(
                "❌ Game ပြီးပါပြီ။",
                show_alert=True
            )

            return

        if user.id not in game["hands"]:

            await query.answer(
                "❌ ဒီ Game မှာ မပါပါ။",
                show_alert=True
            )

            return

        hand = game["hands"][user.id]

        if len(hand) >= 3:

            await query.answer(
                "⚠️ တတိယကဒ် ရပြီးသားပါ။",
                show_alert=True
            )

            return

        if is_auto_shan(hand):

            await query.answer(
                "✨ 8/9 ဖြစ်ပြီးသားမို့ "
                "Auto Shan ပါ။",
                show_alert=True
            )

            return

        if user.id in game["passed"]:

            await query.answer(
                "❌ မယူဘူးရွေးပြီးသားပါ။",
                show_alert=True
            )

            return

        if not game["deck"]:

            await query.answer(
                "❌ Deck ကဒ်ကုန်သွားပါပြီ။",
                show_alert=True
            )

            return

        # Third card
        third_card = game["deck"].pop()

        hand.append(third_card)

        score = calculate_score(hand)

        game["scores"][user.id] = score

        await send_card(
            context.bot,
            chat.id,
            third_card,
            game["sticker_map"]
        )

        if score in [8, 9]:

            text = (
                "✨ <b>KOE MEE!</b> ✨\n\n"
                f"👤 {player_name(user)}\n"
                f"🔢 အမှတ် : "
                f"<b>{score}</b>"
            )

        else:

            text = (
                "🃏 <b>တတိယကဒ် ရပါပြီ</b>\n\n"
                f"👤 {player_name(user)}\n"
                f"🔢 အမှတ် : "
                f"<b>{score}</b>"
            )

        # Button ပျောက်အောင်
        try:
            await query.edit_message_reply_markup(
                reply_markup=None
            )
        except Exception:
            pass

        await context.bot.send_message(
            chat_id=chat.id,
            text=text,
            parse_mode="HTML"
        )

        if all_players_finished(game):

            await finish_game(
                context.bot,
                chat.id,
                game
            )

        return

    # =====================
    # PASS
    # =====================

    if query.data == "pass":

        if not game["started"]:

            await query.answer(
                "❌ Game မစသေးပါ။",
                show_alert=True
            )

            return

        if game["finished"]:

            await query.answer(
                "❌ Game ပြီးပါပြီ။",
                show_alert=True
            )

            return

        if user.id not in game["hands"]:

            await query.answer(
                "❌ ဒီ Game မှာ မပါပါ။",
                show_alert=True
            )

            return

        hand = game["hands"][user.id]

        if len(hand) >= 3:

            await query.answer(
                "⚠️ တတိယကဒ် ရပြီးသားပါ။",
                show_alert=True
            )

            return

        if is_auto_shan(hand):

            await query.answer(
                "✨ Auto Shan ဖြစ်ပြီးသားပါ။",
                show_alert=True
            )

            return

        if user.id in game["passed"]:

            await query.answer(
                "❌ မယူဘူး ရွေးပြီးသားပါ။",
                show_alert=True
            )

            return

        # Player မယူတော့
        game["passed"].add(user.id)

        score = calculate_score(hand)

        game["scores"][user.id] = score

        try:
            await query.edit_message_reply_markup(
                reply_markup=None
            )
        except Exception:
            pass

        await context.bot.send_message(
            chat_id=chat.id,
            text=(
                "❌ <b>တတိယကဒ် မယူတော့ပါ</b>\n\n"
                f"👤 <b>{player_name(user)}</b>\n"
                f"🔢 အမှတ် : "
                f"<b>{score}</b>"
            ),
            parse_mode="HTML"
        )

        if all_players_finished(game):

            await finish_game(
                context.bot,
                chat.id,
                game
            )

        return

    # =====================
    # CANCEL
    # =====================

    if query.data == "cancel":

        if user.id != game["creator_id"]:

            await query.answer(
                "❌ Game ဖွင့်သူပဲ "
                "ပိတ်နိုင်ပါတယ်။",
                show_alert=True
            )

            return

        del games[chat.id]

        await query.edit_message_text(
            "❌ <b>Game အခန်း "
            "ပိတ်လိုက်ပါပြီ။</b>",
            parse_mode="HTML"
        )

        return

    # =====================
    # NEW GAME
    # =====================

    if query.data == "new_game":

        del games[chat.id]

        await query.edit_message_text(
            "🔄 <b>Game အသစ်ဖွင့်နိုင်ပါပြီ။</b>\n\n"
            "/game ကိုနှိပ်ပြီး "
            "အခန်းအသစ်ဖွင့်ပါ။",
            parse_mode="HTML"
        )

        return


# =========================
# ERROR HANDLER
# =========================

async def error_handler(
    update,
    context
):

    logging.error(
        "Bot error: %s",
        context.error
    )


# =========================
# MAIN
# =========================

def main():

    if not TOKEN:

        raise RuntimeError(
            "BOT_TOKEN ENV မတွေ့ပါ။"
        )

    app = (
        Application
    
