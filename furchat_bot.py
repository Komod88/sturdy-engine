#!/usr/bin/env python3
import os
import sys
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_NAME = os.getenv("BOT_NAME", "Рыжик")

if not BOT_TOKEN:
    print("❌ BOT_TOKEN не найден!")
    sys.exit(1)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"🦊 Привет, {user.first_name}!\n"
        f"Я {BOT_NAME} — фурри-лис.\n"
        f"*зевает* Спрашивай что хотел!"
    )

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    await update.message.reply_text(f"*виляет хвостом* Ты сказал: {text}")

def main():
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🚀 Запуск на порту {port}")
    
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    
    if os.environ.get('RENDER'):
        logger.info("🔗 Режим webhook")
        hostname = os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'furchat-bot.onrender.com')
        app.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=BOT_TOKEN,
            webhook_url=f"https://{hostname}/{BOT_TOKEN}"
        )
    else:
        logger.info("📡 Режим polling")
        app.run_polling()

if __name__ == "__main__":
    main()
