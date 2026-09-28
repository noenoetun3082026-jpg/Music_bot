import os, sqlite3, random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")
OWNER = int(os.getenv("BOT_OWNER_ID", "0"))
DB = "/data/bot.db"
BET = 100
STICKER_SET = "Playing_Cards"

db = sqlite3.connect(DB, check_same_thread=False)
db.execute("""CREATE TABLE IF NOT EXISTS coins(
uid INTEGER PRIMARY KEY,
username TEXT,
balance INTEGER DEFAULT 0)""")
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
    if balance is None:
        balance = get_balance(uid)

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

    if r in ["10","J","Q","K"]:
        return 0

    if r == "A":
        return 1

    return int(r)


def score(cards):
    return sum(card_value(c) for c in cards) % 10


def shan(cards):
    return len(cards) == 2 and score(cards) in [8,9]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user

    save_user(
        u.id,
        u.username or u.full_name
    )

    await update.message.reply_text(
        "🃏 SHAN KOE MEE BOT ONLINE!\n\n"
        "/common - 📋 Commands\n"
        "/game - 🎮 Game စမယ်\n"
        "/balance - 💰 Coin ကြည့်မယ်"
    )


async def common(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🃏 SHAN KOE MEE\n\n"
        "/game - 🎮 Game စမယ်\n"
        "/balance - 💰 ကိုယ့် Coin ကြည့်မယ်\n"
        "/balance @username - 👤 သူ့ Coin ကြည့်မယ်\n"
        "/common - 📋 Commands\n\n"
        "👑 OWNER\n"
        "/addcoin @username 1000\n"
        "/delcoin @username 100"
    )


async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user

    save_user(
        u.id,
        u.username or u.full_name
    )

    if context.args:
        username = context.args[0].lstrip("@")

        x = db.execute(
            "SELECT balance FROM coins WHERE username=?",
            (username,)
        ).fetchone()

        await update.message.reply_text(
            f"💰 @{username}: {x[0] if x else 0} Coins"
        )
        return

    await update.message.reply_text(
        f"💰 Your Balance: {get_balance(u.id)} Coins"
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
        await update.message.reply_text("❌ Amount မှားနေပါတယ်။")
        return

    if amount <= 0:
        await update.message.reply_text(
            "❌ Amount က 0 ထက်ကြီးရမယ်။"
        )
        return

    x = db.execute(
        "SELECT uid,balance FROM coins WHERE username=?",
        (username,)
    ).fetchone()

    if not x:
        await update.message.reply_text(
            "❌ User က Bot နဲ့ /start အရင်လုပ်ထားရမယ်။"
        )
        return

    new_balance = x[1] + amount

    save_user(
        x[0],
        username,
        new_balance
    )

    await update.message.reply_text(
        f"✅ @{username}\n"
        f"💰 +{amount} Coins\n"
        f"Balance: {new_balance}"
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
        await update.message.reply_text(
            "❌ Amount မှားနေပါတယ်။"
        )
        return

    if amount <= 0:
        await update.message.reply_text(
            "❌ Amount က 0 ထက်ကြီးရမယ်။"
        )
        return

    x = db.execute(
        "SELECT uid,balance FROM coins WHERE username=?",
        (username,)
    ).fetchone()

    if not x:
        await update.message.reply_text(
            "❌ User မတွေ့ပါ။"
        )
        return

    new_balance = max(0, x[1] - amount)

    save_user(
        x[0],
        username,
        new_balance
    )

    await update.message.reply_text(
        f"✅ @{username}\n"
        f"💰 -{amount} Coins\n"
        f"Balance: {new_balance}"
    )


async def game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        await update.message.reply_text(
            "❌ Game ကို Group ထဲမှာပဲ ကစားလို့ရပါတယ်။"
        )
        return

    gid = update.effective_chat.id

    if gid in games:
        await update.message.reply_text(
            "🎮 Game ရှိပြီးသားပါ။"
        )
        return

    u = update.effective_user

    save_user(
        u.id,
        u.username or u.full_name
    )

    games[gid] = {
        "creator": u.id,
        "players": {}
    }

    kb = [[
        InlineKeyboardButton(
            "➕ JOIN",
            callback_data="join"
        ),
        InlineKeyboardButton(
            "▶️ START",
            callback_data="start"
        )
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
    gid = q.message.chat.id
    g = games.get(gid)

    if not g:
        return await q.answer(
            "❌ Game မရှိတော့ပါ။",
            show_alert=True
        )

    uid = q.from_user.id
    username = q.from_user.username or q.from_user.full_name

    save_user(uid, username)

    if q.data == "join":

        if uid in g["players"]:
            return await q.answer(
                "သင် JOIN လုပ်ပြီးသားပါ။",
                show_alert=True
            )

        if len(g["players"]) >= 5:
            return await q.answer(
                "❌ Player 5 ယောက်ပြည့်ပါပြီ။",
                show_alert=True
            )

        money = get_balance(uid)

        if money < BET:
            return await q.answer(
                f"❌ Coin မလုံလောက်ပါ။\n"
                f"လိုအပ်သည်: {BET}\n"
                f"လက်ရှိ: {money}",
                show_alert=True
            )

        g["players"][uid] = {
            "username": username,
            "cards": [],
            "done": False
        }

        players = "\n".join(
            "• " + p["username"]
            for p in g["players"].values()
        )

        kb = [[
            InlineKeyboardButton(
                "➕ JOIN",
                callback_data="join"
            ),
            InlineKeyboardButton(
                "▶️ START",
                callback_data="start"
            )
        ]]

        await q.answer("✅ JOIN အောင်မြင်ပါတယ်။")

        await q.edit_message_text(
            "🃏 SHAN KOE MEE\n\n"
            "👥 Players:\n"
            + players +
            "\n\n💰 Bet: 100 Coins",
            reply_markup=InlineKeyboardMarkup(kb)
        )

        return

    if q.data == "start":

        if uid != g["creator"]:
            return await q.answer(
                "❌ Game ဖွင့်သူပဲ START လုပ်နိုင်ပါတယ်။",
                show_alert=True
            )

        if len(g["players"]) < 2:
            return await q.answer(
                "❌ အနည်းဆုံး 2 ယောက်လိုပါတယ်။",
                show_alert=True
            )

        for pid in g["players"]:
            if get_balance(pid) < BET:
                return await q.answer(
                    "❌ Player တစ်ယောက်မှာ Coin မလုံလောက်ပါ။",
                    show_alert=True
                )

        for pid, p in g["players"].items():
            save_user(
                pid,
                p["username"],
                get_balance(pid) - BET
            )

        deck = DECK.copy()
        random.shuffle(deck)

        for pid in g["players"]:
            g["players"][pid]["cards"] = [
                deck.pop(),
                deck.pop()
            ]

        await q.answer("🃏 Cards dealt!")

        await q.edit_message_text(
            "🃏 CARDS DEALT!\n\n"
            "တစ်ယောက်ချင်းစီ DRAW / PASS လုပ်ပါ။"
        )

        for pid, p in g["players"].items():

            text = (
                f"👤 {p['username']}\n"
                f"🎴 {', '.join(p['cards'])}\n"
                f"🔢 Score: {score(p['cards'])}"
            )

            if shan(p["cards"]):
                p["done"] = True
                text += "\n\n🔥 SHAN!"

            await q.message.reply_text(text)

            if not p["done"]:

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
                    "ရွေးပါ 👇",
                    reply_markup=InlineKeyboardMarkup(kb)
                )

        await finish(gid, q)
        return

    if q.data.startswith("draw:"):

        pid = int(q.data.split(":")[1])

        if uid != pid:
            return await q.answer(
                "❌ ကိုယ့်အလှည့်မဟုတ်ပါ။",
                show_alert=True
            )

        p = g["players"].get(uid)

        if not p or p["done"]:
            return

        used = []

        for x in g["players"].values():
            used += x["cards"]

        available = [
            c for c in DECK
            if c not in used
        ]

        card = random.choice(available)

        p["cards"].append(card)
        p["done"] = True

        await q.answer("🎴 Third Card ရပြီ!")

        await q.message.reply_text(
            f"👤 {p['username']}\n"
            f"🎴 Third Card: {card}\n"
            f"🔢 Score: {score(p['cards'])}"
        )

        await finish(gid, q)
        return

    if q.data.startswith("pass:"):

        pid = int(q.data.split(":")[1])

        if uid != pid:
            return await q.answer(
                "❌ ကိုယ့်အလှည့်မဟုတ်ပါ။",
                show_alert=True
            )

        p = g["players"].get(uid)

        if not p:
            return

        p["done"] = True

        await q.answer("✋ PASS")

        await q.message.reply_text(
            f"👤 {p['username']} PASS\n"
            f"🔢 Score: {score(p['cards'])}"
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

    for pid, p in g["players"].items():
        results.append((
            score(p["cards"]),
            pid,
            p
        ))

    highest = max(x[0] for x in results)

    winners = [
        x for x in results
        if x[0] == highest
    ]

    pool = len(results) * BET
    prize = pool // len(winners)

    text = "🏆 SHAN KOE MEE RESULT\n\n"

    for s, pid, p in results:
        text += (
            f"👤 {p['username']}\n"
            f"🎴 {', '.join(p['cards'])}\n"
            f"🔢 {s}\n\n"
        )

    text += f"💰 Pool: {pool} Coins\n\n"

    for _, pid, p in winners:
        save_user(
            pid,
            p["username"],
            get_balance(pid) + prize
        )

    if len(winners) == 1:
        p = winners[0][2]

        text += (
            f"🏆 WINNER: {p['username']}\n"
            f"💰 +{prize} Coins"
        )
    else:
        names = ", ".join(
            x[2]["username"]
            for x in winners
        )

        text += (
            f"🤝 DRAW\n"
            f"🏆 {names}\n"
            f"💰 Each +{prize} Coins"
        )

    await q.message.reply_text(text)

    del games[gid]


async def save_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user:
        u = update.effective_user

        save_user(
            u.id,
            u.username or u.full_name
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

        print("Cards loaded:", len(stickers))

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
            save_user_message
        )
    )

    app.run_polling()


if __name__ == "__main__":
    main()
