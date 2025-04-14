from flask import Flask, request, jsonify
from telegram import Bot, Update, InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, filters
import random
import logging
from functools import wraps

# ===== CONFIGURATION (DIRECT VARIABLES - FOR TESTING ONLY) =====
BOT_TOKEN = "7504457974:AAG0i7X4GAX_awDH72M1Q9hetaJCR2xfuOw"
ADMIN_ID = 2114237158
WEBHOOK_URL = "https://xyz-w9uscmo52-waspros.vercel.app/api/index"
WEBHOOK_SECRET = "yhookhvdaw5jnnj"  # Replace with stronger secret

# Service Configuration
SERVICES = [
    "StarVision", "GhostVPN", "AnonX Cleaner",
    "ProPrivacy AI", "MegaMail Unlocker", "Midnight Burner"
]
DONATION_AMOUNTS = [100, 200, 300]  # 1, 2, 3 stars in XTR currency
THANK_YOU_MESSAGES = [
    "🌟 Thanks {name}! You just donated {stars} stars!",
    "✨ Wow {name}! {stars} stars received!",
    "💎 {name}, your {stars} stars make a difference!"
]

# ===== INITIALIZATION =====
app = Flask(__name__)
bot = Bot(token=BOT_TOKEN)
dispatcher = Dispatcher(bot=bot, update_queue=None, workers=0)

# ===== SECURITY MIDDLEWARE =====
def require_secret_token(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.headers.get('X-Telegram-Bot-Api-Secret-Token') != WEBHOOK_SECRET:
            return jsonify({"error": "Unauthorized"}), 403
        return f(*args, **kwargs)
    return decorated_function

# ===== HANDLERS =====
def start(update: Update, _):
    try:
        user = update.effective_user
        service = random.choice(SERVICES)
        stars = random.choice(DONATION_AMOUNTS)
        
        bot.send_invoice(
            chat_id=update.message.chat_id,
            title=f"Support {service}",
            description=f"Help keep {service} running with Telegram Stars",
            payload=f"{service.lower()}_donation",
            provider_token="STARS",
            currency="XTR",
            prices=[LabeledPrice(f"{stars//100} Star(s)", stars)],
            start_parameter="star_donation"
        )
    except Exception as e:
        logging.error(f"Start error: {e}")
        bot.send_message(ADMIN_ID, f"🚨 Start Error: {str(e)}")

def successful_payment(update: Update, _):
    try:
        payment = update.message.successful_payment
        user = update.effective_user
        thank_msg = random.choice(THANK_YOU_MESSAGES).format(
            name=user.first_name,
            stars=payment.total_amount//100
        )
        
        bot.send_message(chat_id=update.message.chat_id, text=thank_msg)
        bot.send_message(
            chat_id=ADMIN_ID,
            text=f"💰 New donation:\nFrom: {user.full_name}\nAmount: {payment.total_amount//100} stars"
        )
    except Exception as e:
        logging.error(f"Payment error: {e}")
        bot.send_message(ADMIN_ID, f"🚨 Payment Error: {str(e)}")

# ===== WEBHOOK ROUTES =====
@app.route('/api/index', methods=['POST'])
@require_secret_token
def webhook():
    try:
        update = Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
        return jsonify({"status": "success"})
    except Exception as e:
        logging.error(f"Webhook error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/set_webhook', methods=['GET'])
def configure_webhook():
    result = bot.set_webhook(
        url=WEBHOOK_URL,
        secret_token=WEBHOOK_SECRET,
        drop_pending_updates=True
    )
    return jsonify({"status": "success", "result": str(result)})

# ===== REGISTER HANDLERS =====
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))

# ===== START APPLICATION =====
if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    
    # Configure webhook automatically on startup
    bot.set_webhook(
        url=WEBHOOK_URL,
        secret_token=WEBHOOK_SECRET,
        drop_pending_updates=True
    )
    
    app.run(host='0.0.0.0', port=5000)
