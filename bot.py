import sqlite3
from datetime import datetime, timedelta

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# ==================================================
# CONFIG
# ==================================================

TOKEN = "8063327999:AAEMTzM80o57ShniGiouu4QvHwWOpTIUVIY"
ADMIN_ID = 8646133090
FORCE_CHANNEL = "https://t.me/free_promotion_botAi"

# ==================================================
# DATABASE
# ==================================================

conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

# USERS
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_seen TEXT,
    last_seen TEXT,
    credits INTEGER DEFAULT 0,
    banned INTEGER DEFAULT 0
)
""")

# POSTS
cursor.execute("""
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    username TEXT,
    category TEXT,
    file_id TEXT,
    file_type TEXT,
    link TEXT,
    description TEXT,
    likes INTEGER DEFAULT 0,
    dislikes INTEGER DEFAULT 0,
    views INTEGER DEFAULT 0,
    approved INTEGER DEFAULT 0,
    featured INTEGER DEFAULT 0,
    time TEXT
)
""")

# USER ACTIONS
cursor.execute("""
CREATE TABLE IF NOT EXISTS post_actions (
    user_id INTEGER,
    post_id INTEGER,
    action TEXT
)
""")

conn.commit()

# ==================================================
# TEMP MEMORY
# ==================================================

user_states = {}

# ==================================================
# USER REGISTER
# ==================================================

def register_user(user):

    cursor.execute(
        "SELECT user_id FROM users WHERE user_id=?",
        (user.id,)
    )

    data = cursor.fetchone()

    now = str(datetime.now())

    if data is None:

        cursor.execute("""
        INSERT INTO users (
            user_id,
            username,
            first_seen,
            last_seen
        )
        VALUES (?, ?, ?, ?)
        """, (
            user.id,
            user.username,
            now,
            now
        ))

    else:

        cursor.execute("""
        UPDATE users
        SET last_seen=?
        WHERE user_id=?
        """, (
            now,
            user.id
        ))

    conn.commit()

# ==================================================
# KEYBOARDS
# ==================================================

def join_keyboard():

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "📢 Join Channel",
                url=FORCE_CHANNEL
            )
        ],
        [
            InlineKeyboardButton(
                "✅ I Joined",
                callback_data="joined"
            )
        ]
    ])

def main_menu():

    return InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                "👤 Profile",
                callback_data="profile"
            )
        ],

        [
            InlineKeyboardButton(
                "📢 Create Post",
                callback_data="create_post"
            )
        ],

        [
            InlineKeyboardButton(
                "📰 Feed",
                callback_data="feed"
            )
        ],

        [
            InlineKeyboardButton(
                "📊 Stats",
                callback_data="stats"
            )
        ],

        [
            InlineKeyboardButton(
                "💰 Credits",
                callback_data="credits"
            )
        ],

        [
            InlineKeyboardButton(
                "❌ End Chat",
                callback_data="end"
            )
        ]

    ])

def back_menu():

    return InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                "🔙 Back",
                callback_data="menu"
            )
        ],

        [
            InlineKeyboardButton(
                "❌ End Chat",
                callback_data="end"
            )
        ]

    ])

# ==================================================
# START
# ==================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "⚠️ Please join our official channel first!",
        reply_markup=join_keyboard()
    )

# ==================================================
# JOINED
# ==================================================

async def joined(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user = update.effective_user

    register_user(user)

    await query.message.edit_text(
        f"""
✅ PROFILE CREATED

👤 {user.first_name}
🆔 {user.id}

Welcome to Promotion Bot 🚀
""",
        reply_markup=main_menu()
    )

# ==================================================
# CALLBACKS
# ==================================================

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user = update.effective_user

    # ======================================
    # END
    # ======================================

    if query.data == "end":

        await query.message.edit_text(
            "👋 Chat Ended\n\nSend /start to begin again"
        )

    # ======================================
    # MENU
    # ======================================

    elif query.data == "menu":

        await query.message.edit_text(
            "🏠 MAIN MENU",
            reply_markup=main_menu()
        )

    # ======================================
    # PROFILE
    # ======================================

    elif query.data == "profile":

        cursor.execute("""
        SELECT *
        FROM users
        WHERE user_id=?
        """, (user.id,))

        data = cursor.fetchone()

        text = f"""
👤 PROFILE

🆔 ID: {user.id}
📛 Username: @{user.username}

📅 First Seen:
{data[2]}

⏰ Last Seen:
{data[3]}

💰 Credits:
{data[4]}
"""

        await query.message.edit_text(
            text,
            reply_markup=back_menu()
        )

    # ======================================
    # STATS
    # ======================================

    elif query.data == "stats":

        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM posts")
        total_posts = cursor.fetchone()[0]

        text = f"""
📊 BOT STATS

👥 Users:
{total_users}

📢 Posts:
{total_posts}
"""

        await query.message.edit_text(
            text,
            reply_markup=back_menu()
        )

    # ======================================
    # CREDITS
    # ======================================

    elif query.data == "credits":

        cursor.execute("""
        SELECT credits
        FROM users
        WHERE user_id=?
        """, (user.id,))

        credits = cursor.fetchone()[0]

        text = f"""
💰 YOUR CREDITS

Current Credits:
{credits}

Future:
Premium promotions coming soon 🚀
"""

        await query.message.edit_text(
            text,
            reply_markup=back_menu()
        )

    # ======================================
    # CREATE POST
    # ======================================

    elif query.data == "create_post":

        user_states[user.id] = {
            "step": "category"
        }

        keyboard = InlineKeyboardMarkup([

            [
                InlineKeyboardButton(
                    "YouTube",
                    callback_data="cat_youtube"
                )
            ],

            [
                InlineKeyboardButton(
                    "Telegram",
                    callback_data="cat_telegram"
                )
            ],

            [
                InlineKeyboardButton(
                    "Business",
                    callback_data="cat_business"
                )
            ]

        ])

        await query.message.edit_text(
            "📂 Choose Category",
            reply_markup=keyboard
        )

    # ======================================
    # CATEGORY
    # ======================================

    elif query.data.startswith("cat_"):

        category = query.data.replace("cat_", "")

        user_states[user.id]["category"] = category
        user_states[user.id]["step"] = "media"

        await query.message.reply_text(
            """
📤 Send:

• Photo
OR
• Video

with caption
"""
        )

    # ======================================
    # FEED
    # ======================================

    elif query.data == "feed":

        cursor.execute("""
        SELECT
        id,
        username,
        description,
        likes,
        dislikes,
        views,
        link,
        file_id,
        file_type
        FROM posts
        WHERE approved=1
        ORDER BY featured DESC, id DESC
        LIMIT 5
        """)

        posts = cursor.fetchall()

        if not posts:

            await query.message.edit_text(
                "📭 No posts available",
                reply_markup=back_menu()
            )

            return

        for p in posts:

            post_id = p[0]

            cursor.execute("""
            UPDATE posts
            SET views = views + 1
            WHERE id=?
            """, (post_id,))

            conn.commit()

            caption = f"""
📢 PROMOTION POST

👤 @{p[1]}

📝 {p[2]}

👍 {p[3]}
👎 {p[4]}
👁 {p[5] + 1}

🔗 {p[6]}
"""

            buttons_feed = InlineKeyboardMarkup([

                [
                    InlineKeyboardButton(
                        "👍 Like",
                        callback_data=f"like_{post_id}"
                    ),

                    InlineKeyboardButton(
                        "👎 Dislike",
                        callback_data=f"dislike_{post_id}"
                    )
                ]

            ])

            if p[8] == "photo":

                await context.bot.send_photo(
                    chat_id=user.id,
                    photo=p[7],
                    caption=caption,
                    reply_markup=buttons_feed
                )

            elif p[8] == "video":

                await context.bot.send_video(
                    chat_id=user.id,
                    video=p[7],
                    caption=caption,
                    reply_markup=buttons_feed
                )

        await context.bot.send_message(
            chat_id=user.id,
            text="🏠 Feed Ended",
            reply_markup=back_menu()
        )

    # ======================================
    # LIKE
    # ======================================

    elif query.data.startswith("like_"):

        post_id = query.data.replace("like_", "")

        cursor.execute("""
        SELECT *
        FROM post_actions
        WHERE user_id=? AND post_id=?
        """, (user.id, post_id))

        already = cursor.fetchone()

        if already:

            await query.answer(
                "Already reacted!"
            )

            return

        cursor.execute("""
        INSERT INTO post_actions
        VALUES (?, ?, ?)
        """, (
            user.id,
            post_id,
            "like"
        ))

        cursor.execute("""
        UPDATE posts
        SET likes = likes + 1
        WHERE id=?
        """, (post_id,))

        conn.commit()

        await query.answer("👍 Liked")

    # ======================================
    # DISLIKE
    # ======================================

    elif query.data.startswith("dislike_"):

        post_id = query.data.replace("dislike_", "")

        cursor.execute("""
        SELECT *
        FROM post_actions
        WHERE user_id=? AND post_id=?
        """, (user.id, post_id))

        already = cursor.fetchone()

        if already:

            await query.answer(
                "Already reacted!"
            )

            return

        cursor.execute("""
        INSERT INTO post_actions
        VALUES (?, ?, ?)
        """, (
            user.id,
            post_id,
            "dislike"
        ))

        cursor.execute("""
        UPDATE posts
        SET dislikes = dislikes + 1
        WHERE id=?
        """, (post_id,))

        conn.commit()

        await query.answer("👎 Disliked")

# ==================================================
# MEDIA POST SYSTEM
# ==================================================

async def media_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    if user.id not in user_states:
        return

    state = user_states[user.id]

    if state["step"] != "media":
        return

    file_id = None
    file_type = None

    if update.message.photo:

        file_id = update.message.photo[-1].file_id
        file_type = "photo"

    elif update.message.video:

        file_id = update.message.video.file_id
        file_type = "video"

    else:

        await update.message.reply_text(
            "❌ Send photo or video"
        )

        return

    caption = update.message.caption or ""

    state["file_id"] = file_id
    state["file_type"] = file_type
    state["description"] = caption

    state["step"] = "link"

    await update.message.reply_text(
        "🔗 Now send promotion link"
    )

# ==================================================
# TEXT HANDLER
# ==================================================

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    if user.id not in user_states:
        return

    state = user_states[user.id]

    # ======================================
    # LINK STEP
    # ======================================

    if state["step"] == "link":

        link = update.message.text

        cursor.execute("""
        INSERT INTO posts (
            user_id,
            username,
            category,
            file_id,
            file_type,
            link,
            description,
            approved,
            time
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (

            user.id,
            user.username,
            state["category"],
            state["file_id"],
            state["file_type"],
            link,
            state["description"],
            1,
            str(datetime.now())

        ))

        conn.commit()

        await update.message.reply_text(
            """
✅ POST PUBLISHED

Your promotion is now live 🚀
""",
            reply_markup=main_menu()
        )

        # ADMIN ALERT

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"""
🚨 NEW PROMOTION

👤 @{user.username}

📂 {state['category']}

📝 {state['description']}

🔗 {link}
"""
        )

        del user_states[user.id]

# ==================================================
# ADMIN COMMANDS
# ==================================================

async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    cursor.execute("SELECT COUNT(*) FROM users")
    total = cursor.fetchone()[0]

    await update.message.reply_text(
        f"👥 Total Users: {total}"
    )

async def posts_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    cursor.execute("SELECT COUNT(*) FROM posts")
    total = cursor.fetchone()[0]

    await update.message.reply_text(
        f"📢 Total Posts: {total}"
    )

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    text = update.message.text.replace("/broadcast", "")

    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()

    sent = 0

    for u in users:

        try:

            await context.bot.send_message(
                chat_id=u[0],
                text=f"📢 ADMIN MESSAGE\n\n{text}"
            )

            sent += 1

        except:
            pass

    await update.message.reply_text(
        f"✅ Broadcast sent to {sent} users"
    )

# ==================================================
# MAIN
# ==================================================

def main():

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(
        CallbackQueryHandler(
            joined,
            pattern="joined"
        )
    )

    app.add_handler(
        CallbackQueryHandler(buttons)
    )

    app.add_handler(
        MessageHandler(
            filters.PHOTO | filters.VIDEO,
            media_handler
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            text_handler
        )
    )

    # ADMIN

    app.add_handler(
        CommandHandler(
            "users",
            users_command
        )
    )

    app.add_handler(
        CommandHandler(
            "posts",
            posts_command
        )
    )

    app.add_handler(
        CommandHandler(
            "broadcast",
            broadcast_command
        )
    )

    print("🚀 BOT RUNNING...")

    app.run_polling()

# ==================================================
# RUN
# ==================================================

if __name__ == "__main__":
    main()
