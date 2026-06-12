import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
import instaloader

TOKEN = os.getenv("BOT_TOKEN")

loader = instaloader.Instaloader(
    download_pictures=False,
    download_videos=False,
    save_metadata=False,
    quiet=True
)

cache = {}

def fetch(username):
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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("یوزرنیم اینستاگرام را بفرست")

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.text.replace("@", "").strip()

    try:
        data = fetch(username)
        cache[username] = data

        keyboard = [
            [
                InlineKeyboardButton("📊 اطلاعات", callback_data=f"info:{username}"),
                InlineKeyboardButton("📸 عکس", callback_data=f"pic:{username}")
            ]
        ]

        caption = f"{data['username']}\n{data['full_name']}"

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
Username: {data['username']}
Name: {data['full_name']}
Bio: {data['bio']}
Followers: {data['followers']}
Following: {data['following']}
Posts: {data['posts']}
Private: {data['private']}
"""
        await q.message.reply_text(text)

    if action == "pic":
        await q.message.reply_photo(data["pic"])


def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    app.add_handler(CallbackQueryHandler(buttons))

    app.run_polling()


if __name__ == "__main__":
    main()
