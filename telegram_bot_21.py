#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import logging
import asyncio
from pathlib import Path

# Добавляем путь к core
sys.path.insert(0, str(Path(__file__).parent))

from core.bot import FurChat
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram import Update

# ТВОЙ ТОКЕН
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class FurChatTelegram:
    def __init__(self):
        self.bot = FurChat(str(Path(__file__).parent))
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        await update.message.reply_text(
            f"🐺 Привет, {user.first_name}!\n"
            f"Я {self.bot.name} - фурри-лис с характером.\n\n"
            f"Команды:\n"
            f"/stats - статистика\n"
            f"/learn - выучить новые слова\n"
            f"/word - слово дня"
        )
    
    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        user = self.bot._get_user(user_id)
        await update.message.reply_text(
            f"📊 Статистика\n\n"
            f"Настроение: {user.get_mood_string()} ({user.mood}/5)\n"
            f"Отношение: {user.get_relation_string()} ({user.relation}/5)\n"
            f"Слов в словаре: {len(self.bot.kb.vocabulary)}\n"
            f"Выучено фраз: {len(self.bot.kb.learned_phrases)}"
        )
    
    async def learn(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("📚 Учу новые слова из словаря... Подожди немного...")
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self.bot.word_learner.learn_new_words, 10)
        await update.message.reply_text(f"✅ Выучено {result} новых слов!")
    
    async def word(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        word = self.bot.word_learner.get_word_of_the_day()
        await update.message.reply_text(f"🎯 Слово дня: {word}")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        
        logger.info(f"Message from {user.first_name} ({user_id}): {message_text[:50]}...")
        
        response = self.bot.respond(user_id, message_text, telegram_mode=not is_private)
        if response:
            await update.message.reply_text(response)
    
    def run(self):
        print(f"\n🐺 Запуск {self.bot.name} в Telegram...")
        print(f"📁 База: {self.bot.base_path}")
        print(f"📚 Слов в словаре: {len(self.bot.kb.vocabulary)}")
        print(f"📚 Выучено фраз: {len(self.bot.kb.learned_phrases)}")
        print("-" * 40)
        
        application = Application.builder().token(TOKEN).build()
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("stats", self.stats))
        application.add_handler(CommandHandler("learn", self.learn))
        application.add_handler(CommandHandler("word", self.word))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        print("✅ Бот запущен! Нажми Ctrl+C для остановки")
        application.run_polling()

if __name__ == "__main__":
    FurChatTelegram().run()