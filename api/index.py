from flask import Flask, request, jsonify
from telegram import Bot, Update, InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, filters
import random
import os
import logging
from functools import wraps

# === INITIALIZATION ===
app = Flask(__name__)

# === CONFIGURATION ===
# Production values should come from environment variables
BOT_TOKEN = os.getenv('BOT_TOKEN', "7504457974:AAG0i7X4GAX_awDH72M1Q9hetaJCR2xfuOw")
ADMIN_ID = int(os.getenv('ADMIN_ID', "2114237158"))
WEBHOOK_URL = os.getenv('WEBHOOK_URL', "https://xyz-w9uscmo52-waspros.vercel.app/api/index")
WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET', "your-secret-token-here")

# Service configuration
SERVICES = [
    "StarVision", "GhostVPN", "AnonX Cleaner",
    "ProPrivacy AI", "MegaMail Unlocker", "Midnight Burner"
]

DONATION_AMOUNTS = [100, 200, 300]  # 1, 2, 3 stars in XTR currency

# === SETUP ===
bot = Bot(token=BOT_TOKEN)
dispatcher = Dispatcher(bot=bot, update_queue=None, workers=0)

# === UTILITIES ===
def restricted(func):
    """Decorator to restrict access to admin only"""
    @wraps(func)
    def wrapped(update, context, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id != ADMIN_ID:
            print(f"Unauthorized access denied for {user_id}.")
            return
        return func(update, context, *args, **kwargs)
    return wrapped

def generate_service_message(user_name: str, service: str) -> str:
    """Generate random donation message"""
    messages = [
        f"Hey {user_name}, support *{service}* with stars!",
        f"Keep *{service}* running with your donation!",
        f"*{service}* needs your support!",
        f"Help *{service}* grow with stars!"
    ]
    return random.choice(messages)

# === HANDLERS ===
def start(update: Update, context) -> None:
    """Handler for /start command"""
    try:
        user = update.effective_user
        service = random.choice(SERVICES)
        stars = random.choice(DONATION_AMOUNTS)
        
        # Create payment invoice
        bot.send_invoice(
            chat_id=update.message.chat_id,
            title=f"Support {service}",
            description=generate_service_message(user.first_name, service),
            payload=f"{service.lower()}_donation",
            provider_token="STARS",  # Special value for Telegram Stars
            currency="XTR",  # Telegram Stars currency code
            prices=[LabeledPrice(f"{stars//100} Star(s)", stars)],
            start_parameter="star_donation",
            need_name=True,
            need_email=True
        )
    except Exception as e:
        logging.error(f"Error in start handler: {e}")
        if ADMIN_ID:
            bot.send_message(ADMIN_ID, f"🚨 Start Error: {str(e)}")

def successful_payment(update: Update, context) -> None:
    """Handle successful payments"""
    try:
        payment = update.message.successful_payment
        user = update.effective_user
        
        # Send thank you message
        bot.send_message(
            chat_id=update.message.chat_id,
            text=f"🎉 Thank you {user.first_name} for donating {payment.total_amount//100} stars!"
        )
        
        # Notify admin
        if ADMIN_ID:
            bot.send_message(
                chat_id=ADMIN_ID,
                text=f"💰 New donation:\n"
                     f"• From: {user.full_name} (@{user.username})\n"
                     f"• Amount: {payment.total_amount//100} stars\n"
                     f"• Service: {payment.invoice_payload}"
            )
    except Exception as e:
        logging.error(f"Payment processing error: {e}")
        if ADMIN_ID:
            bot.send_message(ADMIN_ID, f"🚨 Payment Error: {str(e)}")

# === WEBHOOK ROUTES ===
@app.route('/api/index', methods=['POST'])
def webhook():
    """Main webhook handler"""
    # Verify secret token
    if request.headers.get('X-Telegram-Bot-Api-Secret-Token') != WEBHOOK_SECRET:
        return jsonify({"status": "unauthorized"}), 403
    
    try:
        update = Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
        return jsonify({"status": "success"})
    except Exception as e:
        logging.error(f"Webhook error: {e}")
        if ADMIN_ID:
            bot.send_message(ADMIN_ID, f"🚨 Webhook Error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/set_webhook', methods=['GET'])
@restricted
def set_webhook():
    """Manually set webhook (admin only)"""
    result = bot.set_webhook(
        url=WEBHOOK_URL,
        secret_token=WEBHOOK_SECRET,
        drop_pending_updates=True
    )
    return jsonify({"status": "success", "result": result})

# === REGISTER HANDLERS ===
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))

# === START APPLICATION ===
if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    
    # Set webhook on startup
    bot.set_webhook(
        url=WEBHOOK_URL,
        secret_token=WEBHOOK_SECRET,
        drop_pending_updates=True
    )
    
    # Start Flask app
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
