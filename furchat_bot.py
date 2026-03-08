#!/usr/bin/env python3
import os
import sys
import logging
import asyncio
from pathlib import Path

# Добавляем путь к core (если есть)
core_path = Path(__file__).parent / "core"
if core_path.exists():
    sys.path.insert(0, str(Path(__file__).parent))

# Пробуем импортировать FurChat
try:
    from core.bot import FurChat
    HAS_CORE = True
except ImportError:
    HAS_CORE = False
    print("⚠️ Модуль core не найден, используется упрощённая версия")

from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram import Update

TOKEN = os.environ.get("BOT_TOKEN")")
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

class SimpleFurChat:
    def __init__(self):
        self.name = "Рыжий"
        self.actions = ["*виляет хвостом*", "*чешет за ухом*", "*прижимает уши*"]
        self.greetings = ["*виляет хвостом* Привет!", "Здаров!", "Приветик!"]
        
    def respond(self, user_id, text, telegram_mode=False):
        if "привет" in text.lower():
            return self.greetings[0]
        return f"{self.actions[0]} как дела?"

class FurChatTelegram:
    def __init__(self):
        if HAS_CORE:
            self.bot = FurChat(str(Path(__file__).parent))
        else:
            self.bot = SimpleFurChat()
        print(f"✅ Бот {self.bot.name} готов")
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        await update.message.reply_text(f"🐺 Привет, {user.first_name}!\nЯ {self.bot.name}\n/stats - статистика")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        msg = update.message.text
        response = self.bot.respond(user_id, msg, False)
        if response:
            await update.message.reply_text(response)
    
    def run(self):
        print(f"\n🐺 Запуск {self.bot.name}...")
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", self.start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        print("✅ Бот запущен! Нажми Ctrl+C для остановки")
        app.run_polling()

if __name__ == "__main__":
    FurChatTelegram().run()