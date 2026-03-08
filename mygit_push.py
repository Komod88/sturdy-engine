#!/usr/bin/env python3
"""
Push script for MyGit
Запусти чтобы отправить изменения на GitHub
"""

import os

from config import BOT_TOKEN
import sys
import datetime
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent))

from mygit import MyGit

# Твой GitHub токен
TOKEN = os.environ.get("BOT_TOKEN")

if not GITHUB_TOKEN:
    print("❌ ОШИБКА: GITHUB_TOKEN не указан!")
    sys.exit(1)

# Путь к проекту
repo_path = "/storage/emulated/0/FurryBot/FurChatTelegram"

# Инициализируем Git
git = MyGit(repo_path)

# Добавляем все изменения
git.add(".")

# Создаём коммит
message = f"Автообновление {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
commit = git.commit(message)

if commit:
    # Отправляем на GitHub
    git.push(GITHUB_TOKEN)
else:
    print("❌ Нет изменений для коммита")
