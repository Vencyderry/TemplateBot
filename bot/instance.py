"""
Инициализация и управление глобальным экземпляром BotApplication.

Использует contextvars для безопасного хранения экземпляра приложения.
Это позволяет получать доступ к app из любого места без передачи параметров.

Рекомендуемое использование:
    from bot.core.context import get_app  # Вместо bot.instance

    app = get_app()
    app.logger.info("Hello!")

Для обратной совместимости также доступны:
    from bot.instance import get_app  # Старый способ (работает)
"""
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from bot.core.application import BotApplication


def get_app() -> 'BotApplication':
    """
    Получить экземпляр приложения из контекста.

    Это прокси-функция для обратной совместимости.
    Рекомендуется использовать bot.core.context.get_app() напрямую.

    Returns:
        BotApplication: Экземпляр приложения

    Raises:
        RuntimeError: Если приложение не было инициализировано
    """
    from bot.core.context import get_app as get_app_from_context
    return get_app_from_context()


def init_app(
    log_dir: str = "logs",
    skip_updates: bool = True,
    bot_token: Optional[str] = None
) -> 'BotApplication':
    """
    Инициализировать глобальный экземпляр приложения.

    Создает экземпляр BotApplication и устанавливает его в контекст,
    делая доступным из любого места через get_app().

    Args:
        log_dir: Директория для логов
        skip_updates: Пропускать накопленные обновления
        bot_token: Токен бота

    Returns:
        BotApplication: Инициализированный экземпляр приложения

    Example:
        >>> from bot.instance import init_app
        >>> app = init_app(log_dir="logs", skip_updates=False)
        >>> app.setup(handlers=handlers, middlewares=middlewares)
        >>> app.run()
    """
    from bot.core.application import BotApplication
    from bot.core.context import set_app

    # Создаем экземпляр приложения
    app = BotApplication(
        log_dir=log_dir,
        skip_updates=skip_updates,
        bot_token=bot_token
    )

    # Устанавливаем в контекст для доступа из любого места
    set_app(app)

    return app


__all__ = ['init_app', 'get_app']
