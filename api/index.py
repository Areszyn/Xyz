from flask import Flask, request
from telegram import Bot, Update, InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, filters
import random

# === HARDCODED CONFIG ===
BOT_TOKEN = "7504457974:AAG0i7X4GAX_awDH72M1Q9hetaJCR2xfuOw"
ADMIN_ID = 2114237158  # Replace with your numeric Telegram user ID

bot = Bot(token=BOT_TOKEN)
app = Flask(__name__)
dispatcher = Dispatcher(bot=bot, update_queue=None, workers=0)

# === RANDOM SERVICE NAMES & MESSAGES ===
SERVICES = [
    "Shadow Proxy Tool", "AI Chat Pro", "Crypto Wallet Guard",
    "StarCleaner X", "Night Vision AI", "Secret Mail Unlocker"
]

MESSAGES = [
    "Hey {name}, support *{service}* with some stars!",
    "Help fund *{service}*!",
    "Your stars keep *{service}* alive!",
    "Donate to support *{service}*!",
    "*{service}* runs on stardust. Can you spare some?"
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
        description="Support with Telegram Stars",
        payload="stars-donation",
        provider_token="STARS",  # Special token for Telegram Stars
        currency="XTR",
        prices=[LabeledPrice("Donation", stars)],
        reply_markup=keyboard,
        start_parameter="donate-stars"
    )

# === ON SUCCESSFUL PAYMENT ===
def successful_payment(update: Update, context):
    bot.send_message(chat_id=update.message.chat_id, text="Thanks for donating!")

# === REGISTER HANDLERS ===
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))

# === VERCEL ENTRYPOINT ===
@app.route("/api/index", methods=["POST"])
def main():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"
