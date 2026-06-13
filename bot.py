import sqlite3
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes
)

TOKEN = "8992820380:AAEJpDPg-R5SXoOu3ywkCZfQC9RZejFwLIE"
ADMIN_ID = 7507254732
CHANNEL_USERNAME = "@NitroVPN_Official_Org"

# ---------------- DATABASE ----------------

db = sqlite3.connect("bot.db", check_same_thread=False)
cur = db.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY,
    inviter INTEGER DEFAULT 0,
    referrals INTEGER DEFAULT 0,
    texts_received INTEGER DEFAULT 0
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS texts(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT
)
""")

db.commit()

# ---------------- HELPERS ----------------

async def check_join(bot, user_id):
    try:
        member = await bot.get_chat_member(
            CHANNEL_USERNAME,
            user_id
        )

        return member.status in [
            "member",
            "administrator",
            "creator"
        ]
    except:
        return False

def get_user(user_id):
    cur.execute(
        "SELECT * FROM users WHERE user_id=?",
        (user_id,)
    )
    return cur.fetchone()

# ---------------- START ----------------

async def start(update: Update,
                context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    inviter = 0

    if context.args:
        try:
            inviter = int(context.args[0])
        except:
            inviter = 0

    user = get_user(user_id)

    if not user:

        cur.execute(
            """
            INSERT INTO users
            (user_id, inviter, referrals, texts_received)
            VALUES (?, ?, 0, 0)
            """,
            (user_id, inviter)
        )

        if inviter and inviter != user_id:
            cur.execute(
                """
                UPDATE users
                SET referrals = referrals + 1
                WHERE user_id=?
                """,
                (inviter,)
            )

        db.commit()

    joined = await check_join(
        context.bot,
        user_id
    )

    if not joined:
        await update.message.reply_text(
            f"ابتدا عضو کانال {CHANNEL_USERNAME} شوید."
        )
        return

    await update.message.reply_text(
        "خوش آمدید.\n\n"
        "/text : دریافت کانفیگ\n"
        "/myrefs : تعداد زیرمجموعه\n"
        "/link : دریافت لینک دعوت"
    )

# ---------------- REF LINK ----------------

async def link(update, context):

    me = await context.bot.get_me()

    user_id = update.effective_user.id

    await update.message.reply_text(
        f"https://t.me/{me.username}?start={user_id}"
    )

# ---------------- MY REFS ----------------

async def myrefs(update, context):

    user = get_user(
        update.effective_user.id
    )

    await update.message.reply_text(
        f"تعداد زیرمجموعه‌ها: {user[2]}"
    )

# ---------------- ADD TEXT ----------------

async def addtext(update, context):

    if update.effective_user.id != ADMIN_ID:
        return

    text = " ".join(context.args)

    if not text:
        await update.message.reply_text(
            "کانفیگی وارد نشده."
        )
        return

    cur.execute(
        "INSERT INTO texts(content) VALUES(?)",
        (text,)
    )

    db.commit()

    await update.message.reply_text(
        "کانفیگ ذخیره شد."
    )

# ---------------- GET TEXT ----------------

async def gettext(update, context):

    user_id = update.effective_user.id

    joined = await check_join(
        context.bot,
        user_id
    )

    if not joined:
        await update.message.reply_text(
            "ابتدا عضو کانال شوید."
        )
        return

    user = get_user(user_id)

    referrals = user[2]
    received = user[3]

    if received == 0:
        allowed = True
    else:
        allowed = referrals >= received * 2

    if not allowed:
        need = (received * 2) - referrals

        await update.message.reply_text(
            f"برای دریافت کانفیگ بعدی "
            f"{need} زیرمجموعه دیگر لازم دارید."
        )
        return
    cur.execute(
        "SELECT id, content FROM texts ORDER BY id LIMIT 1"
    )

    row = cur.fetchone()

    if not row:
        await update.message.reply_text(
            "کانفیگی موجود نیست."
        )
        return

    text_id = row[0]
    content = row[1]

    await update.message.reply_text(content)

    cur.execute(
        "DELETE FROM texts WHERE id=?",
        (text_id,)
    )

    cur.execute(
        """
        UPDATE users
        SET texts_received = texts_received + 1
        WHERE user_id=?
        """,
        (user_id,)
    )

    db.commit()

# ---------------- BROADCAST ----------------

async def broadcast(update, context):

    if update.effective_user.id != ADMIN_ID:
        return

    message = " ".join(context.args)

    if not message:
        return

    cur.execute(
        "SELECT user_id FROM users"
    )

    users = cur.fetchall()

    sent = 0

    for user in users:
        try:
            await context.bot.send_message(
                user[0],
                message
            )
            sent += 1
        except:
            pass

    await update.message.reply_text(
        f"{sent} پیام ارسال شد."
    )

# ---------------- MAIN ----------------

app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("text", gettext))
app.add_handler(CommandHandler("link", link))
app.add_handler(CommandHandler("myrefs", myrefs))
app.add_handler(CommandHandler("addtext", addtext))
app.add_handler(CommandHandler("broadcast", broadcast))

print("Bot Started...")
app.run_polling()
