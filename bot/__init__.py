"""
Telegram Business Assistant Bot.

Основные компоненты доступны через:
- bot.core - Ядро приложения (application, config, context, dispatch)
- bot.utils - Утилиты (logger, stages, constants)
- bot.managers - Менеджеры (menu_manager, stats_manager)
- bot.handlers - Обработчики событий
- bot.models - Модели базы данных
- bot.services - Бизнес-логика
- bot.middlewares - Middleware
"""
from bot.core.application import BotApplication
from bot import instance

__all__ = ["BotApplication", "instance"]
