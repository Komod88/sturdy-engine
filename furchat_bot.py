#!/usr/bin/env python3
"""
FurChat Bot - Мультипровайдерная версия
Использует OpenRouter (Gemini) и Cloudflare
"""

import os
import sys
import asyncio
import httpx
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Загружаем .env
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")
CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID")
BOT_NAME = os.getenv("BOT_NAME", "Рыжик")

if not BOT_TOKEN:
    print("❌ Ошибка: BOT_TOKEN не найден!")
    sys.exit(1)

print(f"✅ OpenRouter: {'есть' if OPENROUTER_API_KEY else 'нет'}")
print(f"✅ Cloudflare: {'есть' if CLOUDFLARE_API_TOKEN else 'нет'}")

SYSTEM_PROMPT = "Ты - Рыжик, фурри-лис с характером. Отвечай кратко (1-3 предложения), с юмором и самоиронией. Используй *действия* в звёздочках."

user_contexts = {}
user_last_message = {}

async def query_openrouter(messages):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/Komod88/sturdy-engine",
        "X-Title": "FurChat Bot"
    }
    data = {
        "model": "google/gemini-2.5-flash",
        "messages": messages,
        "temperature": 0.8
    }
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, headers=headers, json=data)
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
    except:
        return None

async def query_cloudflare(messages):
    if not CLOUDFLARE_API_TOKEN or not CLOUDFLARE_ACCOUNT_ID:
        return None
    url = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/run/@cf/meta/llama-3.3-70b-instruct"
    headers = {
        "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {"messages": messages}
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, headers=headers, json=data)
            if response.status_code == 200:
                result = response.json()
                return result["result"]["response"]
    except:
        return None

async def get_response(messages):
    if CLOUDFLARE_API_TOKEN:
        result = await query_cloudflare(messages)
        if result:
            return result
    if OPENROUTER_API_KEY:
        result = await query_openrouter(messages)
        if result:
            return result
    return None

async def start(update, context):
    user = update.effective_user
    await update.message.reply_text(
        f"🦊 Привет, {user.first_name}!\n"
        f"Я {BOT_NAME} - фурри-лис с AI.\n"
        f"*зевает* Спрашивай!"
    )

async def handle_message(update, context):
    user_id = str(update.effective_user.id)
    username = update.effective_user.first_name or "Друг"
    message = update.message.text
    
    if user_id not in user_contexts:
        user_contexts[user_id] = []
    
    user_contexts[user_id].append({"role": "user", "content": f"{username}: {message}"})
    if len(user_contexts[user_id]) > 10:
        user_contexts[user_id] = user_contexts[user_id][-10:]
    
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + user_contexts[user_id]
    
    await update.message.chat.send_action(action="typing")
    response = await get_response(messages)
    
    if response:
        user_contexts[user_id].append({"role": "assistant", "content": response})
        await update.message.reply_text(response)
    else:
        await update.message.reply_text("*зевает* Ошибка, попробуй позже.")

app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print(f"\n🚀 Запуск {BOT_NAME} бота...")
app.run_polling()
