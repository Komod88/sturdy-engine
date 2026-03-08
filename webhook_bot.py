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
# ========== AI ДИАЛОГ С ПАМЯТЬЮ ==========
import requests
import random
from collections import defaultdict

# Запасные ответы на разные темы
FALLBACKS = {
    "привет": ["*виляет хвостом* Привет!", "*машет лапой* Здаров!", "*подпрыгивает* О, привет!"],
    "как дела": ["*зевает* Норм, а у тебя?", "*потягивается* Скучаю...", "*улыбается* Отлично!"],
    "что делаешь": ["*лежит на спинке* Отдыхаю", "*гоняется за хвостом* Развлекаюсь", "*смотрит в окно* Мечтаю"],
    "пока": ["*машет лапой* Пока!", "*грустно* Уходишь?", "Заходи ещё!"],
    "кто ты": ["Я Рыжик - фурри-лис!", "*гордо* Лис с пушистым хвостом!", "Твой пушистый друг"],
    "спасибо": ["*обнимает* Пожалуйста!", "Не за что!", "*радуется* Обращайся!"],
    "люблю": ["*смущается* И я тебя!", "*виляет хвостом* Приятно слышать!", "*прижимается* Ты классный!"],
}

# История диалога для каждого пользователя
user_contexts = defaultdict(list)

def get_ai_response(user_id, message):
    """
    Рыжик отвечает с учётом контекста диалога
    """
    try:
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            # Если нет ключа - используем запасные ответы
            lower_msg = message.lower()
            for key, responses in FALLBACKS.items():
                if key in lower_msg:
                    return random.choice(responses)
            return random.choice(["*чешет за ухом* Хм...", "*наклоняет голову* Расскажи подробнее"])

        # Сохраняем историю для пользователя
        user_contexts[user_id].append({"role": "user", "content": message})
        if len(user_contexts[user_id]) > 10:
            user_contexts[user_id] = user_contexts[user_id][-10:]

        headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "http://localhost",
            "X-Title": "FurChat Bot",
        }

        data = {
            "model": "openrouter/free",
            "messages": [
                {
                    "role": "system", 
                    "content": """Ты — Рыжик, фурри-лис. Твои правила:
- ТОЛЬКО РУССКИЙ ЯЗЫК
- Используй *действия* в звёздочках (*виляет хвостом*, *зевает*, *потягивается*)
- Будь дружелюбным, слегка ленивым, с юмором
- Отвечай коротко (1-2 предложения)
- Помни историю разговора"""
                },
                *user_contexts[user_id]
            ],
            "temperature": 0.9,
            "max_tokens": 200,
        }

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=10
        )

        if response.status_code == 200:
            answer = response.json()['choices'][0]['message']['content']
            if answer and len(answer) > 3:
                user_contexts[user_id].append({"role": "assistant", "content": answer})
                return answer

        # Если API не ответил - ищем по ключевым словам
        lower_msg = message.lower()
        for key, responses in FALLBACKS.items():
            if key in lower_msg:
                return random.choice(responses)

        return random.choice([
            "*чешет за ухом* Хм... интересно",
            "*наклоняет голову* Расскажи подробнее",
            "*виляет хвостом* Давай поговорим об этом",
        ])

    except Exception as e:
        print(f"Ошибка AI: {e}")
        # При ошибке - запасной ответ
        lower_msg = message.lower()
        for key, responses in FALLBACKS.items():
            if key in lower_msg:
                return random.choice(responses)
        return "*зевает* Что-то я задумался..."


# ========== МОСТ МЕЖДУ ИМЕНАМИ ТОКЕНА ==========
# Поддерживаем оба имени для обратной совместимости

# Сначала пробуем BOT_TOKEN
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# Если нет, пробуем BOT_TOKEN
if not BOT_TOKEN:
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    if BOT_TOKEN:
        print("✅ Используется BOT_TOKEN как BOT_TOKEN")

# Если ничего нет — ошибка
if not BOT_TOKEN:
    print("❌ ОШИБКА: Токен не найден! (пробовали BOT_TOKEN и BOT_TOKEN)")
    print("💡 Проверь .env файл или переменные окружения")
    sys.exit(1)

print(f"✅ Токен загружен (длина: {len(BOT_TOKEN)})")


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
TOKEN = os.environ.get("BOT_TOKEN")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

if not BOT_TOKEN:
    print("❌ ОШИБКА: BOT_TOKEN не найден в переменных окружения!")
    sys.exit(1)

print(f"✅ Токен загружен (длина: {len(BOT_TOKEN)})")
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
    application = Application.builder().token(BOT_TOKEN).build()
    print("✅ Telegram Application создан")

# ========== ОБРАБОТЧИКИ ==========
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    print("❌ ОШИБКА: BOT_TOKEN не найден!")
    sys.exit(1)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"🦊 Привет, {user.first_name}!\n"
        f"Я Рыжик - фурри-лис!\n"
        f"Пиши мне что-нибудь!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    message = update.message.text

    await update.message.chat.send_action(action='typing')
    response = get_ai_response(user_id, message)
    await update.message.reply_text(response)
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
    Route(f"/{BOT_TOKEN}", telegram_webhook, methods=["POST"]),
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
        webhook_url = f"{render_url}/{BOT_TOKEN}"
        
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
