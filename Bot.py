import os
import instaloader
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

# ================= CONFIG =================
TOKEN = os.getenv("BOT_TOKEN")
BASE_URL = os.getenv("BASE_URL")

# ================= INSTALOADER =================
loader = instaloader.Instaloader(
    download_pictures=False,
    download_videos=False,
    save_metadata=False,
    quiet=True
)

# ================= FLASK (keep alive) =================
app = Flask(__name__)

@app.route("/")
def home():
    return "OK"

@app.route(f"/webhook/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), app_bot)
    app_bot.update_queue.put(update)
    return "ok"

# ================= CORE FUNCTION =================
def get_profile_pic(username):
    profile = instaloader.Profile.from_username(loader.context, username)
    return profile.profile_pic_url

# ================= HANDLER =================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.text.replace("@", "").strip()

    try:
        pic = get_profile_pic(username)

        await update.message.reply_photo(
            photo=pic,
            caption=f"@{username}"
        )

    except:
        await update.message.reply_text("پیدا نشد ❌")

# ================= BOT =================
app_bot = Application.builder().token(TOKEN).build()
app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

def run_bot():
    app_bot.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        url_path=TOKEN,
        webhook_url=f"{BASE_URL}/webhook/{TOKEN}"
    )

# ================= START =================
if __name__ == "__main__":
    from threading import Thread

    Thread(target=lambda: app.run(host="0.0.0.0", port=10000)).start()
    run_bot()
