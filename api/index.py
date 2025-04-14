from flask import Flask, request
from telegram import Bot, Update, InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, filters
import random

# === HARDCODED BOT SETTINGS ===
BOT_TOKEN = "7504457974:AAG0i7X4GAX_awDH72M1Q9hetaJCR2xfuOw"
ADMIN_ID = 2114237158

bot = Bot(BOT_TOKEN)
app = Flask(__name__)
dispatcher = Dispatcher(bot=bot, update_queue=None, workers=0)

# === Random Names and Messages ===
SERVICES = [
    "StarVision", "GhostVPN", "AnonX Cleaner",
    "ProPrivacy AI", "MegaMail Unlocker", "Midnight Burner"
]

MESSAGES = [
    "Hey {name}, support *{service}* with a star!",
    "Donate to keep *{service}* alive!",
    "*{service}* needs your spark!",
    "Drop some stars for *{service}*!"
]

# === /start COMMAND ===
def start(update: Update, context):
    user = update.effective_user
    service = random.choice(SERVICES)
    message = random.choice(MESSAGES).format(name=user.first_name, service=service)
    stars = random.choice([100, 200, 300])  # 1-3 Stars

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"Donate {stars // 100} Star(s)", pay=True)]
    ])

    bot.send_invoice(
        chat_id=update.message.chat_id,
        title=service,
        description="Support our service with Telegram Stars",
        payload="donate_stars",
        provider_token="STARS",
        currency="XTR",
        prices=[LabeledPrice("Star Support", stars)],
        reply_markup=keyboard,
        start_parameter="star-donation"
    )

def successful_payment(update: Update, context):
    bot.send_message(chat_id=update.message.chat_id, text="Thanks for donating stars!")

# === REGISTER HANDLERS ===
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))

# === VERCEL WEBHOOK ENTRY ===
@app.route("/api/index", methods=["POST"])
def webhook():
    try:
        update = Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
    except Exception as e:
        print(f"Webhook error: {e}")
        return "error", 500
    return "ok", 200
