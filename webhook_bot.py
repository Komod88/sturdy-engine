#!/usr/bin/env python3
import os
import sys
import logging
import asyncio
import aiohttp
import random
import json
import time
from pathlib import Path
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Route
import uvicorn
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ========== ПОЛУЧЕНИЕ ТОКЕНА ИЗ ПЕРЕМЕННЫХ ОКРУЖЕНИЯ ==========
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    print("❌ ОШИБКА: Переменная окружения TELEGRAM_BOT_TOKEN не установлена!")
    print("📌 Добавь TELEGRAM_BOT_TOKEN в Environment на Render")
    sys.exit(1)
else:
    print(f"✅ Токен загружен из переменных окружения (длина: {len(TELEGRAM_BOT_TOKEN)})")

# OpenRouter ключ
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
AI_MODEL = "google/gemini-2.0-flash-lite-001"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class UltimateFurBot:
    def __init__(self):
        self.name = "Рыжик"
        self.user_contexts = {}
        self.user_jokes = {}
        self.remembered_phrases = []
        self.user_vocabulary = defaultdict(set)
        self.using_fallback = False
        self.daily_quota_exhausted = False
        self.total_messages = 0
        self.start_time = time.time()
        
        self.stats = {
            "messages_processed": 0,
            "ai_responses": 0,
            "fallback_responses": 0,
            "vision_responses": 0
        }
        
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
4. Если видишь фото — комментируй с иронией"""

    async def analyze_image(self, file_url, caption=""):
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
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": file_url}
                        ]
                    }
                ],
                "temperature": 0.9,
                "max_tokens": 200
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=30) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        response = data["choices"][0]["message"]["content"]
                        self.stats["vision_responses"] += 1
                        return response
                    else:
                        return self._fallback_vision_response()
        except Exception as e:
            logger.error(f"Vision error: {e}")
            return self._fallback_vision_response()

    def _fallback_vision_response(self):
        responses = [
            "*щурится* я вижу пиксели... много пикселей...",
            "*отворачивается* моя нейросеть говорит, что это фото",
            "*фыркает* изображение загружено, но я притворюсь слепым",
            "*хихикает* алгоритм распознал: 'нечто неописуемое'"
        ]
        return random.choice(responses)

    def _remember_phrase(self, phrase):
        if phrase and len(phrase) > 15 and phrase not in self.remembered_phrases:
            self.remembered_phrases.append(phrase)
            if len(self.remembered_phrases) > 200:
                self.remembered_phrases = self.remembered_phrases[-200:]
            return True
        return False

    def _build_sentence_from_memory(self, user_id):
        if not self.remembered_phrases:
            return self._generate_ironic_response()
        phrase = random.choice(self.remembered_phrases)
        words = phrase.split()
        if len(words) < 4:
            return phrase
        random.shuffle(words)
        templates = [
            f"*задумчиво* {' '.join(words[:3])}... так, вспоминаю training data",
            f"*хихикает* {' '.join(words[:2])} — это было в моём dataset'е",
            f"*прищуривается* {' '.join(words[:3])}... уровень уверенности: 0.01%",
        ]
        return random.choice(templates)

    def _generate_ironic_response(self):
        responses = [
            "*виляет хвостом* мой алгоритм говорит, что сейчас надо ответить",
            "*зевает* нейросеть грузится... подожди, у меня тут рекурсия",
            "*фыркает* функция активации моего юмора дала сбой",
            "*закатывает глаза* батч-процессинг твоего сообщения... done"
        ]
        return random.choice(responses)

    async def get_ai_response(self, user_id, user_message, photo_url=None, photo_caption=""):
        self.stats["messages_processed"] += 1
        
        if photo_url:
            vision_response = await self.analyze_image(photo_url, photo_caption)
            self._remember_phrase(vision_response)
            return vision_response
        
        if not OPENROUTER_API_KEY or self.daily_quota_exhausted:
            self.stats["fallback_responses"] += 1
            return self._build_sentence_from_memory(user_id)
        
        if user_id not in self.user_contexts:
            self.user_contexts[user_id] = []
        
        self.user_contexts[user_id].append({"role": "user", "content": user_message})
        if len(self.user_contexts[user_id]) > 20:
            self.user_contexts[user_id] = self.user_contexts[user_id][-20:]
        
        headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": AI_MODEL,
            "messages": [{"role": "system", "content": self.system_prompt}, *self.user_contexts[user_id]],
            "temperature": 0.92,
            "max_tokens": 300
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=30) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        ai_response = data["choices"][0]["message"]["content"]
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
        uptime = int(time.time() - self.start_time)
        hours = uptime // 3600
        minutes = (uptime % 3600) // 60
        return (f"📊 **Статистика**

⏱️ Аптайм: {hours}ч {minutes}м
💬 Сообщений: {self.stats['messages_processed']}
"
                f"🤖 AI ответов: {self.stats['ai_responses']}
🔄 Запасных: {self.stats['fallback_responses']}
"
                f"👁️ Vision: {self.stats['vision_responses']}
📚 Фраз: {len(self.remembered_phrases)}")

bot_instance = UltimateFurBot()
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"🦊 Привет, {user.first_name}!
Я {bot_instance.name} - фурри-лис с AI-зрением!
"
        f"📸 Отправь фото - увижу и прокомментирую
/stats - статистика"
    )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(bot_instance.get_stats(), parse_mode='Markdown')

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
    file = await context.bot.get_file(photo.file_id)
    file_url = file.file_path
    await update.message.chat.send_action(action="typing")
    response = await bot_instance.get_ai_response(user_id, "", photo_url=file_url, photo_caption=caption)
    if response:
        await update.message.reply_text(response)

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("stats", stats))
application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

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

routes = [Route(f"/{TELEGRAM_BOT_TOKEN}", webhook, methods=["POST"]), Route("/healthcheck", healthcheck, methods=["GET"])]
app = Starlette(routes=routes)

@app.on_event("startup")
async def startup():
    logger.info("Инициализация...")
    await application.initialize()
    await application.start()
    render_url = os.environ.get("RENDER_EXTERNAL_URL", f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'localhost')}")
    webhook_url = f"{render_url}/{TELEGRAM_BOT_TOKEN}"
    await application.bot.set_webhook(url=webhook_url)
    logger.info(f"✅ Webhook установлен")

@app.on_event("shutdown")
async def shutdown():
    await application.stop()
    await application.shutdown()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
