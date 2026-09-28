import os, sqlite3, random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")
OWNER = int(os.getenv("BOT_OWNER_ID", "0"))
DB = "/data/bot.db"
STICKER_SET = "Playing_Cards"
BET = 100

db = sqlite3.connect(DB, check_same_thread=False)
db.execute("""
CREATE TABLE IF NOT EXISTS coins(
    uid INTEGER PRIMARY KEY,
    username TEXT,
    balance INTEGER DEFAULT 0
)
""")
db.commit()

games = {}
stickers = {}

RANKS = ["A","2","3","4","5","6","7","8","9","10","J","Q","K"]
SUITS = ["♠","♥","♦","♣"]
DECK = [r+s for s in SUITS for r in RANKS]


def get_balance(uid):
    x = db.execute(
        "SELECT balance FROM coins WHERE uid=?", (uid,)
    ).fetchone()
    return x[0] if x else 0


def save_user(uid, username, balance=None):
    old = get_balance(uid)
    if balance is None:
        balance = old
    db.execute("""
        INSERT INTO coins(uid,username,balance)
        VALUES(?,?,?)
        ON CONFLICT(uid) DO UPDATE SET
        username=excluded.username,
        balance=excluded.balance
    """, (uid, username, balance))
    db.commit()


def card_value(card):
    r = card[:-1]
    if r in ["J","Q","K","10"]:
        return 0
    if r == "A":
        return 1
    return int(r)


def score(cards):
    return sum(card_value(x) for x in cards) % 10


def is_shan(cards):
    return len(cards) == 2 and score(cards) in [8, 9]


async def common(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🃏 SHAN KOE MEE\n\n"
        "/game - 🎮 Game စမယ်\n"
        "/balance - 💰 Coin ကြည့်မယ်\n"
        "/balance @username - 👤 သူ့ Coin ကြည့်မယ်\n"
        "/common - 📋 Commands\n\n"
        "👑 OWNER COMMANDS\n"
        "/addcoin @username 1000\n"
        "/delcoin @username 100"
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user(
        update.effective_user.id,
        update.effective_user.username or update.effective_user.full_name
    )
    await update.message.reply_text(
        "🃏 SHAN KOE MEE BOT ONLINE!\n\n"
        "/common - Commands\n"
        "/game - Game စမယ်\n"
        "/balance - Coin ကြည့်မယ်"
    )


async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    save_user(
        user.id,
        user.username or user.full_name
    )

    if context.args:
        target = context.args[0].lstrip("@")
        x = db.execute(
            "SELECT balance FROM coins WHERE username=?",
            (target,)
        ).fetchone()

        await update.message.reply_text(
            f"💰 @{target}: {x[0] if x else 0} Coins"
        )
        return

    await update.message.reply_text(
        f"💰 Your Balance: {get_balance(user.id)} Coins"
    )


async def addcoin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER:
        return

    if len(context.args) < 2:
        await update.message.reply_text(
            "/addcoin @username 1000"
        )
        return

    username = context.args[0].lstrip("@")

    try:
        amount = int(context.args[1])
    except:
        await update.message.reply_text("Amount မှန်အောင်ထည့်ပါ။")
        return

    if amount <= 0:
        await update.message.reply_text("Amount က 0 ထက်ကြီးရမယ်။")
        return

    x = db.execute(
        "SELECT uid,balance FROM coins WHERE username=?",
        (username,)
    ).fetchone()

    if not x:
        await update.message.reply_text(
            "❌ ဒီ User က Bot နဲ့ အရင် /start လုပ်ထားရမယ်။"
        )
        return

    save_user(x[0], username, x[1] + amount)

    await update.message.reply_text(
        f"✅ @{username}\n"
        f"💰 +{amount} Coins\n"
        f"Balance: {x[1] + amount}"
    )


async def delcoin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER:
        return

    if len(context.args) < 2:
        await update.message.reply_text(
            "/delcoin @username 100"
        )
        return

    username = context.args[0].lstrip("@")

    try:
        amount = int(context.args[1])
    except:
        await update.message.reply_text("Amount မှန်အောင်ထည့်ပါ။")
        return

    if amount <= 0:
        await update.message.reply_text("Amount က 0 ထက်ကြီးရမယ်။")
        return

    x = db.execute(
        "SELECT uid,balance FROM coins WHERE username=?",
        (username,)
    ).fetchone()

    if not x:
        await update.message.reply_text("❌ User မတွေ့ပါ။")
        return

    new_balance = max(0, x[1] - amount)

    save_user(x[0], username, new_balance)

    await update.message.reply_text(
        f"✅ @{username}\n"
        f"💰 -{amount} Coins\n"
        f"Balance: {new_balance}"
    )


async def game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        await update.message.reply_text(
            "❌ Game ကို Group ထဲမှာပဲ စလို့ရပါတယ်။"
        )
        return

    gid = update.effective_chat.id

    if gid in games:
        await update.message.reply_text(
            "🎮 Game တစ်ခုရှိပြီးသားပါ။"
        )
        return

    user = update.effective_user

    save_user(
        user.id,
        user.username or user.full_name
    )

    games[gid] = {
        "creator": user.id,
        "players": {}
    }

    kb = [[
        InlineKeyboardButton("➕ JOIN", callback_data="join"),
        InlineKeyboardButton("▶️ START", callback_data="start")
    ]]

    await update.message.reply_text(
        "🃏 SHAN KOE MEE\n\n"
        "💰 Bet: 100 Coins\n"
        "👥 Players: 2–5\n\n"
        "ကစားမယ့်သူ JOIN လုပ်ပါ။",
        reply_markup=InlineKeyboardMarkup(kb)
    )


async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    gid = q.message.chat.id
    game_data = games.get(gid)

    if not game_data:
        return

    uid = q.from_user.id
    username = q.from_user.username or q.from_user.full_name

    save_user(uid, username)

    if q.data == "join":

        if uid in game_data["players"]:
            return await q.answer(
                "သင် JOIN လုပ်ပြီးသားပါ။",
                show_alert=True
            )

        if len(game_data["players"]) >= 5:
            return await q.answer(
                "❌ Player 5 ယောက်ပြည့်ပါပြီ။",
                show_alert=True
            )

        if get_balance(uid) < BET:
            return await q.answer(
                "❌ Coin 100 မရှိပါ။",
                show_alert=True
            )

        game_data["players"][uid] = {
            "username": username,
            "cards": [],
            "done": False
        }

        players = "\n".join(
            "• " + x["username"]
            for x in game_data["players"].values()
        )

        kb = [[
            InlineKeyboardButton("➕ JOIN", callback_data="join"),
            InlineKeyboardButton("▶️ START", callback_data="start")
        ]]

        await q.edit_message_text(
            "🃏 SHAN KOE MEE\n\n"
            "👥 Players:\n" + players +
            "\n\n💰 Bet: 100 Coins",
            reply_markup=InlineKeyboardMarkup(kb)
        )

    elif q.data == "start":

        if uid != game_data["creator"]:
            return await q.answer(
                "❌ Game ဖွင့်သူပဲ START လုပ်နိုင်ပါတယ်။",
                show_alert=True
            )

        if len(game_data["players"]) < 2:
            return await q.answer(
                "❌ အနည်းဆုံး 2 ယောက်လိုပါတယ်။",
                show_alert=True
            )

        for pid in game_data["players"]:
            if get_balance(pid) < BET:
                return await q.answer(
                    "❌ Player တစ်ယောက်မှာ Coin မလုံလောက်ပါ။",
                    show_alert=True
                )

        for pid, player in game_data["players"].items():
            save_user(
                pid,
                player["username"],
                get_balance(pid) - BET
            )

        deck = DECK.copy()
        random.shuffle(deck)

        for pid in game_data["players"]:
            game_data["players"][pid]["cards"] = [
                deck.pop(), deck.pop()
            ]

        await q.edit_message_text(
            "🃏 CARDS DEALT!\n\n"
            "တစ်ယောက်ချင်းစီရဲ့ Card ကို Bot က ပြပါမယ်။"
        )

        for pid, player in game_data["players"].items():

            text = (
                f"👤 {player['username']}\n"
                f"🎴 Card: {player['cards'][0]}, "
                f"{player['cards'][1]}\n"
                f"🔢 Score: {score(player['cards'])}"
            )

            if is_shan(player["cards"]):
                player["done"] = True
                text += "\n\n🔥 SHAN!"

            await q.message.reply_text(text)

            if not player["done"]:
                kb = [[
                    InlineKeyboardButton(
                        "🎴 DRAW",
                        callback_data=f"draw:{pid}"
                    ),
                    InlineKeyboardButton(
                        "✋ PASS",
                        callback_data=f"pass:{pid}"
                    )
                ]]

                await q.message.reply_text(
                    f"👤 {player['username']} ရွေးပါ။",
                    reply_markup=InlineKeyboardMarkup(kb)
                )

        await finish(gid, q)


    elif q.data.startswith("draw:"):

        pid = int(q.data.split(":")[1])

        if pid != uid:
            return await q.answer(
                "❌ ကိုယ့်အလှည့်မဟုတ်ပါ။",
                show_alert=True
            )

        player = game_data["players"].get(uid)

        if not player or player["done"]:
            return

        used = []

        for p in game_data["players"].values():
            used += p["cards"]

        available = [c for c in DECK if c not in used]

        card = random.choice(available)
        player["cards"].append(card)
        player["done"] = True

        await q.message.reply_text(
            f"🎴 {player['username']} Third Card: {card}\n"
            f"🔢 Score: {score(player['cards'])}"
        )

        await finish(gid, q)


    elif q.data.startswith("pass:"):

        pid = int(q.data.split(":")[1])

        if pid != uid:
            return await q.answer(
                "❌ ကိုယ့်အလှည့်မဟုတ်ပါ။",
                show_alert=True
            )

        player = game_data["players"].get(uid)

        if not player:
            return

        player["done"] = True

        await q.message.reply_text(
            f"✋ {player['username']} PASS\n"
            f"🔢 Score: {score(player['cards'])}"
        )

        await finish(gid, q)


async def finish(gid, q):
    g = games.get(gid)

    if not g:
        return

    if not all(
        p["done"]
        for p in g["players"].values()
    ):
        return

    results = []

    for pid, player in g["players"].items():
        results.append((
            score(player["cards"]),
            pid,
            player
        ))

    highest = max(x[0] for x in results)

    winners = [
        x for x in results
        if x[0] == highest
    ]

    pool = len(results) * BET
    prize = pool // len(winners)

    text = "🏆 SHAN KOE MEE RESULT\n\n"

    for s, pid, player in results:
        text += (
            f"👤 {player['username']}\n"
            f"🎴 {', '.join(player['cards'])}\n"
            f"🔢 {s}\n\n"
        )

    text += f"💰 Pool: {pool} Coins\n\n"

    if len(winners) == 1:
        _, pid, player = winners[0]

        save_user(
            pid,
            player["username"],
            get_balance(pid) + pool
        )

        text += (
            f"🏆 WINNER: {player['username']}\n"
            f"💰 +{pool} Coins"
        )

    else:
        names = []

        for _, pid, player in winners:
            save_user(
                pid,
                player["username"],
                get_balance(pid) + prize
            )
            names.append(player["username"])

        text += (
            "🤝 DRAW\n"
            f"🏆 {', '.join(names)}\n"
            f"💰 Each +{prize} Coins"
        )

    await q.message.reply_text(text)

    del games[gid]


async def save_message_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user:
        save_user(
            update.effective_user.id,
            update.effective_user.username
            or update.effective_user.full_name
        )


async def post_init(app):
    await app.bot.set_my_commands([
        ("start", "Bot စမယ်"),
        ("common", "Commands ကြည့်မယ်"),
        ("game", "Shan Koe Mee ဆော့မယ်"),
        ("balance", "Coin ကြည့်မယ်"),
        ("addcoin", "Owner Coin ထည့်မယ်"),
        ("delcoin", "Owner Coin ဖြုတ်မယ်")
    ])

    try:
        pack = await app.bot.get_sticker_set(STICKER_SET)

        for i, sticker in enumerate(pack.stickers[:52]):
            stickers[DECK[i]] = sticker.file_id

        print("Card stickers loaded:", len(stickers))

    except Exception as e:
        print("Sticker error:", e)


def main():
    app = (
        Application.builder()
        .token(TOKEN)
        .post_init(post_init)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("common", common))
    app.add_handler(CommandHandler("game", game))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("addcoin", addcoin))
    app.add_handler(CommandHandler("delcoin", delcoin))

    app.add_handler(
        CallbackQueryHandler(callback)
    )

    app.add_handler(
        MessageHandler(
            filters.ALL,
            save_message_user
        )
    )

    app.run_polling()


if __name__ == "__main__":
    main()
