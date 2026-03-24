#!/usr/bin/env python3
"""
FurChat Bot - Исправленный
"""

import os
import sys
import logging
import random
import asyncio
import httpx
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = "8696373751:AAEZZyJiE6nA65uWW99UZdFKnr356Tgg6as"
OPENROUTER_API_KEY = "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"
BOT_NAME = "Рыжик"

print(f"✅ Бот запущен: {BOT_NAME}")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def get_simple_response(message):
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

async def get_ai_response(message):
    if not OPENROUTER_API_KEY:
        return get_simple_response(message)
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/Komod88/sturdy-engine",
        "X-Title": "FurChat Bot"
    }
    data = {
        "model": "google/gemini-2.0-flash-lite-001",
        "messages": [
            {"role": "system", "content": "Ты - Рыжик, фурри-лис. Отвечай кратко и с юмором. Используй *действия* в звёздочках."},
            {"role": "user", "content": message}
        ],
        "temperature": 0.8,
        "max_tokens": 150
    }
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(url, headers=headers, json=data)
            if response.status_code == 200:
                result = response.json()
                answer = result['choices'][0]['message']['content']
                if answer and answer.strip():
                    return answer
            return get_simple_response(message)
    except Exception as e:
        logger.error(f"OpenRouter error: {e}")
        return get_simple_response(message)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"🦊 Привет, {user.first_name}!\n"
        f"Я {BOT_NAME} — фурри-лис.\n"
        f"*зевает* Спрашивай что хотел!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message_text = update.message.text
    logger.info(f"Сообщение от {user.first_name}: {message_text}")
    await update.message.chat.send_action(action="typing")
    response = await get_ai_response(message_text)
    if not response or not response.strip():
        response = "*зевает* Что-то пошло не так... Попробуй ещё раз!"
    try:
        await update.message.reply_text(response)
    except Exception as e:
        logger.error(f"Ошибка отправки: {e}")
        await update.message.reply_text("*зевает* Ошибка, но я жив!")

def main():
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🚀 Запуск бота {BOT_NAME} на порту {port}")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    try:
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
    except Exception as e:
        logger.error(f"Ошибка запуска: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
