"""
Базовые компоненты бота.

Этот модуль содержит инициализацию базовых компонентов,
которые не зависят от других модулей проекта.
"""
import pytz
import telegrinder
from dataclasses import dataclass
from typing import Optional
from telegrinder import API, Token, Telegrinder
from telegrinder.client.aiohttp import AiohttpClient

from bot.utils import CtxStorage, AlignedLogger
from bot.managers import MenuManager


@dataclass
class BotComponents:
    """
    Контейнер для всех компонентов бота.

    Attributes:
        api: API клиент для взаимодействия с Telegram
        bot: Экземпляр Telegrinder
        fmt: HTML форматтер для сообщений
        wm: WaiterMachine для ожидания событий
        client: HTTP клиент (aiohttp)
        ctx: Хранилище контекста
        logger: Логгер приложения
        tz: Часовой пояс (по умолчанию Europe/Moscow)
        menu_manager: Менеджер для управления меню и сообщениями
    """
    api: API
    bot: Telegrinder
    fmt: type
    wm: telegrinder.WaiterMachine
    client: AiohttpClient
    ctx: CtxStorage
    logger: AlignedLogger
    tz: pytz.tzinfo.BaseTzInfo
    menu_manager: MenuManager


def get_bot_token() -> str:
    """Получить токен бота из конфигурации."""
    from bot.core.config import settings
    return settings.bot_token


def create_bot_components(bot_token: Optional[str] = None) -> BotComponents:
    """
    Создать все компоненты бота.

    Args:
        bot_token: Токен бота (если не указан, получается автоматически)

    Returns:
        BotComponents: Контейнер со всеми компонентами бота
    """
    from bot.core.config import settings

    if bot_token is None:
        bot_token = get_bot_token()

    # Инициализация основных компонентов
    api = API(token=Token(bot_token))
    bot = Telegrinder(api)

    # Вспомогательные объекты
    fmt = telegrinder.tools.HTMLFormatter
    wm = telegrinder.WaiterMachine()
    client = AiohttpClient()
    ctx = CtxStorage()
    logger = AlignedLogger()
    tz = settings.get_timezone()
    menu_manager = MenuManager(api)

    # Удаляем логирование telegrinder для использования кастомного логгера
    telegrinder.logger.remove()

    return BotComponents(
        api=api,
        bot=bot,
        fmt=fmt,
        wm=wm,
        client=client,
        ctx=ctx,
        logger=logger,
        tz=tz,
        menu_manager=menu_manager,
    )


__all__ = ['BotComponents', 'get_bot_token', 'create_bot_components']
