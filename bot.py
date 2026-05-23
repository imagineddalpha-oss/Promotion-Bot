import sqlite3
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters
)

# =========================
# CONFIG
# =========================

TOKEN = "8063327999:AAEMTzM80o57ShniGiouu4QvHwWOpTIUVIY"
ADMIN_ID = 8646133090
FORCE_CHANNEL = "https://t.me/free_promotion_botAi"

# =========================
# DATABASE
# =========================

conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_seen TEXT,
    last_seen TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    username TEXT,
    category TEXT,
    link TEXT,
    description TEXT,
    time TEXT
)
""")

conn.commit()

# =========================
# USER REGISTER
# =========================

def register_user(user):

    cursor.execute("SELECT user_id FROM users WHERE user_id=?", (user.id,))
    data = cursor.fetchone()

    now = str(datetime.now())

    if data is None:
        cursor.execute("""
        INSERT INTO users VALUES (?, ?, ?, ?)
        """, (user.id, user.username, now, now))
    else:
        cursor.execute("""
        UPDATE users SET last_seen=? WHERE user_id=?
        """, (now, user.id))

    conn.commit()

# =========================
# KEYBOARDS
# =========================

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👤 Profile", callback_data="profile")],
        [InlineKeyboardButton("📢 Post Promotion", callback_data="post")],
        [InlineKeyboardButton("📊 Stats", callback_data="stats")],
        [InlineKeyboardButton("📢 Feed", callback_data="feed")],
        [InlineKeyboardButton("❌ End Chat", callback_data="end")]
    ])

def back_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back", callback_data="menu")],
        [InlineKeyboardButton("❌ End Chat", callback_data="end")]
    ])

def join_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Join Channel", url=FORCE_CHANNEL)],
        [InlineKeyboardButton("✅ I Joined", callback_data="joined")]
    ])

# =========================
# POST STATES
# =========================

CATEGORY, LINK, DESC = range(3)

# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "⚠️ Please join our official channel first!",
        reply_markup=join_keyboard()
    )

# =========================
# JOIN CONFIRM (NO CHECK)
# =========================

async def joined(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user = update.effective_user
    register_user(user)

    await query.message.edit_text(
        f"""
✅ PROFILE CREATED

👤 Welcome {user.first_name}
🆔 {user.id}
""",
        reply_markup=main_menu()
    )

# =========================
# CALLBACK HANDLER
# =========================

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user = update.effective_user

    # END CHAT
    if query.data == "end":
        await query.message.edit_text("👋 Chat Ended\nType /start to restart")
        return

    # MENU
    if query.data == "menu":
        await query.message.edit_text("🏠 Main Menu", reply_markup=main_menu())

    # PROFILE
    elif query.data == "profile":

        cursor.execute("SELECT * FROM users WHERE user_id=?", (user.id,))
        data = cursor.fetchone()

        text = f"""
👤 PROFILE

🆔 {user.id}
📛 @{user.username}

📅 First: {data[2] if data else 'N/A'}
⏰ Last: {data[3] if data else 'N/A'}
"""

        await query.message.edit_text(text, reply_markup=back_menu())

    # STATS
    elif query.data == "stats":

        cursor.execute("SELECT COUNT(*) FROM users")
        users = cursor.fetchone()[0]

        await query.message.edit_text(
            f"📊 Total Users: {users}",
            reply_markup=back_menu()
        )

    # FEED
    elif query.data == "feed":

        cursor.execute("SELECT username, description FROM posts ORDER BY id DESC LIMIT 5")
        posts = cursor.fetchall()

        text = "📢 FEED\n\n"

        for p in posts:
            text += f"👤 @{p[0]}\n📝 {p[1]}\n\n"

        if not posts:
            text = "📭 No posts yet"

        await query.message.edit_text(text, reply_markup=back_menu())

    # POST START
    elif query.data == "post":

        await query.message.edit_text(
            "📂 Choose Category",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("YouTube", callback_data="cat_youtube")],
                [InlineKeyboardButton("Telegram", callback_data="cat_telegram")],
                [InlineKeyboardButton("Business", callback_data="cat_business")]
            ])
        )

        context.user_data["step"] = "category"

# =========================
# POST FLOW
# =========================

async def post_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    text = update.message.text

    step = context.user_data.get("step")

    if step == "link":
        context.user_data["link"] = text
        context.user_data["step"] = "desc"
        await update.message.reply_text("📝 Send description")

    elif step == "desc":

        category = context.user_data.get("category")
        link = context.user_data.get("link")

        cursor.execute("""
        INSERT INTO posts (user_id, username, category, link, description, time)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (user.id, user.username, category, link, text, str(datetime.now())))

        conn.commit()

        await update.message.reply_text("✅ Post Published!", reply_markup=main_menu())

        # ADMIN NOTIFY
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"""
🚨 NEW POST

👤 @{user.username}
📂 {category}
🔗 {link}
📝 {text}
"""
        )

        context.user_data["step"] = None

# =========================
# CATEGORY SELECT
# =========================

async def category_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    category = query.data

    context.user_data["category"] = category
    context.user_data["step"] = "link"

    await query.message.reply_text("🔗 Send link")

# =========================
# MAIN
# =========================

def main():

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(joined, pattern="joined"))
    app.add_handler(CallbackQueryHandler(category_handler, pattern="cat_"))
    app.add_handler(CallbackQueryHandler(buttons))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, post_flow))

    print("Bot Running...")
    app.run_polling()

if __name__ == "__main__":
    main()
