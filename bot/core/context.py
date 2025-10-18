"""
Контекстное хранилище для глобального доступа к компонентам приложения.

Использует contextvars для безопасного доступа в async окружении.
Это позволяет получать app из любого места без передачи параметров,
при этом сохраняя изоляцию между параллельными запросами.

Пример использования:
    # При инициализации (один раз):
    from bot.core.context import set_app
    app = BotApplication(...)
    set_app(app)

    # В любом месте кода:
    from bot.core.context import get_app
    app = get_app()
    app.logger.info("Hello from anywhere!")
"""
from contextvars import ContextVar
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from bot.core.application import BotApplication

# Контекстная переменная для хранения экземпляра приложения
_app_context: ContextVar[Optional['BotApplication']] = ContextVar('app', default=None)


def set_app(app: 'BotApplication') -> None:
    """
    Установить экземпляр приложения в контекст.

    Вызывается один раз при инициализации приложения.

    Args:
        app: Экземпляр BotApplication для установки в контекст

    Example:
        >>> from bot.core.application import BotApplication
        >>> from bot.core.context import set_app
        >>> app = BotApplication()
        >>> set_app(app)
    """
    _app_context.set(app)


def get_app() -> 'BotApplication':
    """
    Получить экземпляр приложения из контекста.

    Безопасно для использования в async/await коде.
    Может вызываться из любого места в коде после инициализации.

    Returns:
        BotApplication: Экземпляр приложения

    Raises:
        RuntimeError: Если приложение не было инициализировано

    Example:
        >>> from bot.core.context import get_app
        >>> app = get_app()
        >>> app.logger.info("Logging from anywhere!")
    """
    app = _app_context.get()
    if app is None:
        raise RuntimeError(
            "Application context not initialized. "
            "Make sure to call set_app() during initialization."
        )
    return app


def try_get_app() -> Optional['BotApplication']:
    """
    Попытаться получить экземпляр приложения из контекста.

    В отличие от get_app(), не выбрасывает исключение,
    если приложение не инициализировано.

    Returns:
        BotApplication | None: Экземпляр приложения или None

    Example:
        >>> from bot.core.context import try_get_app
        >>> app = try_get_app()
        >>> if app:
        >>>     app.logger.info("App is available")
    """
    return _app_context.get()


__all__ = ['set_app', 'get_app', 'try_get_app']
