#!/usr/bin/env python3
"""
Direct Run - запускает fixed_mygit_v3.py
"""

import os
import sys
from pathlib import Path

repo_path = "/storage/emulated/0/FurryBot/FurChatTelegram"
os.chdir(repo_path)

# Добавляем текущую папку в путь
sys.path.insert(0, repo_path)

file_path = Path(repo_path) / "fixed_mygit_v3.py"
if not file_path.exists():
    print("❌ Файл не найден")
    sys.exit(1)

with open(file_path, 'r', encoding='utf-8') as f:
    exec(f.read())
