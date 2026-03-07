#!/usr/bin/env python3
import os
import sys
import logging
import asyncio
import aiohttp
import random
import time
from pathlib import Path
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Route
import uvicorn
from collections import defaultdict
from dotenv import load_dotenv

# Добавляем путь к core
sys.path.insert(0, str(Path(__file__).parent))

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ========== ЗАГРУЗКА .ENV ==========
env_loaded = False
env_paths = [
    Path('.env'),
    Path('/etc/secrets/.env'),
]

for env_path in env_paths:
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        print(f"✅ Загружен .env из: {env_path}")
        env_loaded = True
        break

if not env_loaded:
    print("⚠️ .env файл не найден, использую переменные окружения")

# ========== ПРОВЕРКА ТОКЕНОВ ==========
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    print("=== ОТЛАДОЧНАЯ ИНФОРМАЦИЯ ===")
    print(f"PORT из окружения: {os.environ.get('PORT', 'не задан')}")
    print(f"RENDER_EXTERNAL_URL: {os.environ.get('RENDER_EXTERNAL_URL', 'не задан')}")
    print(f"Токен найден: {'✅' if TELEGRAM_BOT_TOKEN else '❌'}")
    print(f"Длина токена: {len(TELEGRAM_BOT_TOKEN) if TELEGRAM_BOT_TOKEN else 0}")
    print("="*50)
    print(f"PORT из окружения: {os.environ.get('PORT', 'не задан')}")
    print(f"RENDER_EXTERNAL_URL: {os.environ.get('RENDER_EXTERNAL_URL', 'не задан')}")
    print(f"Токен найден: {'✅' if TELEGRAM_BOT_TOKEN else '❌'}")
    print(f"Длина токена: {len(TELEGRAM_BOT_TOKEN) if TELEGRAM_BOT_TOKEN else 0}")
    print("="*50)
    print("❌ ОШИБКА: TELEGRAM_BOT_TOKEN не найден!")
    sys.exit(1)

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
AI_MODEL = "google/gemini-2.0-flash-lite-001"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

print(f"✅ Токен загружен (длина: {len(TELEGRAM_BOT_TOKEN)})")
print(f"✅ OpenRouter API ключ {'найден' if OPENROUTER_API_KEY else 'не найден'}")

class SimpleBot:
    def __init__(self):
        self.name = "Рыжик"
        self.start_time = time.time()
        self.message_count = 0
    
    async def get_response(self, message):
        self.message_count += 1
        responses = [
            "*виляет хвостом* Привет!",
            "*зевает* Как дела?",
            "*хихикает* Расскажи что-нибудь",
        ]
        return random.choice(responses)

# Создаем экземпляр бота
bot_instance = SimpleBot()
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# ========== ОБРАБОТЧИКИ ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"🦊 Привет, {user.first_name}!\n"
        f"Я {bot_instance.name} - фурри-лис!\n"
        f"/stats - статистика"
    )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uptime = int(time.time() - bot_instance.start_time)
    hours = uptime // 3600
    minutes = (uptime % 3600) // 60
    await update.message.reply_text(
        f"📊 Статистика\n"
        f"⏱️ Аптайм: {hours}ч {minutes}м\n"
        f"💬 Сообщений: {bot_instance.message_count}"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    msg = update.message.text
    
    await update.message.chat.send_action(action="typing")
    response = await bot_instance.get_response(msg)
    
    if response:
        await update.message.reply_text(response)

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("stats", stats))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# ========== WEBHOOK ==========
async def webhook(request):
    try:
        data = await request.json()
        update = Update.de_json(data, application.bot)
        await application.process_update(update)
        return Response("ok", status_code=200)
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return Response("error", status_code=500)

async def healthcheck(request):
    return Response("healthy", status_code=200)

async def test(request):
    return Response("✅ Бот работает!", status_code=200)

# ========== МАРШРУТЫ ==========
routes = [
    Route(f"/{TELEGRAM_BOT_TOKEN}", webhook, methods=["POST"]),
    Route("/healthcheck", healthcheck, methods=["GET"]),
    Route("/test", test, methods=["GET"]),
]

app = Starlette(routes=routes)

# ========== ЗАПУСК ==========


# ========== ЗАПУСК ДЛЯ RENDER ==========
if __name__ == "__main__":
    import uvicorn
    import asyncio
    
    port = int(os.environ.get("PORT", 10000))
    print(f"✅ ЗАПУСК НА ПОРТУ: {port}")
    
    # Простой запуск без сложной инициализации
    uvicorn.run(
        "webhook_bot:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        reload=False
    )
