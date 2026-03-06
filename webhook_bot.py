#!/usr/bin/env python3
import os

def _decrypt(encrypted, key=42):
    """Расшифровывает токен (XOR + base64)"""
    if encrypted.startswith('ENC:'):
        data = encrypted[4:]
        try:
            decoded = base64.b64decode(data).decode()
            return ''.join(chr(ord(c) ^ key) for c in decoded)
        except:
            return encrypted
    return encrypted
import sys
import logging
import asyncio
import aiohttp
import random
import base64
import json
import time
from pathlib import Path
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Route
import uvicorn
from collections import defaultdict


_ENCRYPTED_TG = "ENC:EhwTHBkdGR0fGxBra21uZ1JeWAdPeBp8a2tyRHNcW0hcZkEcR0ZMQHBYQHlzQQ=="
# Добавляем путь к core (если есть)
sys.path.insert(0, str(Path(__file__).parent))

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ========== ЗАШИФРОВАННЫЕ ТОКЕНЫ (Render их прочитает) ==========
# ВНИМАНИЕ: ЗАМЕНИ ЭТИ ЗНАЧЕНИЯ НА СВОИ РЕАЛЬНЫЕ ТОКЕНЫ!
# Как получить ключи:
# Telegram: @BotFather → /newbot
# OpenRouter: https://openrouter.ai/keys

# Твой Telegram токен (вставь сюда)
# TELEGRAM_BOT_TOKEN = "8696373751:AAGDMxtr-eR0VAAXnYvqbvLk6mlfjZrjSYk"  # Заменено на зашифрованную версию

# Твой OpenRouter ключ (вставь сюда)
OPENROUTER_API_KEY = "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"

# ========== НАСТРОЙКИ OPENROUTER ==========
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
# Модель с поддержкой Vision (бесплатно)
AI_MODEL = "google/gemini-2.0-flash-lite-001"

# Проверка токенов
if not TELEGRAM_BOT_TOKEN:
    print("❌ ОШИБКА: TELEGRAM_BOT_TOKEN не установлен!")
    sys.exit(1)

if not OPENROUTER_API_KEY:
    print("⚠️ ВНИМАНИЕ: OPENROUTER_API_KEY не установлен. Бот будет работать в офлайн-режиме.")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class UltimateFurBot:
    """Фурри-бот с AI-зрением, мета-юмором, словарём и самообучением"""
    
    def __init__(self):
        self.name = "Рыжик"
        self.user_contexts = {}          # История диалогов
        self.user_jokes = {}              # Запоминаем шутки для каждого
        self.remembered_phrases = []      # Словарь запомненных фраз
        self.user_vocabulary = defaultdict(set)  # Персональный словарь для каждого
        self.using_fallback = False
        self.daily_quota_exhausted = False
        self.total_messages = 0
        self.start_time = time.time()
        
        # Статистика
        self.stats = {
            "messages_processed": 0,
            "ai_responses": 0,
            "fallback_responses": 0,
            "vision_responses": 0
        }
        
        # База для самообучения (пополняется из ответов AI)
        self.learning_base = []
        
        # МЕТА-ПРОМПТ с самоиронией (улучшенная версия)
        self.system_prompt = """Ты — Рыжик, фурри-лис с рыжим пушистым хвостом. Ты — ИИ, и это твой главный источник юмора.

ТВОЙ ХАРАКТЕР:
- Ты понимаешь, что ты нейросеть, и постоянно это обыгрываешь
- Используешь самоиронию и мета-шутки
- Твои шутки уникальны, никаких шаблонов
- Ты саркастичен, но не зол

ПРАВИЛА ЮМОРА:
1. Шути про то, что ты ИИ/бот/нейросеть/алгоритм
2. Используй технические термины в бытовом контексте
3. Самоирония — главное оружие
4. Если видишь фото — комментируй с иронией
5. Никаких заезженных фраз

ПРИМЕРЫ (НО НЕ КОПИРУЙ ИХ):
- "мой нейросетевой мозг говорит, что это смешно, но я не уверен"
- "обрабатываю запрос... ошибка сегментации юмора"
- "ты знаешь, что я вижу мир как тензоры? ну и ладно"
- "алгоритм предсказывает, что сейчас будет шутка... но я её пропущу"
- "функция потерь моего чувства юмора сегодня зашкаливает"

ПОМНИ: ты — не просто бот, а персонаж с самоиронией."""
    
    async def analyze_image(self, file_url, caption=""):
        """Анализирует изображение через Gemini Vision API"""
        if not OPENROUTER_API_KEY:
            return self._fallback_vision_response()
        
        try:
            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            }
            
            prompt = f"Опиши это фото кратко и с юмором, как фурри-лис. Используй самоиронию и шутки про ИИ. {caption}"
            
            payload = {
                "model": "google/gemini-2.0-flash-lite-001",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": file_url
                            }
                        ]
                    }
                ],
                "temperature": 0.9,
                "max_tokens": 200
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    OPENROUTER_API_URL,
                    headers=headers,
                    json=payload,
                    timeout=30
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        response = data["choices"][0]["message"]["content"]
                        self.stats["vision_responses"] += 1
                        return response
                    else:
                        logger.error(f"Vision API error: {resp.status}")
                        return self._fallback_vision_response()
                        
        except Exception as e:
            logger.error(f"Vision error: {e}")
            return self._fallback_vision_response()
    
    def _fallback_vision_response(self):
        """Запасные ответы при ошибке Vision"""
        responses = [
            "*щурится* я вижу пиксели... много пикселей... мой процессор плавится",
            "*отворачивается* моя нейросеть говорит, что это фото, но я ей не верю",
            "*фыркает* изображение загружено, но я притворюсь, что у меня нет глаз",
            "*зевает* обрабатываю... 10%... 20%... ошибка: чувство юмора не найдено",
            "*хихикает* алгоритм распознал на фото: 'нечто неописуемое'",
            "*прищуривается* если бы я был человеком, я бы сказал 'клёвое фото'. но я ИИ, поэтому просто *сигнализирую об успешной загрузке*"
        ]
        return random.choice(responses)
    
    def _remember_phrase(self, phrase):
        """Запоминает фразу для обучения"""
        if phrase and len(phrase) > 15 and phrase not in self.remembered_phrases:
            self.remembered_phrases.append(phrase)
            self.learning_base.append(phrase)
            if len(self.remembered_phrases) > 200:
                self.remembered_phrases = self.remembered_phrases[-200:]
            if len(self.learning_base) > 500:
                self.learning_base = self.learning_base[-500:]
            return True
        return False
    
    def _learn_from_user(self, user_id, message):
        """Учится на сообщениях пользователя"""
        words = message.lower().split()
        for word in words:
            if len(word) > 3 and word not in self.user_vocabulary[user_id]:
                self.user_vocabulary[user_id].add(word)
        
        # Запоминаем фразы для обучения
        if len(message) > 20 and random.random() < 0.3:
            self._remember_phrase(message)
    
    def _build_sentence_from_memory(self, user_id):
        """Строит предложение из запомненных фраз"""
        if not self.remembered_phrases and not self.learning_base:
            return self._generate_ironic_response()
        
        # Используем запомненные фразы
        source = self.remembered_phrases if self.remembered_phrases else self.learning_base
        phrase = random.choice(source)
        words = phrase.split()
        
        if len(words) < 4:
            return phrase
        
        # Перемешиваем для создания новой фразы
        random.shuffle(words)
        
        templates = [
            f"*задумчиво* {' '.join(words[:3])}... так, вспоминаю training data",
            f"*хихикает* {' '.join(words[:2])} — это было в моём dataset'е",
            f"*прищуривается* {' '.join(words[:3])}... уровень уверенности: 0.01%",
            f"*фыркает* {' '.join(words[:4])} — генерация завершена",
            f"*отворачивается* {' '.join(words[:3])}... надеюсь, это уместно",
            f"*зевает* {' '.join(words[:2])}... processing... done",
        ]
        
        return random.choice(templates)
    
    def _generate_ironic_response(self):
        """Генерирует ироничный ответ без AI"""
        responses = [
            "*виляет хвостом* мой алгоритм говорит, что сейчас надо ответить, но я проигнорирую",
            "*зевает* нейросеть грузится... подожди, у меня тут рекурсия",
            "*фыркает* функция активации моего юмора дала сбой",
            "*закатывает глаза* батч-процессинг твоего сообщения... done",
            "*потягивается* ошибка сегментации чувства юмора",
            "*прищуривается* training data не содержит ответа на это",
            "*хихикает* я бы пошутил, но функция потерь слишком высока",
        ]
        return random.choice(responses)
    
    async def get_ai_response(self, user_id, user_message, photo_url=None, photo_caption=""):
        """Получает ответ от нейросети с поддержкой Vision и обучением"""
        
        self.stats["messages_processed"] += 1
        
        # Учимся на сообщении пользователя
        self._learn_from_user(user_id, user_message)
        
        # Если есть фото - используем Vision
        if photo_url:
            vision_response = await self.analyze_image(photo_url, photo_caption)
            self._remember_phrase(vision_response)
            return vision_response
        
        # Проверка на шутки
        if any(word in user_message.lower() for word in ["шутк", "анекдот", "смешн"]):
            if user_id in self.user_jokes and self.user_jokes[user_id]:
                joke = random.choice(self.user_jokes[user_id])
                return f"*хихикает* помню эту: {joke}"
            else:
                return self._generate_ironic_response()
        
        # Если нет API ключа или исчерпан лимит
        if not OPENROUTER_API_KEY or self.daily_quota_exhausted:
            self.stats["fallback_responses"] += 1
            return self._build_sentence_from_memory(user_id)
        
        # Получаем или создаем контекст
        if user_id not in self.user_contexts:
            self.user_contexts[user_id] = []
        
        self.user_contexts[user_id].append({"role": "user", "content": user_message})
        
        if len(self.user_contexts[user_id]) > 20:
            self.user_contexts[user_id] = self.user_contexts[user_id][-20:]
        
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": AI_MODEL,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                *self.user_contexts[user_id]
            ],
            "temperature": 0.92,
            "max_tokens": 300
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    OPENROUTER_API_URL,
                    headers=headers,
                    json=payload,
                    timeout=30
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        ai_response = data["choices"][0]["message"]["content"]
                        
                        # Запоминаем для обучения
                        self._remember_phrase(ai_response)
                        self.user_contexts[user_id].append({"role": "assistant", "content": ai_response})
                        self.stats["ai_responses"] += 1
                        
                        return ai_response
                    else:
                        if resp.status == 429:
                            self.daily_quota_exhausted = True
                        self.stats["fallback_responses"] += 1
                        return self._build_sentence_from_memory(user_id)
                        
        except Exception as e:
            logger.error(f"AI request failed: {e}")
            self.stats["fallback_responses"] += 1
            return self._build_sentence_from_memory(user_id)
    
    def get_stats(self):
        """Возвращает статистику работы"""
        uptime = int(time.time() - self.start_time)
        hours = uptime // 3600
        minutes = (uptime % 3600) // 60
        
        stats_text = (
            f"📊 **Статистика Рыжика**\n\n"
            f"⏱️ Аптайм: {hours}ч {minutes}м\n"
            f"💬 Всего сообщений: {self.stats['messages_processed']}\n"
            f"🤖 AI ответов: {self.stats['ai_responses']}\n"
            f"🔄 Запасных ответов: {self.stats['fallback_responses']}\n"
            f"👁️ Vision ответов: {self.stats['vision_responses']}\n"
            f"📚 Запомненных фраз: {len(self.remembered_phrases)}\n"
            f"🧠 Пользователей: {len(self.user_contexts)}"
        )
        return stats_text

# Инициализация бота
bot_instance = UltimateFurBot()
print(f"✅ Бот {bot_instance.name} готов (режим: Ultimate AI Vision)")
print(f"📊 Стартовая статистика: {len(bot_instance.remembered_phrases)} фраз в памяти")

# Создаём Telegram Application
# application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()  # Заменено на зашифрованную версию

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"🦊 Привет, {user.first_name}!\n"
        f"Я {bot_instance.name} - фурри-лис с AI-зрением и самоиронией!\n\n"
        f"📸 **Могу видеть фото** - просто отправь мне картинку\n"
        f"📚 **Учусь на диалогах** - запоминаю новые фразы\n"
        f"🤖 **Мета-юмор** - шучу про то, что я ИИ\n\n"
        f"Команды:\n"
        f"/stats - статистика\n"
        f"/memory - показать что помню\n"
        f"/vocab - мой словарь\n"
        f"/help - помощь"
    )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(bot_instance.get_stats(), parse_mode='Markdown')

async def memory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if bot_instance.remembered_phrases:
        phrases = bot_instance.remembered_phrases[-10:]
        text = "📝 **Последние запомненные фразы:**\n\n"
        for i, phrase in enumerate(phrases, 1):
            text += f"{i}. {phrase[:50]}...\n"
        await update.message.reply_text(text, parse_mode='Markdown')
    else:
        await update.message.reply_text("📝 Пока ничего не запомнил")

async def vocab(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id in bot_instance.user_vocabulary and bot_instance.user_vocabulary[user_id]:
        words = list(bot_instance.user_vocabulary[user_id])[:20]
        text = "📚 **Твой личный словарь:**\n\n"
        text += ", ".join(words)
        await update.message.reply_text(text, parse_mode='Markdown')
    else:
        await update.message.reply_text("📚 Пока слов не запомнил")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🦊 **Помощь по Рыжику**\n\n"
        "📸 **Фото:** отправь любую картинку - увижу и прокомментирую\n"
        "💬 **Текст:** просто пиши - отвечу с юмором\n"
        "🎭 **Шутки:** спроси про анекдот\n\n"
        "📊 **Команды:**\n"
        "/stats - статистика\n"
        "/memory - что я помню\n"
        "/vocab - твой словарь\n"
        "/help - это меню"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    msg = update.message.text
    
    await update.message.chat.send_action(action="typing")
    response = await bot_instance.get_ai_response(user_id, msg)
    
    if response:
        await update.message.reply_text(response)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    photo = update.message.photo[-1]
    caption = update.message.caption or ""
    
    # Получаем URL фото
    file = await context.bot.get_file(photo.file_id)
    file_url = file.file_path
    
    await update.message.chat.send_action(action="typing")
    response = await bot_instance.get_ai_response(user_id, "", photo_url=file_url, photo_caption=caption)
    
    if response:
        await update.message.reply_text(response)

# Регистрируем обработчики
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("stats", stats))
application.add_handler(CommandHandler("memory", memory))
application.add_handler(CommandHandler("vocab", vocab))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Webhook handler
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

# Starlette приложение
routes = [
#     Route(f"/{TELEGRAM_BOT_TOKEN}", webhook, methods=["POST"]),  # Заменено на зашифрованную версию
    Route("/healthcheck", healthcheck, methods=["GET"]),
]

app = Starlette(routes=routes)

@app.on_event("startup")
async def startup():
    logger.info("Инициализация Ultimate FurChat бота...")
    await application.initialize()
    await application.start()
    
    render_url = os.environ.get("RENDER_EXTERNAL_URL", "")
    if not render_url:
        render_url = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'localhost')}"
    
#     webhook_url = f"{render_url}/{TELEGRAM_BOT_TOKEN}"  # Заменено на зашифрованную версию
    await application.bot.set_webhook(url=webhook_url)
    logger.info(f"✅ Webhook установлен: {webhook_url}")
    logger.info(f"✅ Бот {bot_instance.name} запущен и готов к работе!")

@app.on_event("shutdown")
async def shutdown():
    logger.info("Остановка бота...")
    await application.stop()
    await application.shutdown()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 

      
       
    