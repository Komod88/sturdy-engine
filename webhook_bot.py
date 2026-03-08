#!/usr/bin/env python3
import os
import sys
import logging
from pathlib import Path
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route
import uvicorn

# ========== НАСТРОЙКИ ==========
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
if not TELEGRAM_BOT_TOKEN:
    print("❌ ОШИБКА: TELEGRAM_BOT_TOKEN не найден!")
    sys.exit(1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print(f"✅ Токен загружен (длина: {len(TELEGRAM_BOT_TOKEN)})")

# ========== ЭНДПОИНТЫ ==========
async def healthcheck(request):
    return PlainTextResponse("healthy")

async def test(request):
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
