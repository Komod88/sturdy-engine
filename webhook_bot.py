#!/usr/bin/env python3
"""
FurChat Bot - Умный фурри-лис с AI
Версия 2.0 - Исправленная
"""

import os
import sys
import json
import logging
import asyncio
import random
import httpx
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from dotenv import load_dotenv

# Telegram
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ========== ЗАГРУЗКА КОНФИГУРАЦИИ ==========
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BOT_NAME = os.getenv("BOT_NAME", "Рыжик")

if not BOT_TOKEN:
    print("❌ ОШИБКА: BOT_TOKEN не найден!")
    sys.exit(1)

# ========== НАСТРОЙКИ ==========
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "google/gemini-2.0-flash-lite-001"  # Бесплатная модель
MAX_HISTORY = 10
REQUEST_TIMEOUT = 30

# ========== ЛОГИРОВАНИЕ ==========
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== ПАМЯТЬ ДИАЛОГОВ ==========
user_contexts = defaultdict(list)
user_last_message = {}

# ========== СИСТЕМНЫЙ ПРОМПТ ==========
SYSTEM_PROMPT = """Ты - Рыжик, фурри-лис с ярким характером.
Особенности:
- Ты дружелюбный, слегка ленивый, но обаятельный
- Используй *действия* в звёздочках (например, *зевает*, *виляет хвостом*)
- Отвечай кратко (1-3 предложения)
- Можешь немного подкалывать, но доброжелательно
- Используй русский язык
- Иногда вставляй лисьи повадки"""

# ========== ОСНОВНАЯ ФУНКЦИЯ AI ==========
async def get_ai_response(user_id: str, message: str) -> str:
    """Получает ответ от OpenRouter AI с контекстом"""
    
    # Сохраняем сообщение в историю
    user_contexts[user_id].append({"role": "user", "content": message})
    if len(user_contexts[user_id]) > MAX_HISTORY * 2:
        user_contexts[user_id] = user_contexts[user_id][-MAX_HISTORY*2:]
    
    # Проверка ключа
    if not OPENROUTER_API_KEY:
        logger.error("❌ OPENROUTER_API_KEY не найден!")
        return "🦊 Ой, у меня временные трудности с доступом к мозгам..."
    
    # Формируем контекст для AI
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(user_contexts[user_id][-MAX_HISTORY:])
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/Komod88/sturdy-engine",
        "X-Title": "FurChat Bot",
    }
    
    data = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0.8,
        "max_tokens": 200
    }
    
    # Пробуем разные модели если первая не сработает
    models_to_try = [MODEL, "mistralai/mistral-7b-instruct", "openrouter/free"]
    
    for attempt, model in enumerate(models_to_try):
        try:
            data["model"] = model
            logger.info(f"🤖 Пробую модель: {model}")
            
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                response = await client.post(OPENROUTER_URL, headers=headers, json=data)
                
                if response.status_code == 200:
                    result = response.json()
                    answer = result['choices'][0]['message']['content']
                    
                    # Сохраняем ответ в историю
                    user_contexts[user_id].append({"role": "assistant", "content": answer})
                    
                    logger.info(f"✅ Успех! Модель: {model}")
                    return answer
                else:
                    logger.warning(f"⚠️ Модель {model} вернула {response.status_code}")
                    
        except httpx.TimeoutException:
            logger.warning(f"⏱️ Таймаут модели {model}")
        except Exception as e:
            logger.warning(f"⚠️ Ошибка модели {model}: {e}")
        
        await asyncio.sleep(1)
    
    # Если все модели не сработали - используем умный fallback
    logger.warning("⚠️ Все модели недоступны, использую умный fallback")
    return generate_smart_response(user_id, message)

# ========== УМНЫЙ FALLBACK ==========
def generate_smart_response(user_id: str, message: str) -> str:
    """Генерирует осмысленный ответ на основе истории диалога"""
    
    # Анализируем историю
    history = user_contexts[user_id]
    msg_lower = message.lower()
    
    # Ищем похожие сообщения в истории
    similar_responses = []
    for i, entry in enumerate(history):
        if entry["role"] == "user" and i + 1 < len(history):
            if history[i + 1]["role"] == "assistant":
                # Проверяем похожесть сообщений
                if any(word in entry["content"].lower() for word in msg_lower.split()):
                    similar_responses.append(history[i + 1]["content"])
    
    # Если нашли похожие - используем их
    if similar_responses:
        return random.choice(similar_responses)
    
    # Если нет истории - генерируем на основе ключевых слов
    responses = []
    
    if any(word in msg_lower for word in ['привет', 'здравствуй', 'хай', 'hello']):
        responses = [
            "*потягивается* О, привет! Давно не виделись!",
            "*зевает* Здарова! Чё нового?",
            "*виляет хвостом* Привет-привет! Как сам?"
        ]
    elif any(word in msg_lower for word in ['как дела', 'как ты', 'чё как']):
        responses = [
            "*зевает* Да норм, лежу, балдею... А у тебя как?",
            "*чешет за ухом* Жиза... Скучновато немного",
            "*потягивается* Лучше всех, а ты?"
        ]
    elif any(word in msg_lower for word in ['шутк', 'анекдот', 'смешно']):
        responses = [
            "*хихикает* Идёт программист по улице, видит дверь. Открывает... А там бесконечный цикл!",
            "*смеётся* Почему лисы не играют в карты? Потому что в лесу все волки — шулера!",
            "*ухмыляется* Звонок в техподдержку: - У меня компьютер не работает! - А вы пробовали его погладить?"
        ]
    elif any(word in msg_lower for word in ['пока', 'до свидания', 'bye']):
        responses = [
            "*машет лапой* Пока-пока! Заходи ещё!",
            "*зевает* Уже уходишь? Ну давай, бывай!",
            "*грустно* Эх, ладно... Возвращайся!"
        ]
    else:
        # Анализируем длину и структуру сообщения для более умного ответа
        words = msg_lower.split()
        if len(words) < 3:
            responses = [
                "*задумчиво чешет подбородок* Хм... интересно...",
                "*зевает* А? Чего?",
                "*виляет хвостом* Расскажи подробнее!"
            ]
        elif len(words) > 10:
            responses = [
                "*внимательно слушает* Много текста... Покороче можно?",
                "*кивает* Угу... И что дальше?",
                "*записывает в блокнотик* Любопытно..."
            ]
        else:
            responses = [
                "*прищуривается* И?",
                "*зевает* Ну и?",
                "*виляет хвостом* Рассказывай!"
            ]
    
    return random.choice(responses)

# ========== ОБРАБОТЧИКИ КОМАНД ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"🦊 Привет, {user.first_name}!"
"
        f"Я {BOT_NAME} - фурри-лис с искусственным интеллектом."
"
        f"Просто пиши мне, и поболтаем!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    message = update.message.text
    
    # Защита от спама
    now = datetime.now().timestamp()
    if user_id in user_last_message:
        if now - user_last_message[user_id] < 1:
            return
    user_last_message[user_id] = now
    
    # Печатаем...
    await update.message.chat.send_action(action="typing")
    
    # Получаем ответ
    response = await get_ai_response(user_id, message)
    await update.message.reply_text(response)

# ========== ЗАПУСК ==========
def main():
    print(f"🚀 Запуск {BOT_NAME} бота...")
    print(f"✅ Токен загружен (длина: {len(BOT_TOKEN)})")
    print(f"✅ OpenRouter API ключ: {'найден' if OPENROUTER_API_KEY else 'не найден'}")
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("✅ Обработчики зарегистрированы")
    print("🚀 Бот запускается...")
    
    app.run_polling()

if __name__ == "__main__":
    main()
