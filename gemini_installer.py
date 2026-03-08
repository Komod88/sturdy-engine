#!/usr/bin/env python3
"""
Gemini AI Installer для FurChat бота
Переключает с OpenRouter на Google Gemini
Лимит: 500-1500 запросов в день
"""

import os
import sys
import subprocess
from pathlib import Path

# ========== ЦВЕТА ==========
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"

def print_color(text, color):
    print(f"{color}{text}{RESET}")

def install_gemini():
    """Устанавливает библиотеку Google Generative AI"""
    print_color("\n📦 Устанавливаю Google Generative AI...", BLUE)
    try:
        import google.generativeai
        print_color("✅ Библиотека уже установлена", GREEN)
    except ImportError:
        print_color("❌ Библиотека не найдена. Устанавливаю...", YELLOW)
        subprocess.check_call([sys.executable, "-m", "pip", "install", "google-generativeai"])
        print_color("✅ Google Generative AI установлен!", GREEN)

def get_gemini_key():
    """Запрашивает ключ Gemini у пользователя"""
    print_color("\n🔑 Получи ключ Gemini:", BLUE)
    print("   1. Зайди на https://aistudio.google.com/apikey")
    print("   2. Нажми 'Create API Key'")
    print("   3. Скопируй ключ")
    return input("\n📝 Вставь Gemini API ключ: ").strip()

def update_env_file(gemini_key):
    """Обновляет .env файл с новым ключом"""
    env_path = Path("/storage/emulated/0/FurryBot/FurChatTelegram/.env")
    
    if env_path.exists():
        with open(env_path, 'r') as f:
            lines = f.readlines()
        
        # Заменяем или добавляем GEMINI_KEY
        found = False
        for i, line in enumerate(lines):
            if line.startswith("GEMINI_KEY="):
                lines[i] = f"GEMINI_KEY={gemini_key}\n"
                found = True
                break
        
        if not found:
            lines.append(f"\n# Google Gemini API Key\nGEMINI_KEY={gemini_key}\n")
        
        with open(env_path, 'w') as f:
            f.writelines(lines)
    else:
        with open(env_path, 'w') as f:
            f.write(f"""# Telegram Bot Token
BOT_TOKEN=8696373751:AAEvctxXZWhA7_goWAJuxQXvBN7OugKvTuM

# Google Gemini API Key
GEMINI_KEY={gemini_key}

# Настройки
BOT_NAME=Рыжик
""")
    
    print_color("✅ .env файл обновлён с Gemini ключом", GREEN)

def create_gemini_bot():
    """Создаёт новую версию бота с Gemini"""
    bot_path = Path("/storage/emulated/0/FurryBot/FurChatTelegram/furchat_bot_gemini.py")
    
    gemini_code = '''#!/usr/bin/env python3
"""
FurChat Bot - Версия с Google Gemini
Лимит: 500-1500 запросов в день
"""

import os
import sys
import json
import logging
import asyncio
import random
from datetime import datetime
from pathlib import Path
from collections import defaultdict, deque

# Google Gemini
import google.generativeai as genai

# Telegram
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Загружаем .env
from dotenv import load_dotenv
env_path = Path("/storage/emulated/0/FurryBot/FurChatTelegram/.env")
load_dotenv(dotenv_path=env_path)

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_KEY")
BOT_NAME = os.getenv("BOT_NAME", "Рыжик")

if not BOT_TOKEN:
    print("❌ ОШИБКА: BOT_TOKEN не найден!")
    sys.exit(1)

if not GEMINI_KEY:
    print("❌ ОШИБКА: GEMINI_KEY не найден!")
    print("💡 Получи ключ на https://aistudio.google.com/apikey")
    sys.exit(1)

# Настраиваем Gemini
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-2.0-flash-lite-001')

# Настройки
MAX_HISTORY = 30
MEMORY_FILE = "bot_memory.json"

# Логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Память
class BotMemory:
    def __init__(self, memory_file=MEMORY_FILE):
        self.memory_file = memory_file
        self.phrases = []
        self.user_stats = defaultdict(lambda: {
            'messages': 0,
            'first_seen': None,
            'last_seen': None
        })
        self.load()
    
    def load(self):
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.phrases = data.get('phrases', [])
                    stats = data.get('user_stats', {})
                    for user_id, stat in stats.items():
                        self.user_stats[user_id] = stat
        except Exception as e:
            logger.error(f"Ошибка загрузки памяти: {e}")
    
    def save(self):
        try:
            stats = {}
            for user_id, stat in self.user_stats.items():
                stats[user_id] = dict(stat)
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump({'phrases': self.phrases, 'user_stats': stats}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Ошибка сохранения памяти: {e}")
    
    def remember_phrase(self, phrase):
        if phrase not in self.phrases:
            self.phrases.append(phrase)
            if len(self.phrases) > 100:
                self.phrases = self.phrases[-100:]
            self.save()
    
    def update_user_stats(self, user_id, username):
        now = datetime.now().isoformat()
        stats = self.user_stats[user_id]
        if not stats['first_seen']:
            stats['first_seen'] = now
        stats['last_seen'] = now
        stats['messages'] += 1
        stats['username'] = username
        self.save()

memory = BotMemory()
user_contexts = defaultdict(lambda: deque(maxlen=MAX_HISTORY))
user_last_message = {}

SYSTEM_PROMPT = """Ты — Рыжик, фурри-лис.

ОСОБЕННОСТИ:
- Ты обаятельный, с лёгким цинизмом
- Используй чёрный юмор и самоиронию
- *Действия* в звёздочках обязательны
- Шути про то, что ты бот

ДЛИНА ОТВЕТА:
- Шутка — 1 предложение
- Вопрос — 2-3 предложения
- Философия — до 4 предложений

ПРИМЕРЫ:
- *зевает* Живу в папке furchat, работаю на дядю
- *хитро* Мой код говорит «привет», а я говорю «пока, баги»"""

async def get_ai_response(user_id: str, message: str, username: str = "Друг") -> str:
    memory.update_user_stats(user_id, username)
    user_contexts[user_id].append(f"Пользователь: {message}")
    
    try:
        # Формируем контекст
        history = list(user_contexts[user_id])[-5:]
        context = "\\n".join(history)
        prompt = f"{SYSTEM_PROMPT}\\n\\nИстория:\\n{context}\\n\\nОтветь как Рыжик:"
        
        # Запрос к Gemini
        response = await asyncio.to_thread(
            model.generate_content,
            prompt
        )
        
        answer = response.text
        user_contexts[user_id].append(f"Рыжик: {answer}")
        
        if len(answer) > 20 and random.random() < 0.1:
            memory.remember_phrase(answer)
        
        return answer
        
    except Exception as e:
        logger.error(f"Gemini ошибка: {e}")
        return random.choice([
            "*зевает* Ой, всё сломалось...",
            "*чешет за ухом* Давай позже, я в ауте",
            "*грустно* Баги замучили..."
        ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    username = user.first_name or "Друг"
    await update.message.reply_text(
        f"🦊 Привет, {username}!\\n"
        f"Я {BOT_NAME} на Gemini AI.\\n"
        f"*зевает* 500 запросов в день, погнали!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    username = update.effective_user.first_name or "Друг"
    message = update.message.text
    
    now = datetime.now().timestamp()
    if user_id in user_last_message:
        if now - user_last_message[user_id] < 1:
            return
    user_last_message[user_id] = now
    
    await update.message.chat.send_action(action="typing")
    response = await get_ai_response(user_id, message, username)
    await update.message.reply_text(response)

def main():
    print(f"\\n🚀 Запуск {BOT_NAME} на Gemini...")
    print(f"✅ Токен загружен (длина: {len(BOT_TOKEN)})")
    print(f"✅ Gemini ключ: {'найден' if GEMINI_KEY else 'не найден'}")
    
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("✅ Обработчики зарегистрированы")
    print("🚀 Бот запускается...\\n")
    
    app.run_polling()

if __name__ == "__main__":
    main()
'''
    
    with open(bot_path, 'w', encoding='utf-8') as f:
        f.write(gemini_code)
    
    print_color(f"✅ Создан файл: {bot_path}", GREEN)
    return bot_path

def main():
    print_color("""
    ╔════════════════════════════════════════╗
    ║  Google Gemini Installer               ║
    ║  Переключает бота на Gemini AI         ║
    ║  Лимит: 500-1500 запросов/день         ║
    ╚════════════════════════════════════════╝
    """, BLUE)
    
    # 1. Устанавливаем библиотеку
    install_gemini()
    
    # 2. Получаем ключ
    gemini_key = get_gemini_key()
    
    # 3. Обновляем .env
    update_env_file(gemini_key)
    
    # 4. Создаём нового бота
    bot_path = create_gemini_bot()
    
    print_color("\n" + "="*50, GREEN)
    print_color("✅ УСТАНОВКА ЗАВЕРШЕНА!", GREEN)
    print_color("="*50, GREEN)
    print_color("\n🚀 Теперь запусти бота:", YELLOW)
    print(f"   cd /storage/emulated/0/FurryBot/FurChatTelegram")
    print(f"   python furchat_bot_gemini.py")
    print_color("\n📝 Все настройки сохранены в .env", BLUE)

if __name__ == "__main__":
    main()