import os
import logging
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# إعداد التوكن من متغير البيئة
TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # عنوان السيرفر العام (مثل من Deta أو ngrok)

# إعداد تسجيل الأخطاء والمعلومات
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# تخزين حالة المستخدم
user_modes = {}

# دوال التحويل
def text_to_unicode(text: str) -> str:
    return '-'.join(f'U+{ord(char):04X}' for char in text)

def unicode_to_text(unicode_string: str) -> str:
    try:
        codes = unicode_string.strip().split('-')
        chars = [chr(int(code.upper().replace('U+', ''), 16)) for code in codes]
        return ''.join(chars)
    except (ValueError, IndexError):
        return "⚠️ صيغة اليونيكود غير صالحة. تأكد من الكتابة الصحيحة."

# أوامر البوت
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_modes[update.effective_user.id] = None
    await update.message.reply_text(
        "👋 مرحبًا!\n\n"
        "/text → تحويل نص إلى يونيكود\n"
        "/unicode → تحويل يونيكود إلى نص\n"
        "/stop → إيقاف الوضع النشط"
    )

async def text_mode_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_modes[update.effective_user.id] = "text"
    await update.message.reply_text("✅ وضع النص → يونيكود مفعل. أرسل النص الآن.")

async def unicode_mode_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_modes[update.effective_user.id] = "unicode"
    await update.message.reply_text("✅ وضع يونيكود → نص مفعل. أرسل الأكواد الآن.")

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_modes[update.effective_user.id] = None
    await update.message.reply_text("🛑 تم إيقاف الوضع. أرسل أمرًا جديدًا للبدء.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = user_modes.get(update.effective_user.id)
    if mode == "text":
        await update.message.reply_text(text_to_unicode(update.message.text))
    elif mode == "unicode":
        await update.message.reply_text(unicode_to_text(update.message.text))
    else:
        await update.message.reply_text("❓ أرسل /text أو /unicode للبدء.")

# إعداد التطبيق
app = Flask(__name__)
telegram_app = Application.builder().token(TOKEN).build()

# إضافة الأوامر
telegram_app.add_handler(CommandHandler("start", start_command))
telegram_app.add_handler(CommandHandler("text", text_mode_command))
telegram_app.add_handler(CommandHandler("unicode", unicode_mode_command))
telegram_app.add_handler(CommandHandler("stop", stop_command))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# نقطة استقبال التحديثات من تيليجرام
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    telegram_app.update_queue.put(update)
    return "ok"

# تعيين عنوان webhook عند التشغيل
@app.route("/")
def index():
    telegram_app.bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")
    return "✅ Webhook set!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)