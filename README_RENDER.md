# 🐺 FurChat Bot для Telegram

## 🚀 Деплой на Render

1. Создай репозиторий на GitHub и загрузи туда эти файлы
2. Зайди на [render.com](https://render.com)
3. Нажми **"New +" → "Blueprint"**
4. Подключи свой репозиторий
5. Render сам найдёт `render.yaml` и настроит всё

## 🔧 Переменные окружения

- `BOT_TOKEN` - токен твоего бота (уже в render.yaml)

## 📁 Структура

- `webhook_bot.py` - основной файл бота
- `requirements.txt` - зависимости
- `render.yaml` - конфигурация Render
- `core/` - основная логика (опционально)

## 🌐 После деплоя

Бот будет доступен по адресу: `https://furchat-bot.onrender.com`

В Telegram бот будет отвечать через webhook.
