#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import logging
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.bot import FurChat

# Автоматически определяем версию библиотеки
try:
    import telegram
    TELEGRAM_VERSION = telegram.__version__
    if TELEGRAM_VERSION.startswith('20.'):
        from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
        MODE = "new"
    else:
        from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
        MODE = "old"
except:
    print("❌ Библиотека telegram не установлена")
    sys.exit(1)

TOKEN = os.environ.get("BOT_TOKEN", "os.environ.get("BOT_TOKEN", "")")

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

class FurChatTelegram:
    def __init__(self):
        self.bot = FurChat(str(Path(__file__).parent))
        self.mode = MODE
        print(f"  📡 Режим совместимости: {'новый' if self.mode == 'new' else 'старый'}")
        
        if self.mode == "new":
            self.application = None
        else:
            self.updater = Updater(token=TOKEN, use_context=True)
            self.dp = self.updater.dispatcher
    
    # Общие методы
    def start(self, update, context):
        user = update.effective_user
        update.message.reply_text(
            f"🐺 Привет, {user.first_name}!\nЯ {self.bot.name} - фурри-лис с характером.\n\nКоманды:\n/stats - статистика\n/learn - выучить новые слова\n/word - слово дня\n/help - помощь"
        )
    
    def help(self, update, context):
        update.message.reply_text(
            f"🐺 **{self.bot.name} - помощь**\n\n/stats - статистика\n/learn - выучить новые слова\n/word - слово дня",
            parse_mode='Markdown' if self.mode == "new" else None
        )
    
    def stats(self, update, context):
        user_id = str(update.effective_user.id)
        user = self.bot._get_user(user_id)
        update.message.reply_text(
            f"📊 **Статистика**\n\nНастроение: {user.get_mood_string()} ({user.mood}/5)\nОтношение: {user.get_relation_string()} ({user.relation}/5)\nСлов в словаре: {len(self.bot.kb.vocabulary)}\nВыучено фраз: {len(self.bot.kb.learned_phrases)}",
            parse_mode='Markdown' if self.mode == "new" else None
        )
    
    def learn(self, update, context):
        update.message.reply_text("📚 Учу новые слова...")
        result = self.bot.word_learner.learn_new_words(10)
        update.message.reply_text(f"✅ Выучено {result} новых слов!")
    
    def word(self, update, context):
        word = self.bot.word_learner.get_word_of_the_day()
        update.message.reply_text(f"🎯 Слово дня: **{word}**", parse_mode='Markdown' if self.mode == "new" else None)
    
    def handle_message(self, update, context):
        user = update.effective_user
        user_id = str(user.id)
        message_text = update.message.text
        is_private = update.message.chat.type == 'private'
        
        if not is_private:
            mentioned = False
            bot_username = context.bot.username
            if bot_username and f"@{bot_username}" in message_text:
                mentioned = True
                message_text = message_text.replace(f"@{bot_username}", "").strip()
            triggers = ["рыжий", "лис", "фурри", "бот"]
            if not mentioned and not any(t in message_text.lower() for t in triggers):
                return
        
        response = self.bot.respond(user_id, message_text, telegram_mode=not is_private)
        if response:
            update.message.reply_text(response)
    
    # Запуск для новой версии
    def run_new(self):
        from telegram.ext import Application, CommandHandler, MessageHandler, filters
        self.application = Application.builder().token(TOKEN).build()
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help))
        self.application.add_handler(CommandHandler("stats", self.stats))
        self.application.add_handler(CommandHandler("learn", self.learn))
        self.application.add_handler(CommandHandler("word", self.word))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        print("✅ Бот запущен! Нажми Ctrl+C для остановки")
        self.application.run_polling()
    
    # Запуск для старой версии
    def run_old(self):
        self.dp.add_handler(CommandHandler("start", self.start))
        self.dp.add_handler(CommandHandler("help", self.help))
        self.dp.add_handler(CommandHandler("stats", self.stats))
        self.dp.add_handler(CommandHandler("learn", self.learn))
        self.dp.add_handler(CommandHandler("word", self.word))
        self.dp.add_handler(MessageHandler(Filters.text & ~Filters.command, self.handle_message))
        print("✅ Бот запущен! Нажми Ctrl+C для остановки")
        self.updater.start_polling()
        self.updater.idle()
    
    def run(self):
        print(f"\n🐺 Запуск {self.bot.name} в Telegram...")
        if self.mode == "new":
            self.run_new()
        else:
            self.run_old()

def main():
    bot = FurChatTelegram()
    bot.run()

if __name__ == "__main__":
    main()
