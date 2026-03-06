#!/usr/bin/env python3
import os
import sys
import logging
import asyncio
from pathlib import Path
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Route
import uvicorn

# Добавляем путь к core
sys.path.insert(0, str(Path(__file__).parent))

# Пытаемся импортировать FurChat
try:
    from core.bot import FurChat
    HAS_CORE = True
except ImportError:
    HAS_CORE = False
    print("⚠️ Модуль core не найден, используется упрощённая версия")

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN", "8696373751:AAHVQRg9ZXrJbuaKnT1UdTIAvqa9GEfPan4")
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

class SimpleBot:
    def __init__(self):
        self.name = "Рыжий"
        self.actions = ["*виляет хвостом*", "*чешет за ухом*", "*прижимает уши*"]
        self.greetings = ["*виляет хвостом* Привет!", "Здаров!", "Приветик!"]
        
    def respond(self, user_id, text, telegram_mode=False):
        text = text.lower()
        if "привет" in text:
            return f"{self.actions[0]} Привет!"
        elif "как дела" in text:
            return f"{self.actions[1]} Норм, а у тебя?"
        elif "пока" in text:
            return f"{self.actions[2]} Пока!"
        else:
            return f"{self.actions[0]} {text}?"

# Создаём приложение
if HAS_CORE:
    bot_instance = FurChat(str(Path(__file__).parent))
else:
    bot_instance = SimpleBot()

print(f"✅ Бот {bot_instance.name} готов")

# Создаём Telegram Application
application = Application.builder().token(TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"🐺 Привет, {user.first_name}!\n"
        f"Я {bot_instance.name} - фурри-лис\n"
        f"Просто пиши мне!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    msg = update.message.text
    response = bot_instance.respond(user_id, msg, False)
    if response:
        await update.message.reply_text(response)

application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Webhook handler для Starlette
async def webhook(request):
    try:
        data = await request.json()
        update = Update.de_json(data, application.bot)
        await application.process_update(update)
        return Response("ok", status_code=200)
    except Exception as e:
        logging.error(f"Webhook error: {e}")
        return Response("error", status_code=500)

async def healthcheck(request):
    return Response("healthy", status_code=200)

# Starlette приложение
routes = [
    Route(f"/{TOKEN}", webhook, methods=["POST"]),
    Route("/healthcheck", healthcheck, methods=["GET"]),
]

app = Starlette(routes=routes)

# Устанавливаем webhook при запуске
async def startup():
    webhook_url = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'localhost')}/{TOKEN}"
    await application.bot.set_webhook(url=webhook_url)
    print(f"✅ Webhook установлен: {webhook_url}")

app.add_event_handler("startup", startup)

# Для локального тестирования
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
