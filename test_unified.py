#!/usr/bin/env python3
"""
Test unified token
"""

import os

from config import BOT_TOKEN
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()
token = os.getenv("BOT_TOKEN")

if token:
    print(f"✅ Токен найден: {token[:15]}...")
    print(f"📏 Длина: {len(token)}")
    
    import requests
    response = requests.get(f"https://api.telegram.org/bot{token}/getMe")
    
    if response.status_code == 200:
        data = response.json()
        if data.get("ok"):
            bot_info = data.get("result", {})
            print(f"✅ Токен работает!")
            print(f"🤖 Имя: {bot_info.get('first_name', 'неизвестно')}")
        else:
            print(f"❌ Ошибка: {data}")
    else:
        print(f"❌ Ошибка {response.status_code}: {response.text}")
else:
    print("❌ BOT_TOKEN не найден в .env")
    print("
📋 Содержимое .env:")
    if Path(".env").exists():
        with open(".env", 'r') as f:
            print(f.read())
