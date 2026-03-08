#!/usr/bin/env python3
import os
import shutil
import subprocess
from pathlib import Path

print("="*60)
print("🔥 ФИНАЛЬНЫЙ УСТАНОВЩИК FURCHAT")
print("="*60)

# Папки
download = Path("/storage/emulated/0/Download")
target = Path("/storage/emulated/0/FurryBot/FurChatTelegram")

# Создаём целевую папку
target.mkdir(parents=True, exist_ok=True)
print(f"📁 Целевая папка: {target}")

# Файлы для перемещения
files = [
    "super_installer.py",
    "furchat_bot.py", 
    "telegram_bot_21.py",
    "telegram_bot_fixed.py",
    "telegram_bot_ultimate.py",
    "telegram_bot.py"
]

# Перемещение
print("\n📦 ПЕРЕМЕЩЕНИЕ ФАЙЛОВ")
print("-"*40)

moved = 0
for file in files:
    src = download / file
    dst = target / file
    if src.exists():
        print(f"📄 Найден: {file}")
        shutil.move(str(src), str(dst))
        print(f"  ✅ Перемещён в {target}")
        moved += 1
    else:
        print(f"❌ Не найден: {file}")

print(f"\n✅ Перемещено: {moved} файлов")

# Установка библиотеки
print("\n📦 УСТАНОВКА БИБЛИОТЕКИ")
print("-"*40)

subprocess.run(["pip", "install", "python-telegram-bot==21.4"], capture_output=True)
print("✅ Библиотека установлена")

# Создание скрипта запуска
print("\n📝 СОЗДАНИЕ СКРИПТА ЗАПУСКА")
print("-"*40)

run_script = target / "start_bot.sh"
with open(run_script, "w") as f:
    f.write("""#!/bin/bash
cd "$(dirname "$0")"
python3 furchat_bot.py
""")
os.chmod(run_script, 0o755)
print(f"✅ Скрипт создан: {run_script}")

print("\n" + "="*60)
print("✅ УСТАНОВКА ЗАВЕРШЕНА!")
print("="*60)
print(f"\n📁 Все файлы в: {target}")
print("\n🚀 ЗАПУСК БОТА:")
print("-"*40)
print("ВАРИАНТ 1 - Через терминал:")
print(f"cd {target}")
print("python3 furchat_bot.py")
print("\nВАРИАНТ 2 - Через скрипт:")
print(f"cd {target}")
print("./start_bot.sh")
print("\nВАРИАНТ 3 - В Pydroid:")
print("1. Открой Pydroid")
print(f"2. Найди файл {target}/furchat_bot.py")
print("3. Нажми RUN (▶️)")