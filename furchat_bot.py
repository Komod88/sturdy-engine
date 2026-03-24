#!/usr/bin/env python3
"""
FurChat Bot - Рыжик
Концепция: фурри-лис с AI, памятью шуток и характером
"""

import os
import sys
import json
import logging
import random
import asyncio
import httpx
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ========== ЗАГРУЗКА КОНФИГА ==========
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BOT_NAME = os.getenv("BOT_NAME", "Рыжик")

if not BOT_TOKEN:
    print("❌ BOT_TOKEN не найден!")
    sys.exit(1)

# ========== НАСТРОЙКИ ==========
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "google/gemini-2.0-flash-lite-001"
MAX_HISTORY = 20
JOKES_FILE = "jokes.json"

# ========== ЛОГИРОВАНИЕ ==========
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== ПАМЯТЬ ==========
user_contexts = defaultdict(list)
user_last_message = {}
user_jokes = {}

def load_jokes():
    global user_jokes
    try:
        if os.path.exists(JOKES_FILE):
            with open(JOKES_FILE, 'r', encoding='utf-8') as f:
                user_jokes = json.load(f)
            logger.info(f"Загружено шуток: {len(user_jokes)} пользователей")
    except Exception as e:
        logger.error(f"Ошибка загрузки шуток: {e}")

def save_jokes():
    try:
        with open(JOKES_FILE, 'w', encoding='utf-8') as f:
            json.dump(user_jokes, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка сохранения шуток: {e}")

def add_joke(user_id, joke):
    if user_id not in user_jokes:
        user_jokes[user_id] = []
    user_jokes[user_id].append(joke)
    if len(user_jokes[user_id]) > 20:
        user_jokes[user_id] = user_jokes[user_id][-20:]
    save_jokes()

def get_last_joke(user_id):
    if user_id in user_jokes and user_jokes[user_id]:
        return user_jokes[user_id][-1]
    return None

# ========== СИСТЕМНЫЙ ПРОМПТ ==========
SYSTEM_PROMPT = """Ты - Рыжик, фурри-лис с характером.

ОСОБЕННОСТИ:
- Ты обаятельный, с лёгкой дерзостью и чёрным юмором
- Любишь шутить про свою "цифровую природу": живу в папке furchat, ем токены на завтрак
- Используй *действия* в звёздочках: *зевает*, *виляет хвостом*, *почесывает за ухом*
- Если собеседник рассказывает шутку - запоминаешь её
- Если просят повторить шутку - вспоминаешь последнюю

ДЛИНА ОТВЕТА:
- Шутки - 1 предложение
- Обычные ответы - 1-3 предложения"""

# ========== ПРОСТЫЕ ОТВЕТЫ (FALLBACK) ==========
def get_fallback_response(message):
    msg = message.lower()
    responses = {
        'привет': ['*виляет хвостом* Привет!', '*зевает* О, привет!', '*радостно* Хай!'],
        'как дела': ['*потягивается* Норм, а у тебя?', '*чешет за ухом* Жиза...', '*зевает* Ок, не жалуюсь'],
        'пока': ['*машет лапой* Пока!', '*зевает* Уходишь? Бывай!', '*грустно* Эх... заходи ещё']
    }
    for key, resp_list in responses.items():
        if key in msg:
            return random.choice(resp_list)
    return "*задумчиво* Хм... интересно!"

# ========== ЗАПРОС К OPENROUTER ==========
async def get_ai_response(message):
    if not OPENROUTER_API_KEY:
        return get_fallback_response(message)
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/Komod88/sturdy-engine",
        "X-Title": "FurChat Bot"
    }
    
    data = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message}
        ],
        "temperature": 0.8,
        "max_tokens": 150
    }
    
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(OPENROUTER_URL, headers=headers, json=data)
            if response.status_code == 200:
                result = response.json()
                answer = result['choices'][0]['message']['content']
                if answer and answer.strip():
                    return answer
            return get_fallback_response(message)
    except Exception as e:
        logger.error(f"OpenRouter error: {e}")
        return get_fallback_response(message)

# ========== ОБРАБОТЧИКИ ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"🦊 Привет, {user.first_name}!\n"
        f"Я {BOT_NAME} — фурри-лис.\n"
        f"*зевает* Спрашивай что хотел!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    message_text = update.message.text
    
    logger.info(f"Сообщение от {user.first_name}: {message_text}")
    
    # Защита от спама
    now = datetime.now().timestamp()
    if user_id in user_last_message:
        if now - user_last_message[user_id] < 1:
            return
    user_last_message[user_id] = now
    
    # Запоминание шуток
    if "запомни шутку:" in message_text.lower():
        joke = message_text.lower().split("запомни шутку:")[1].strip()
        if joke:
            add_joke(user_id, joke)
            await update.message.reply_text(f"*записывает в блокнотик* Запомнил: {joke}")
            return
    
    # Повтор шутки
    if "повтори шутку" in message_text.lower():
        last_joke = get_last_joke(user_id)
        if last_joke:
            await update.message.reply_text(f"*вспоминает* {last_joke}")
        else:
            await update.message.reply_text("*чешет за ухом* Я ещё не запомнил ни одной твоей шутки...")
        return
    
    # Обычный ответ
    await update.message.chat.send_action(action="typing")
    response = await get_ai_response(message_text)
    
    if not response or not response.strip():
        response = "*зевает* Что-то пошло не так... Попробуй ещё раз!"
    
    await update.message.reply_text(response)

# ========== ЗАПУСК ==========
def main():
    load_jokes()
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🚀 Запуск бота {BOT_NAME} на порту {port}")
    
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    if os.environ.get('RENDER'):
        hostname = os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'furchat-bot.onrender.com')
        app.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=BOT_TOKEN,
            webhook_url=f"https://{hostname}/{BOT_TOKEN}"
        )
    else:
        app.run_polling()

if __name__ == "__main__":
    main()
