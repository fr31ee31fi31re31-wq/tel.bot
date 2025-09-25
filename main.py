import os
import logging
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

user_modes = {}

def text_to_unicode(text: str) -> str:
    return "-".join(f"U+{ord(c):04X}" for c in text)

def unicode_to_text(unicode_string: str) -> str:
    try:
        codes = unicode_string.strip().split("-")
        chars = [chr(int(code.upper().replace("U+", ""), 16)) for code in codes]
        return "".join(chars)
    except (ValueError, IndexError):
        return "⚠️ صيغة يونيكود غير صالحة."

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_modes[update.effective_user.id] = None
    await update.message.reply_text("👋 ...")

# بقية الأوامر نفسها …

app = Flask(__name__)
telegram_app = Application.builder().token(TOKEN).build()

telegram_app.add_handler(CommandHandler("start", start_command))
# … باقي الهاندلرز

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    telegram_app.update_queue.put(update)
    return "ok"

@app.route("/")
def index():
    return "Webhook is running"

if __name__ == "__main__":
    # تأكد من استدعاء setup_webhook بشكل صحيح
    asyncio.get_event_loop().create_task(
        telegram_app.bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")
    )
    app.run(port=5000)