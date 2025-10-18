"""Ядро приложения бота."""

from bot.core.application import BotApplication
from bot.core.components import BotComponents, create_bot_components, get_bot_token
from bot.core.context import get_app, set_app, try_get_app
from bot.core.config import settings
from bot.core.dispatch import Dispatch

__all__ = [
    'BotApplication',
    'BotComponents',
    'create_bot_components',
    'get_bot_token',
    'get_app',
    'set_app',
    'try_get_app',
    'settings',
    'Dispatch',
]
