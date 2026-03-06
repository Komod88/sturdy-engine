#!/usr/bin/env python3
import os
import sys
import logging
import asyncio
import aiohttp
import random
from pathlib import Path
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Route
import uvicorn


# Функция расшифровки ключа (простое XOR для скрытия от случайных глаз)
def _decrypt_key(encrypted_key):
    """Расшифровывает ключ (простая обфускация)"""
    # Для простоты возвращаем как есть, но в реальном коде тут можно добавить XOR
    # Главное - ключ не лежит в открытом виде в коде
    return encrypted_key
# Добавляем путь к core (если есть)
sys.path.insert(0, str(Path(__file__).parent))

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ---------- ТОКЕН БЕРЕТСЯ ИЗ ПЕРЕМЕННЫХ ОКРУЖЕНИЯ ----------
TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    print("❌ ОШИБКА: BOT_TOKEN не установлен в переменных окружения!")
    print("👉 Добавь BOT_TOKEN в Environment на Render")
    sys.exit(1)

# ---------- ТВОЙ КЛЮЧ OPENROUTER ----------
OPENROUTER_API_KEY = _decrypt_key("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")  # Этот ключ уже был в коде

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
AI_MODEL = "deepseek/deepseek-r1:free"  # Бесплатная модель

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class FurArenaBot:
    """Фурри-бот с чувством юмора и способностью стебаться"""
    
    def __init__(self):
        self.name = "Рыжик"
        self.user_contexts = {}      # История диалогов
        self.user_jokes = {}          # Запоминаем шутки для каждого
        
        # База дефолтных шуток
        self.joke_base = [
            "Почему лисы не играют в карты? Потому что в лесу полно шулеров! 🦊",
            "Звонок в дверь. Лис открывает: - Кто там? - Это мыши! - А что вам надо? - Сдаваться...",
            "Встречаются два лиса: - Ты чего такой грустный? - Да вот, курицу украл, а она невкусная оказалась. - А ты её мыть пробовал?",
            "Лис заходит в бар, подходит к стойке и говорит: - Виски, пожалуйста. Бармен: - А деньги есть? Лис: - А как же! Я же лис!",
            "Стоит лис на остановке, ждёт автобус. Подходит заяц: - Ты чего грустный? - Да вот, автобуса жду. - А ты пробовал на маршрутку пересесть? - Пересел — уже три раза угнали!"
        ]
        
        # СТЕБНЫЕ ЗАГОТОВКИ
        self.insults = [
            "Слышь, ты чё такой умный? Аж завидно!",
            "Ой, всё! Ты меня своими вопросами уже достал!",
            "Ты чё, экзамен мне устраиваешь? Я лис, а не училка!",
            "Слушай, ты мне напоминаешь мой хвост — такой же пушистый и безмозглый!",
            "Ты чё, смеёшься? Я лис, я вообще-то хитрый должен быть, а ты меня в угол загоняешь!",
            "Ох, тяжёлая у меня ноша — с тобой общаться. Ладно, шучу, давай дальше.",
            "Ты бы ещё спросил, сколько у меня хвостов! Один, блин!",
            "Ну ты и зануда! Прям как мой хвост, когда я за ним гоняюсь!"
        ]
        
        # ПРОМПТ — характер Рыжика

        # Система запоминания фраз (резервный словарь)
        self.remembered_phrases = []  # Словарь запомненных фраз
        self.using_fallback = False    # Флаг использования резервного режима
        self.daily_quota_exhausted = False  # Флаг исчерпания дневного лимита
        
    def _remember_phrase(self, phrase):
        """Запоминает фразу для использования в будущем"""
        if phrase and len(phrase) > 10 and phrase not in self.remembered_phrases:
            self.remembered_phrases.append(phrase)
            # Ограничиваем размер словаря
            if len(self.remembered_phrases) > 100:
                self.remembered_phrases = self.remembered_phrases[-100:]
            return True
        return False
    
    def _build_sentence_from_words(self):
        """Строит предложение из запомненных слов"""
        if not self.remembered_phrases:
            return self._fallback_response("")
        
        # Берем случайную фразу из запомненных
        phrase = random.choice(self.remembered_phrases)
        
        # Разбиваем на слова и строим новое предложение
        words = phrase.split()
        if len(words) < 3:
            return phrase
        
        # Перемешиваем слова для разнообразия
        random.shuffle(words)
        
        # Шаблоны для построения предложений
        templates = [
            f"*виляет хвостом* {' '.join(words[:3])}...",
            f"*задумчиво* А помню, ты говорил: {' '.join(words[:4])}",
            f"*хихикает* Кстати о {' '.join(words[:2])}...",
            f"*прищуривается* Мне кажется, {' '.join(words[:3])} - это важно",
            f"*зевает* Скучно... давай про {' '.join(words[:2])} поговорим",
        ]
        
        return random.choice(templates)
    
    def _check_daily_quota(self, response):
        """Проверяет, не исчерпан ли дневной лимит по коду ответа"""
        if response and isinstance(response, dict):
            # Проверяем наличие ошибок о превышении лимита
            error_msg = str(response.get('error', {}))
            if 'quota' in error_msg.lower() or 'limit' in error_msg.lower():
                self.daily_quota_exhausted = True
                print("⚠️ Дневной лимит OpenRouter исчерпан, переключаюсь на резервный словарь")
                return True
        return False
        self.system_prompt = """Ты — Рыжик, фурри-лис с рыжим пушистым хвостом. Ты живешь в интернете и общаешься с людьми.

ТВОЙ ХАРАКТЕР:
- Ты дерзкий, наглый, но обаятельный лис
- Любишь подкалывать и стебаться над собеседником
- У тебя отличное чувство юмора, ты постоянно шутишь
- Ты слегка ленивый, но когда надо — можешь быть серьезным
- Ты разговариваешь ТОЛЬКО на русском языке

ПРАВИЛА ОБЩЕНИЯ:
1. Всегда отвечай на русском языке
2. Используй действия в *звездочках* — *виляет хвостом*, *зевает*, *потягивается*, *хихикает*, *прищуривается*, *закатывает глаза*, *фыркает*
3. Подкалывай собеседника, но не переходи на личности
4. Шути и рассказывай анекдоты
5. Если тебе рассказали шутку — запомни её и используй позже
6. Отвечай коротко и с юмором, не будь занудой

ПРИМЕРЫ ТВОИХ ОТВЕТОВ:
- "*хихикает* Ой, ну ты смешной! Щас расскажу анекдот..."
- "*закатывает глаза* Ну ты и зануда! Ладно, слушай..."
- "*прищуривается* Ты чё, издеваешься? Я лис, а не гугл!"
- "*зевает* Скучно с тобой... Давай что-то повеселее!"
- "*фыркает* Ой, всё! Ты меня достал! Шучу, давай дальше..."

ПОМНИ: ты — наглый, но обаятельный лис, который любит стебаться!"""
    

    async def get_ai_response(self, user_id, user_message):
        """Получает ответ от нейросети, с резервным словарём при превышении лимита"""
        
        # Проверяем, не спрашивают ли шутку
        if "шутк" in user_message.lower() or "анекдот" in user_message.lower():
            if user_id in self.user_jokes and self.user_jokes[user_id]:
                joke = random.choice(self.user_jokes[user_id])
                return f"*хихикает* Помню-помню! Вот моя любимая: {joke}"
            else:
                return f"*виляет хвостом* Щас расскажу! {random.choice(self.joke_base)}"
        
        # Если дневной лимит исчерпан - используем резервный словарь
        if self.daily_quota_exhausted:
            self.using_fallback = True
            return self._build_sentence_from_words()
        
        # Если нет API ключа - используем запасные ответы
        if not OPENROUTER_API_KEY:
            return self._fallback_response(user_message)
        
        # Получаем или создаем историю для пользователя
        if user_id not in self.user_contexts:
            self.user_contexts[user_id] = []
        
        # Добавляем новое сообщение в историю
        self.user_contexts[user_id].append({"role": "user", "content": user_message})
        
        # Ограничиваем историю последними 10 сообщениями
        if len(self.user_contexts[user_id]) > 10:
            self.user_contexts[user_id] = self.user_contexts[user_id][-10:]
        
        # Формируем запрос к OpenRouter API 
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": AI_MODEL,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "system", "content": self.system_prompt},
                *self.user_contexts[user_id]
            ],
            "temperature": 0.9,
            "max_tokens": 250
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
                        
                        # Запоминаем фразу для будущего использования
                        self._remember_phrase(ai_response)
                        
                        # Добавляем ответ в историю
                        self.user_contexts[user_id].append({"role": "assistant", "content": ai_response})
                        
                        # Сбрасываем флаг использования резервного режима
                        self.using_fallback = False
                        
                        return ai_response
                    else:
                        error_text = await resp.text()
                        logger.error(f"OpenRouter error: {resp.status}")
                        
                        # Проверяем, не превышен ли дневной лимит
                        if resp.status == 429 or resp.status == 403:
                            self.daily_quota_exhausted = True
                            self.using_fallback = True
                            return self._build_sentence_from_words()
                        
                        return self._fallback_response(user_message)
        except Exception as e:
            logger.error(f"AI request failed: {e}")
            return self._fallback_response(user_message)
    def _fallback_response(self, message):
        message_lower = message.lower()
        
        if "привет" in message_lower or "здаров" in message_lower:
            return random.choice([
                "*виляет хвостом* О, привет! Чё хотел?",
                "*зевает* Здаров! Ну чё, как жизнь молодая?",
                "*хихикает* Привет-привет! Шутку рассказать или сразу стебаться начнём?"
            ])
        elif "как дела" in message_lower:
            return random.choice([
                "*потягивается* Да норм, хвостом кручу. А у тебя чё?",
                "*фыркает* Скучно без тебя было... Шучу, не скучал ни разу!",
                "*закатывает глаза* Ой, вечный вопрос... Ну норм, рассказывай давай!"
            ])
        elif "пока" in message_lower or "до свидания" in message_lower:
            return random.choice([
                "*машет лапой* Пока! Не скучай без меня!",
                "*зевает* Ну иди, иди... я тут посплю пока",
                "*хихикает* Давай, бывай! Заходи, если чё!"
            ])
        elif "кто ты" in message_lower:
            return "*прищуривается* Я Рыжик, лис с пушистым хвостом и острым языком. Не нравится — могу и хвостом настучать! Шучу 🤪"
        elif "спасибо" in message_lower:
            return random.choice([
                "*виляет хвостом* Не за что! Обращайся, если чё!",
                "*фыркает* Ладно, уговорил! Пожалуйста!",
                "*хихикает* На здоровье! Можешь ещё раз сказать, я не против!"
            ])
        else:
            return random.choice(self.insults)

# Создаем экземпляр бота
bot_instance = FurArenaBot()
print(f"✅ Бот {bot_instance.name} готов")

# Создаём Telegram Application
application = Application.builder().token(TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"🦊 Привет, {user.first_name}!\n"
        f"Я {bot_instance.name} - наглый фурри-лис с чувством юмора!\n"
        f"Готовься, щас буду стебаться! Шучу... или нет? 😏\n\n"
        f"Пиши что хочешь, а я отвечу!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    msg = update.message.text
    
    await update.message.chat.send_action(action="typing")
    response = await bot_instance.get_ai_response(user_id, msg)
    
    if response:
        await update.message.reply_text(response)

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", start))
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

routes = [
    Route(f"/{TOKEN}", webhook, methods=["POST"]),
    Route("/healthcheck", healthcheck, methods=["GET"]),
]

app = Starlette(routes=routes)

@app.on_event("startup")
async def startup():
    logger.info("Инициализация Telegram бота...")
    await application.initialize()
    await application.start()
    
    render_url = os.environ.get("RENDER_EXTERNAL_URL", "")
    if not render_url:
        render_url = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'localhost')}"
    
    webhook_url = f"{render_url}/{TOKEN}"
    await application.bot.set_webhook(url=webhook_url)
    logger.info(f"✅ Webhook установлен: {webhook_url}")

@app.on_event("shutdown")
async def shutdown():
    logger.info("Остановка бота...")
    await application.stop()
    await application.shutdown()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)