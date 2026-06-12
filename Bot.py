import os
from flask import Flask, request
import instaloader

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

# ================= CONFIG =================
TOKEN = os.getenv("BOT_TOKEN")
BASE_URL = os.getenv("BASE_URL")  # آدرس Render

loader = instaloader.Instaloader(
    download_pictures=False,
    download_videos=False,
    save_metadata=False,
    quiet=True
)

cache = {}

# ================= FLASK APP =================
app = Flask(__name__)

# Telegram webhook endpoint
@app.route(f"/webhook/{TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, app_bot)
    app_bot.update_queue.put(update)
    return "ok"

@app.route("/")
def home():
    return "Bot is running"

# ================= INSTAGRAM =================
def fetch_profile(username):
    p = instaloader.Profile.from_username(loader.context, username)

    return {
        "username": p.username,
        "full_name": p.full_name,
        "bio": p.biography,
        "followers": p.followers,
        "following": p.followees,
        "posts": p.mediacount,
        "private": p.is_private,
        "pic": p.profile_pic_url
    }

# ================= TELEGRAM HANDLERS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("یوزرنیم اینستاگرام را ارسال کن")

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.text.replace("@", "").strip()

    try:
        data = fetch_profile(username)
        cache[username] = data

        keyboard = [
            [
                InlineKeyboardButton("📊 اطلاعات", callback_data=f"info:{username}"),
                InlineKeyboardButton("📸 عکس", callback_data=f"pic:{username}")
            ]
        ]

        caption = f"{data['username']} | {data['full_name']}"

        await update.message.reply_photo(
            photo=data["pic"],
            caption=caption,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except:
        await update.message.reply_text("پروفایل پیدا نشد")

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    action, username = q.data.split(":")
    data = cache.get(username)

    if not data:
        await q.message.reply_text("دوباره ارسال کن")
        return

    if action == "info":
        text = f"""
👤 Username: {data['username']}
📝 Name: {data['full_name']}
📄 Bio: {data['bio']}

👥 Followers: {data['followers']}
➡️ Following: {data['following']}
📦 Posts: {data['posts']}
🔒 Private: {data['private']}
"""
        await q.message.reply_text(text)

    elif action == "pic":
        await q.message.reply_photo(data["pic"])

# ================= INIT BOT =================
app_bot = Application.builder().token(TOKEN).build()

app_bot.add_handler(CommandHandler("start", start))
app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
app_bot.add_handler(CallbackQueryHandler(buttons))

# ================= MAIN =================
def run_bot():
    app_bot.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        url_path=TOKEN,
        webhook_url=f"{BASE_URL}/webhook/{TOKEN}"
    )

if __name__ == "__main__":
    from threading import Thread

    Thread(target=lambda: app.run(host="0.0.0.0", port=10000)).start()
    run_bot()
