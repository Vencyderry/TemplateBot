"""
Middleware для бота.

Структура аналогична handlers - группы middleware объединяются в списки.
"""

from bot.middlewares.message import (
    MessageDeleteMiddleware,
    RegistrationMiddleware
)
from bot.middlewares.callback_query import (
    CallbackQueryAnswerMiddleware,
    UserUpdateMiddleware
)
from bot.middlewares.registry import Middlewares

# Middleware для сообщений
message_middlewares = [
    RegistrationMiddleware(),
    MessageDeleteMiddleware(),
]

# Middleware для callback-запросов
callback_query_middlewares = [
    CallbackQueryAnswerMiddleware(),
    UserUpdateMiddleware(),
]


middlewares = Middlewares()
middlewares.message.extend(message_middlewares)
middlewares.callback_query.extend(callback_query_middlewares)

__all__ = [
    "middlewares"
]
