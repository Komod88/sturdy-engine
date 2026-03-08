#!/usr/bin/env python3
"""
Test bot token - проверяет работает ли токен
"""

import os

from config import BOT_TOKEN
import sys
from pathlib import Path
from dotenv import load_dotenv

# Загружаем .env
env_path = Path('.env')
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    print("✅ .env файл загружен")
else:
    print("❌ .env файл не найден!")
    sys.exit(1)

TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    print("❌ Токен не найден в переменных окружения!")
    sys.exit(1)

print(f"✅ Токен загружен: {TOKEN[:15]}...")
print(f"📏 Длина токена: {len(TOKEN)}")

# Проверяем через Telegram API
import requests
response = requests.get(f"https://api.telegram.org/bot{TOKEN}/getMe")

if response.status_code == 200:
    data = response.json()
    if data.get("ok"):
        bot_info = data.get("result", {})
        print(f"✅ Токен работает!")
        print(f"🤖 Имя бота: {bot_info.get('first_name', 'неизвестно')}")
        print(f"🆔 ID: {bot_info.get('id', 'неизвестно')}")
    else:
        print(f"❌ Ошибка: {data}")
else:
    print(f"❌ Ошибка {response.status_code}: {response.text}")
