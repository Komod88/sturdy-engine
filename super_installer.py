#!/usr/bin/env python3
import os
import sys
import subprocess

print("="*60)
print("🐺 СУПЕР-УСТАНОВЩИК FURCHAT")
print("="*60)

# ШАГ 1: Установка библиотеки
print("\n1️⃣ УСТАНОВКА TELEGRAM БИБЛИОТЕКИ")
print("-"*40)

print("📦 Устанавливаю python-telegram-bot 21.4...")
subprocess.run([sys.executable, "-m", "pip", "install", "python-telegram-bot==21.4"], 
               capture_output=True)

# ШАГ 2: Создание файла бота
print("\n2️⃣ СОЗДАНИЕ ФАЙЛА БОТА")
print("-"*40)

bot_code = '''#!/usr/bin/env python3
import os
import sys
import logging
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from core.bot import FurChat
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram import Update

TOKEN = "8696373751:AAHVQRg9ZXrJbuaKnT1UdTIAvqa9GEfPan4"
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

class FurChatTelegram:
    def __init__(self):
        self.bot = FurChat(str(Path(__file__).parent))
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        await update.message.reply_text(f"🐺 Привет, {user.first_name}!\\nЯ {self.bot.name}\\n/stats - статистика\\n/learn - учить слова\\n/word - слово дня")
    
    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        user = self.bot._get_user(user_id)
        await update.message.reply_text(
            f"📊 Статистика\\nНастроение: {user.get_mood_string()} ({user.mood}/5)\\n"
            f"Отношение: {user.get_relation_string()} ({user.relation}/5)\\n"
            f"Слов: {len(self.bot.kb.vocabulary)}\\nФраз: {len(self.bot.kb.learned_phrases)}"
        )
    
    async def learn(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("📚 Учу...")
        result = await asyncio.get_event_loop().run_in_executor(None, self.bot.word_learner.learn_new_words, 10)
        await update.message.reply_text(f"✅ Выучено {result} слов!")
    
    async def word(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        word = self.bot.word_learner.get_word_of_the_day()
        await update.message.reply_text(f"🎯 Слово дня: {word}")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        msg = update.message.text
        is_private = update.message.chat.type == 'private'
        
        if not is_private:
            mentioned = False
            if context.bot.username and f"@{context.bot.username}" in msg:
                mentioned = True
                msg = msg.replace(f"@{context.bot.username}", "").strip()
            triggers = ["рыжий", "лис", "фурри", "бот"]
            if not mentioned and not any(t in msg.lower() for t in triggers):
                return
        
        response = self.bot.respond(user_id, msg, telegram_mode=not is_private)
        if response:
            await update.message.reply_text(response)
    
    def run(self):
        print(f"\\n🐺 Запуск {self.bot.name}...")
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", self.start))
        app.add_handler(CommandHandler("stats", self.stats))
        app.add_handler(CommandHandler("learn", self.learn))
        app.add_handler(CommandHandler("word", self.word))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        print("✅ Бот запущен!")
        app.run_polling()

if __name__ == "__main__":
    FurChatTelegram().run()
'''

# Сохраняем в правильную папку
target_dir = "/storage/emulated/0/FurryBot/FurChatTelegram"
os.makedirs(target_dir, exist_ok=True)
bot_path = os.path.join(target_dir, "furchat_bot.py")

with open(bot_path, "w", encoding="utf-8") as f:
    f.write(bot_code)
print(f"✅ Файл создан: {bot_path}")

# ШАГ 3: Создание скрипта запуска
print("\n3️⃣ СОЗДАНИЕ СКРИПТА ЗАПУСКА")
print("-"*40)

run_script = os.path.join(target_dir, "start.sh")
with open(run_script, "w", encoding="utf-8") as f:
    f.write("""#!/bin/bash
cd "$(dirname "$0")"
python3 furchat_bot.py
""")
os.chmod(run_script, 0o755)
print(f"✅ Скрипт создан: {run_script}")

# ШАГ 4: Инструкция
print("\n" + "="*60)
print("✅ УСТАНОВКА ЗАВЕРШЕНА!")
print("="*60)
print(f"\n📁 Папка: {target_dir}")
print("\n🚀 ЗАПУСК:")
print("="*40)
print("ВАРИАНТ 1 - через терминал:")
print(f"cd {target_dir}")
print("python3 furchat_bot.py")
print("\nВАРИАНТ 2 - через Pydroid:")
print("1. Открой Pydroid")
print("2. Найди файл furchat_bot.py")
print("3. Нажми RUN (▶️)")
print("\n" + "="*60)