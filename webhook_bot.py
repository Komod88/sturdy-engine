#!/usr/bin/env python3
"""
Telegram bot for Render
"""

import os
import sys
import logging
from pathlib import Path
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse, Response
from starlette.routing import Route
import uvicorn
import asyncio

# ========== ЗАГРУЗКА ИЗ .ENV ==========
try:
    from dotenv import load_dotenv
    env_path = Path('.env')
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        print("✅ .env файл загружен")
    else:
        print("⚠️ .env файл не найден, использую переменные окружения")
except ImportError:
    print("⚠️ python-dotenv не установлен")

# ========== ТОКЕНЫ ИЗ ПЕРЕМЕННЫХ ОКРУЖЕНИЯ ==========
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

if not TELEGRAM_BOT_TOKEN:
    print("❌ ОШИБКА: TELEGRAM_BOT_TOKEN не найден в переменных окружения!")
    sys.exit(1)

print(f"✅ Токен загружен (длина: {len(TELEGRAM_BOT_TOKEN)})")
print(f"✅ OpenRouter API ключ {'найден' if OPENROUTER_API_KEY else 'не найден'}")

# ========== TELEGRAM ИМПОРТЫ ==========
try:
    from telegram import Update
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
    TELEGRAM_AVAILABLE = True
    print("✅ python-telegram-bot импортирован")
except ImportError:
    TELEGRAM_AVAILABLE = False
    print("⚠️ python-telegram-bot не установлен")

# ========== НАСТРОЙКА ЛОГИРОВАНИЯ ==========
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== СОЗДАЁМ TELEGRAM APPLICATION ==========
application = None
if TELEGRAM_AVAILABLE:
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    print("✅ Telegram Application создан")

# ========== ОБРАБОТЧИКИ ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"🦊 Привет, {user.first_name}!\n"
        f"Я Рыжик - фурри-лис!\n"
        f"Пиши мне что-нибудь!"
    )

"
        f"Я Рыжик - фурри-лис!
"
        f"Пиши мне что-нибудь!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    await update.message.reply_text(f"*виляет хвостом* {text}")

if application:
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ Обработчики зарегистрированы")

# ========== WEBHOOK ОБРАБОТЧИК ==========
async def telegram_webhook(request):
    if not application:
        return Response("Telegram bot not available", status_code=500)
    
    try:
        data = await request.json()
        logger.info(f"📥 Получен запрос от Telegram")
        update = Update.de_json(data, application.bot)
        await application.process_update(update)
        return Response("ok", status_code=200)
    except Exception as e:
        logger.error(f"❌ Webhook error: {e}")
        return Response("error", status_code=500)

# ========== ЭНДПОИНТЫ ==========
async def healthcheck(request):
    return PlainTextResponse("healthy")

async def test(request):
    return PlainTextResponse("✅ Бот работает!")

# ========== МАРШРУТЫ ==========
routes = [
    Route(f"/{TELEGRAM_BOT_TOKEN}", telegram_webhook, methods=["POST"]),
    Route("/healthcheck", healthcheck),
    Route("/test", test),
]

app = Starlette(routes=routes)

# ========== ИНИЦИАЛИЗАЦИЯ ==========
@app.on_event("startup")
async def startup():
    logger.info("🚀 Запуск бота...")
    
    if application:
        await application.initialize()
        await application.start()
        
        render_url = os.environ.get("RENDER_EXTERNAL_URL", "https://furchat-bot.onrender.com")
        webhook_url = f"{render_url}/{TELEGRAM_BOT_TOKEN}"
        
        logger.info(f"🔗 Устанавливаю webhook: {webhook_url}")
        
        try:
            await application.bot.set_webhook(url=webhook_url)
            logger.info("✅ Webhook установлен")
        except Exception as e:
            logger.error(f"❌ Ошибка установки webhook: {e}")

@app.on_event("shutdown")
async def shutdown():
    logger.info("🛑 Остановка бота...")
    if application:
        await application.stop()
        await application.shutdown()

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"✅ Запуск на порту: {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
