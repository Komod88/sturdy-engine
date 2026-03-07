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







# ========== НАСТРОЙКА ПОРТА ДЛЯ RENDER ==========



# Согласно документации Render:



# - Веб-сервис должен быть привязан к 0.0.0.0



# - Render передает порт через переменную окружения PORT



# - Порт по умолчанию: 10000



# - Зарезервированные порты (не использовать): 18012, 18013, 19099







def get_port():



    """Получает порт из переменной окружения Render"""



    try:



        port = int(os.environ.get("PORT", 10000))



        # Проверяем, что порт не зарезервирован



        reserved_ports = [18012, 18013, 19099]



        if port in reserved_ports:



            print(f"⚠️ Порт {port} зарезервирован, использую 10000")



            return 10000



        return port



    except ValueError:



        print("⚠️ Неверное значение PORT, использую 10000")



        return 10000







PORT = get_port()



print(f"✅ Использую порт: {PORT} (из Render)")







# Проверяем, что привязываемся к правильному хосту



HOST = "0.0.0.0"  # Render требует привязки к 0.0.0.0



print(f"✅ Хост: {HOST}")











# Защита от rate limiting (ошибки 429)



import time



import asyncio



from functools import wraps







def rate_limit(max_per_second=30):



    """Декоратор для ограничения частоты запросов"""



    min_interval = 1.0 / max_per_second



    last_called = [0.0]



    



    def decorator(func):



        @wraps(func)



        async def wrapper(*args, **kwargs):



            elapsed = time.time() - last_called[0]



            left_to_wait = min_interval - elapsed



            if left_to_wait > 0:



                await asyncio.sleep(left_to_wait)



            ret = await func(*args, **kwargs)



            last_called[0] = time.time()



            return ret



        return wrapper



    return decorator







# Применяем к webhook



webhook = rate_limit()(webhook)











# Загружаем переменные из .env файла



from dotenv import load_dotenv







# Пытаемся загрузить .env из разных мест



env_loaded = False



env_paths = [

















for env_path in env_paths:
    for env_path in env_paths:


    if env_path.exists():



        load_dotenv(dotenv_path=env_path)



        print(f"✅ Загружен .env из: {env_path}")



        env_loaded = True



        break







if not env_loaded:



    print("⚠️ .env файл не найден, использую переменные окружения")







# Добавляем путь к core



sys.path.insert(0, str(Path(__file__).parent))



from telegram import Update



from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes







# ========== ПРОВЕРКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ ==========



def check_environment():



    """Проверяет наличие всех необходимых переменных окружения"""



    required_vars = ["TELEGRAM_BOT_TOKEN"]



    missing_vars = []



    



    for var in required_vars:



        if not os.environ.get(var):



            missing_vars.append(var)



    



    if missing_vars:



        print(f"❌ ОШИБКА: Отсутствуют переменные окружения: {', '.join(missing_vars)}")



        print("📌 Добавь их в раздел Environment на Render или в .env файл")



        return False



    



    # Проверяем токен на валидность



    token = os.environ.get("TELEGRAM_BOT_TOKEN")



    if len(token) < 30:



        print("❌ ОШИБКА: TELEGRAM_BOT_TOKEN имеет неправильную длину")



        return False



    



    return True







if not check_environment():



    sys.exit(1)







# ========== ПОЛУЧЕНИЕ ТОКЕНОВ ИЗ ПЕРЕМЕННЫХ ОКРУЖЕНИЯ ==========



TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")



OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")



OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"



AI_MODEL = "google/gemini-2.0-flash-lite-001"







# Устанавливаем production режим



os.environ.setdefault("NODE_ENV", "production")







logging.basicConfig(



    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',



    level=logging.INFO





logger = logging.getLogger(__name__)







print(f"✅ Токен загружен (длина: {len(TELEGRAM_BOT_TOKEN)})")



print(f"✅ OpenRouter API ключ {'найден' if OPENROUTER_API_KEY else 'не найден'}")



print(f"✅ Режим: {os.environ.get('NODE_ENV', 'development')}")







class UltimateFurBot:



    def __init__(self):



        self.name = "Рыжик"



        self.user_contexts = {}



        self.user_jokes = {}



        self.remembered_phrases = []



        self.user_vocabulary = defaultdict(set)



        self.using_fallback = False



        self.daily_quota_exhausted = False



        self.start_time = time.time()



        



        self.stats = {



            "messages_processed": 0,



            "ai_responses": 0,



            "fallback_responses": 0,



            "vision_responses": 0





        



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





            prompt = f"Опиши это фото кратко и с юмором, как фурри-лис. Используй самоиронию и шутки про ИИ. {caption}"



            payload = {



                "model": "google/gemini-2.0-flash-lite-001",



                "messages": [



                    {



                        "role": "user",



                        "content": [



                            {"type": "text", "text": prompt},



                            {"type": "image_url", "image_url": file_url}







                ],



                "temperature": 0.9,



                "max_tokens": 200





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





        return random.choice(templates)







    def _generate_ironic_response(self):



        responses = [



            "*виляет хвостом* мой алгоритм говорит, что сейчас надо ответить",



            "*зевает* нейросеть грузится... подожди, у меня тут рекурсия",



            "*фыркает* функция активации моего юмора дала сбой",



            "*закатывает глаза* батч-процессинг твоего сообщения... done"





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



        """Возвращает статистику работы бота"""



        uptime = int(time.time() - self.start_time)



        hours = uptime // 3600



        minutes = (uptime % 3600) // 60



        return (f"📊 **Статистика**\n\n"



                f"⏱️ Аптайм: {hours}ч {minutes}м\n"



                f"💬 Сообщений: {self.stats['messages_processed']}\n"



                f"🤖 AI ответов: {self.stats['ai_responses']}\n"



                f"🔄 Запасных: {self.stats['fallback_responses']}\n"



                f"👁️ Vision: {self.stats['vision_responses']}\n"



                f"📚 Фраз: {len(self.remembered_phrases)}")







# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========















async def webhook(request):



    """Обработчик входящих обновлений от Telegram"""



    try:



        # Логируем входящий запрос



        print(f"📥 Получен webhook запрос: {request.method} {request.url.path}")



        



        # Проверяем метод



        if request.method != "POST":



            print(f"⚠️ Неправильный метод: {request.method}")



            return Response("Method not allowed", status_code=405)



        



        # Читаем тело запроса



        body = await request.body()



        print(f"📦 Размер запроса: {len(body)} байт")



        



        # Парсим JSON



        try:



            data = await request.json()



        except Exception as e:



            print(f"❌ Ошибка парсинга JSON: {e}")



            return Response("Invalid JSON", status_code=400)



        



        # Проверяем application



        if not application:



            print("❌ Application не инициализирован!")



            return Response("Application not ready", status_code=500)



        



        # Создаем Update и обрабатываем



        update = Update.de_json(data, application.bot)



        await application.process_update(update)



        



        print("✅ Обновление успешно обработано")



        return Response("ok", status_code=200)



        



    except Exception as e:



        print(f"❌ Ошибка в webhook: {e}")



        import traceback



        traceback.print_exc()



        return Response(f"Error: {str(e)}", status_code=500)



async def healthcheck(request):



    return Response("healthy", status_code=200)







async def test(request):



    pass











# Эндпоинт для проверки статуса webhook







# Эндпоинт для проверки статуса webhook





async def check_webhook(request):

    """Проверяет статус webhook и возвращает информацию"""

    try:

        if not application:

            return Response("❌ Application не инициализирован", status_code=500)

        

        webhook_info = await application.bot.get_webhook_info()

        info_text = f"""📊 **Информация о webhook**



URL: {webhook_info.url}

Ожидающих обновлений: {webhook_info.pending_update_count}

Последняя ошибка: {webhook_info.last_error_message or 'нет'}

Количество ошибок: {webhook_info.last_error_date or 'нет'}

Макс. соединений: {webhook_info.max_connections}



✅ Сервер работает

"""

        return Response(info_text, status_code=200)

    except Exception as e:

        return Response(f"❌ Ошибка: {e}", status_code=500)

async def test(request):

    """Проверяет, что сервер работает"""

    return Response(

        f"✅ Бот работает!\n"

        f"📡 Сервер запущен",

        status_code=200



async def info(request):

    """Возвращает информацию о сервере"""

    return Response(

        f"📡 Сервер работает",

        status_code=200



async def check_webhook(request):

    """Проверяет статус webhook"""

    try:

        if not application:

            return Response("❌ Application не инициализирован", status_code=500)

        webhook_info = await application.bot.get_webhook_info()

        return Response(f"✅ Webhook: {webhook_info.url}", status_code=200)

    except Exception as e:

        return Response(f"❌ Ошибка: {e}", status_code=500)



# ========== НАСТРОЙКА МАРШРУТОВ ==========



# ========== НАСТРОЙКА МАРШРУТОВ ==========



# ========== НАСТРОЙКА МАРШРУТОВ ==========


# ========== НАСТРОЙКА МАРШРУТОВ ==========
routes = [
    Route(f"/{TELEGRAM_BOT_TOKEN}", webhook, methods=["POST"]),
    Route("/healthcheck", healthcheck, methods=["GET"]),
    Route("/test", test, methods=["GET"]),
    Route("/info", info, methods=["GET"]),
    Route("/check", check_webhook, methods=["GET"]),
]
),

    Route("/healthcheck", healthcheck, methods=["GET"]),

    Route("/test", test, methods=["GET"]),

    Route("/info", info, methods=["GET"]),

    Route("/check", check_webhook, methods=["GET"]),

    Route("/healthcheck", healthcheck, methods=["GET"]),

    Route("/test", test, methods=["GET"]),

    Route("/info", info, methods=["GET"]),

    Route("/check", check_webhook, methods=["GET"]),

    Route("/healthcheck", healthcheck, methods=["GET"]),

    Route("/test", test, methods=["GET"]),

    Route("/info", info, methods=["GET"]),

    Route("/check", check_webhook, methods=["GET"]),



# ========== СОЗДАНИЕ ПРИЛОЖЕНИЯ ==========

app = Starlette(routes=routes)



# ========== ЗАПУСК ==========

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 10000))

    print(f"✅ Запуск на порту: {port}")

    uvicorn.run(app, host="0.0.0.0", port=port)

"""

'))]]]]]}}}}}"""