#!/usr/bin/env python3
"""
Упрощённый бот для Render
"""

import os
import urllib.parse
import sys
import logging
from pathlib import Path
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route
import uvicorn

# ========== ТОКЕН ПРЯМО В КОДЕ ==========
TELEGRAM_BOT_TOKEN = "8696373751:AAE7t0lcx_7SIeEOQL8ORMl6zedQd4Jcrz4"

if not TELEGRAM_BOT_TOKEN:
    print("❌ ОШИБКА: TELEGRAM_BOT_TOKEN не найден!")
    sys.exit(1)

print(f"✅ Токен загружен (длина: {len(TELEGRAM_BOT_TOKEN)})")

# ========== ЭНДПОИНТЫ ==========
async def healthcheck(request):
    """Проверка здоровья"""
    return PlainTextResponse("healthy")

async def test(request):
    """Тестовый эндпоинт"""
    return PlainTextResponse("✅ Бот работает!")

# ========== МАРШРУТЫ ==========
routes = [
    Route("/healthcheck", healthcheck),
    Route("/test", test),
]

app = Starlette(routes=routes)

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"✅ Запуск на порту: {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
