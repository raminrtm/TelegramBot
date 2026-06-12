import os
import time
import random
import requests
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")
BASE_URL = os.getenv("BASE_URL")

app = Flask(__name__)

# ================= CACHE =================
cache = {}

# ================= USER AGENTS =================
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (X11; Linux x86_64)",
]

# ================= CORE FETCH =================
def get_profile_pic(username):
    username = username.lower().strip()

    # 🔥 CACHE FIRST
    if username in cache:
        if time.time() - cache[username]["time"] < 3600:
            return cache[username]["pic"]

    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "application/json"
    }

    # ================= METHOD 1: GRAPHQL =================
    try:
        url = f"https://i.instagram.com/api/v1/users/web_profile_info/?username={username}"
        r = requests.get(url, headers=headers, timeout=8)

        if r.status_code == 200:
            data = r.json()
            pic = data["data"]["user"]["profile_pic_url_hd"]

            cache[username] = {"pic": pic, "time": time.time()}
            return pic

    except:
        pass

    # ================= METHOD 2: CDN FALLBACK =================
    try:
        cdn_url = f"https://instagram.com/{username}/?__a=1&__d=dis"
        r = requests.get(cdn_url, headers=headers, timeout=8)

        if r.status_code == 200:
            data = r.json()
            pic = data["graphql"]["user"]["profile_pic_url_hd"]

            cache[username] = {"pic": pic, "time": time.time()}
            return pic

    except:
        pass

    # ================= METHOD 3: DIRECT CDN GUESS =================
    try:
        guess = f"https://www.instagram.com/{username}/media/?size=l"
        r = requests.get(guess, headers=headers, timeout=8)

        if r.status_code == 200:
            cache[username] = {"pic": guess, "time": time.time()}
            return guess

    except:
        pass

    raise Exception("all methods failed")

# ================= WEBHOOK =================
@app.route("/")
def home():
    return "OK"

@app.route(f"/webhook/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), app_bot)
    app_bot.update_queue.put(update)
    return "ok"

# ================= HANDLER =================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.text.replace("@", "").strip()

    # 🔥 retry with backoff
    for i in range(3):
        try:
            pic = get_profile_pic(username)
            break
        except:
            time.sleep(0.5 + random.random())
            pic = None

    if not pic:
        await update.message.reply_text("❌ پیدا نشد یا محدود شد")
        return

    await update.message.reply_photo(photo=pic, caption=f"@{username}")

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

if __name__ == "__main__":
    from threading import Thread

    Thread(target=lambda: app.run(host="0.0.0.0", port=10000)).start()
    run_bot()
