#!/usr/bin/env python3
"""
Config - универсальная конфигурация с поддержкой всех имён
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Загружаем .env
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    print("✅ .env файл загружен")

class TokenBridge:
    """Мост между разными именами токена"""
    
    # Список возможных имён переменной
    TOKEN_NAMES = [
        "BOT_TOKEN",
        "TELEGRAM_BOT_TOKEN", 
        "TELEGRAM_TOKEN",
        "TOKEN"
    ]
    
    @classmethod
    def get_token(cls):
        """Пытается найти токен под любым именем"""
        for name in cls.TOKEN_NAMES:
            token = os.getenv(name)
            if token:
                print(f"✅ Токен найден как {name}")
                return token
        return None
    
    @classmethod
    def validate(cls):
        """Проверяет наличие токена"""
        token = cls.get_token()
        if not token:
            print("❌ Токен не найден! Пробовали имена:", ", ".join(cls.TOKEN_NAMES))
            print("💡 Проверь .env файл")
            sys.exit(1)
        print(f"✅ Токен загружен (длина: {len(token)})")
        return token

# Создаём единый токен
BOT_TOKEN = TokenBridge.validate()

# Остальные настройки
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
BOT_NAME = os.getenv("BOT_NAME", "Рыжик")
