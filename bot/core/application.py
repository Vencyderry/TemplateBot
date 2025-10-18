"""
Класс для удобного запуска и настройки Telegram бота.
"""
from typing import List, Optional, Callable
from telegrinder import Dispatch

from bot.core.components import create_bot_components
from bot.middlewares.registry import Middlewares
from bot.utils import setup_logging, LoggerHandler
from bot.models.database import start_database


class BotApplication:
    """
    Главный класс приложения для настройки и запуска Telegram бота.

    Инкапсулирует всю логику инициализации:
    - Настройка логирования
    - Инициализация базы данных
    - Регистрация хендлеров
    - Подключение middleware
    - Добавление фоновых задач

    Пример использования:
        app = BotApplication()
        app.setup()
        app.run()
    """

    def __init__(
        self,
        log_dir: str = "logs",
        skip_updates: bool = True,
        bot_token: Optional[str] = None
    ):
        """
        Инициализация приложения.

        Args:
            log_dir: Директория для хранения логов
            skip_updates: Пропускать ли накопленные обновления при запуске
            bot_token: Токен бота (если не указан, берется из переменных окружения или config.py)
        """
        self.log_dir = log_dir
        self.skip_updates = skip_updates

        # Инициализация всех компонентов бота
        components = create_bot_components(bot_token)

        # Присваиваем компоненты как атрибуты класса
        self.api = components.api
        self.bot = components.bot
        self.fmt = components.fmt
        self.wm = components.wm
        self.client = components.client
        self.ctx = components.ctx
        self.logger = components.logger
        self.tz = components.tz
        self.menu_manager = components.menu_manager

        # Внутренние переменные
        self._handlers: List[Dispatch] = []
        self._middlewares: Optional[Middlewares] = None
        self._background_tasks: List[Callable] = []
        self._is_setup = False

    def setup_logging(self) -> 'BotApplication':
        """Настройка логирования."""
        setup_logging(self.log_dir)
        self.logger.info("Starting JapanLife Bot...")
        return self

    def setup_database(self) -> 'BotApplication':
        """Инициализация базы данных."""
        start_database()
        return self

    def register_handlers(self, handlers: List[Dispatch]) -> 'BotApplication':
        """
        Регистрация обработчиков событий.

        Args:
            handlers: Список диспетчеров с обработчиками
        """
        self._handlers = handlers

        LoggerHandler.log_pre_loading_handler(handlers)

        for dp in handlers:
            self.bot.dispatch.message.handlers.extend(dp.message.handlers)
            self.bot.dispatch.callback_query.handlers.extend(dp.callback_query.handlers)

        LoggerHandler.log_post_loading_handler(handlers)

        return self

    def setup_middlewares(self, middlewares: Middlewares) -> 'BotApplication':
        """Настройка middleware."""

        self._middlewares = middlewares

        # Добавляем middleware для сообщений
        for middleware in middlewares.message:
            self.bot.on.message.middlewares.append(middleware)

        # Добавляем middleware для callback-запросов
        for middleware in middlewares.callback_query:
            self.bot.on.callback_query.middlewares.append(middleware)

        return self

    def add_background_task(self, task: Callable) -> 'BotApplication':
        """
        Добавление фоновой задачи.

        Args:
            task: Асинхронная функция для выполнения в фоне
        """
        self._background_tasks.append(task)
        self.bot.loop_wrapper.add_task(task)
        return self

    def setup(self, handlers: Optional[List[Dispatch]] = None, middlewares: Middlewares = None) -> 'BotApplication':
        """
        Полная настройка приложения.

        Args:
            handlers: Список обработчиков (опционально)
            middlewares: Список предобработчиков (опционально)
        """
        if self._is_setup:
            self.logger.warning("Application already setup. Skipping...")
            return self

        self.setup_logging()
        self.setup_database()

        if handlers is not None:
            self.register_handlers(handlers)

        if middlewares is not None:
            self.setup_middlewares(middlewares)

        self._is_setup = True
        self.logger.success("Bot successfully configured")

        return self

    def run(self) -> None:
        """Запуск бота."""
        if not self._is_setup:
            raise RuntimeError(
                "Application is not setup. Call setup() before run()"
            )

        self.logger.success("Bot started successfully")
        self.bot.run_forever(skip_updates=self.skip_updates)

    def run_polling(self) -> None:
        """Альтернативное название для run() для совместимости."""
        self.run()
