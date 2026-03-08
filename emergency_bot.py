#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
from pathlib import Path

# Добавляем путь к core
sys.path.insert(0, str(Path(__file__).parent))

from core.bot import FurChat

print("="*60)
print("🐺 FurChat - АВАРИЙНЫЙ РЕЖИМ (без Telegram)")
print("="*60)
print("Библиотека telegram не установлена.")
print("Запускаю консольную версию...")
print("="*60)

if __name__ == "__main__":
    bot = FurChat(str(Path(__file__).parent))
    bot.console_mode()
