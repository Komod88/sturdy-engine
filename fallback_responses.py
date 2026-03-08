#!/usr/bin/env python3
"""
Запасные ответы для бота (когда нейросеть не работает)
"""

import random

class FallbackResponses:
    """Коллекция запасных ответов"""
    
    GREETINGS = [
        "*виляет хвостом* Привет!",
        "*зевает* О, привет...",
        "*принюхивается* Здаров!",
        "*потягивается* Ну привет!"
    ]
    
    QUESTIONS = [
        "*задумчиво* Хм, интересно...",
        "*чешет за ухом* Дай подумать...",
        "*прищуривается* А сам-то как думаешь?",
        "*хихикает* Хороший вопрос!"
    ]
    
    FUNNY = [
        "*фыркает* Ой, всё!",
        "*закатывает глаза* Ну ты и зануда!",
        "*отворачивается* Мне стыдно за нас обоих",
        "*зевает* Скучно с тобой..."
    ]
    
    @classmethod
    def get(cls, category="GREETINGS"):
        """Возвращает случайный ответ из категории"""
        category = getattr(cls, category.upper(), cls.GREETINGS)
        return random.choice(category)
    
    @classmethod
    def get_for_message(cls, message):
        """Выбирает ответ в зависимости от сообщения"""
        msg = message.lower()
        
        if "привет" in msg or "здаров" in msg:
            return random.choice(cls.GREETINGS)
        elif "как дела" in msg:
            return random.choice([
                "*потягивается* Норм, а у тебя?",
                "*зевает* Скучаю...",
                "*виляет хвостом* Отлично!"
            ])
        elif "пока" in msg or "до свидания" in msg:
            return random.choice([
                "*машет лапой* Пока!",
                "*зевает* Иди-иди...",
                "*провожает взглядом* Бывай!"
            ])
        elif "?" in msg:
            return random.choice(cls.QUESTIONS)
        else:
            return random.choice(cls.FUNNY)
