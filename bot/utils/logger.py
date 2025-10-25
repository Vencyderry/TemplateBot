import inspect
import sys
from pathlib import Path
from loguru import logger
from typing import Optional, List

from telegrinder import Dispatch

from bot.core.config import settings


class AlignedLogger:
    max_length_caller_info = 55
    default_depth = 2  # сколько фреймов будут пропускаться при логировании по умолчанию

    def __init__(self, default_section: str = "BOT"):
        self.default_section = default_section

    def log(self, level: str, message: str, section: Optional[str] = None, depth: Optional[int] = default_depth):
        """Универсальный метод логирования с правильным местом вызова"""
        section_name = section or self.default_section

        # Используем depth, чтобы пропустить фреймы этого класса
        logger.opt(depth=depth).bind(section=section_name.upper()).log(level, message)

    def info(self, message: str, section: Optional[str] = None, depth: Optional[int] = default_depth):
        self.log("INFO", message, section, depth)

    def error(self, message: str, section: Optional[str] = None, depth: Optional[int] = default_depth):
        self.log("ERROR", message, section, depth)

    def warning(self, message: str, section: Optional[str] = None, depth: Optional[int] = default_depth):
        self.log("WARNING", message, section, depth)

    def debug(self, message: str, section: Optional[str] = None, depth: Optional[int] = default_depth):
        self.log("DEBUG", message, section, depth)

    def success(self, message: str, section: Optional[str] = None, depth: Optional[int] = default_depth):
        self.log("SUCCESS", message, section, depth)

    @staticmethod
    def section(section_name: str):
        return AlignedLogger(section_name)


def custom_filter(record):
    """Фильтр для обработки и форматирования записей лога"""
    if "section" not in record["extra"]:
        record["extra"]["section"] = ""

    # Если это telegrinder, добавляем секцию
    if record["name"].startswith("telegrinder"):
        record["extra"]["section"] = "TELEGRINDER"

    # Собираем информацию о месте вызова в одну строку
    caller_info = f"{record['name']}:{record['function']}:{record['line']}"

    if len(caller_info) > AlignedLogger.max_length_caller_info:
        caller_info = caller_info[:(AlignedLogger.max_length_caller_info - 3)] + "..."
    else:
        caller_info = caller_info.ljust(AlignedLogger.max_length_caller_info)

    record["extra"]["caller_formatted"] = caller_info
    return True


def setup_logging(log_dir: str = "logs", enable_rotation: bool = True):
    """
    Настраивает файловый вывод и stdout/stderr с улучшенным форматированием
    """
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)

    # Убираем все стандартные обработчики
    logger.remove()

    console_format = (
        "<level>{level: <8}</level> | "
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<cyan>{extra[caller_formatted]}</cyan> | "
        "<blue>{extra[section]:<11}</blue> | "
        "<level>{message}</level>"
    )

    file_format = (
        "{time:YYYY-MM-DD HH:mm:ss} | "
        "{level: <8} | "
        "{extra[caller_formatted]} | "
        "{extra[section]:<11} | "
        "{message}"
    )

    logger.add(
        sys.stdout,
        format=console_format,
        level=settings.log_level,
        colorize=True,
        backtrace=True,
        diagnose=True,
        filter=custom_filter
    )

    logger.add(
        log_path / "info.log",
        format=file_format,
        level="DEBUG",
        rotation="10 MB" if enable_rotation else None,
        retention="30 days",
        compression="zip",
        backtrace=True,
        diagnose=True,
        enqueue=True,
        filter=custom_filter
    )

    logger.add(
        log_path / "errors.log",
        format=file_format,
        level="ERROR",
        rotation="5 MB" if enable_rotation else None,
        retention="60 days",
        compression="zip",
        backtrace=True,
        diagnose=True,
        enqueue=True,
        filter=custom_filter
    )


class ComponentLogger:
    """Универсальный логгер для компонентов приложения (handlers, middlewares, tasks)"""

    # --- Handlers ---
    @staticmethod
    def log_pre_loading_handlers(handlers: List[Dispatch]):
        """Логирует начало загрузки хендлеров"""
        logger.info("Starting handler setup...", section="HANDLERS")
        ComponentLogger._log_handler_details(handlers)

    @staticmethod
    def log_post_loading_handlers(handlers: List[Dispatch]):
        """Логирует завершение загрузки хендлеров"""
        logger.success(f"Successfully loaded {len(handlers)} dispatchers", section="HANDLERS")

        total_message_handlers = sum(len(dp.message.handlers) for dp in handlers)
        total_callback_handlers = sum(len(dp.callback_query.handlers) for dp in handlers)

        logger.success(
            f"Total handlers: {total_message_handlers} message, {total_callback_handlers} callback",
            section="HANDLERS"
        )

    @staticmethod
    def _log_handler_details(handlers: List[Dispatch]):
        """Логирует детальную информацию о загружаемых хендлерах"""
        for i, dp in enumerate(handlers):
            dp_name = getattr(dp, 'title', f'Dispatcher_{i}')
            message_count = len(dp.message.handlers)
            callback_count = len(dp.callback_query.handlers)

            log_message = f"Loading handlers <{message_count} message|{callback_count} callback> dispatcher - [{dp_name}]"
            logger.success(log_message, section="HANDLERS")

    # --- Middlewares ---
    @staticmethod
    def log_middlewares(message_middlewares: List, callback_middlewares: List):
        """Логирует загрузку middlewares"""
        logger.info("Starting middleware setup...", section="MIDDLEWARES")

        # Логируем message middlewares
        for middleware in message_middlewares:
            middleware_name = middleware.__class__.__name__
            logger.success(f"Loading message middleware: {middleware_name}", section="MIDDLEWARES")

        # Логируем callback middlewares
        for middleware in callback_middlewares:
            middleware_name = middleware.__class__.__name__
            logger.success(f"Loading callback middleware: {middleware_name}", section="MIDDLEWARES")

        # Итоговая статистика
        logger.success(
            f"Successfully loaded {len(message_middlewares)} message, {len(callback_middlewares)} callback middlewares",
            section="MIDDLEWARES"
        )

    # --- Background Tasks ---
    @staticmethod
    def log_background_tasks(tasks: List):
        """Логирует регистрацию фоновых задач"""
        logger.info("Registering background tasks...", section="TASKS")

        for task in tasks:
            task_name = getattr(task, '__name__', str(task))
            logger.success(f"Registered task: {task_name}", section="TASKS")

        logger.success(f"Successfully registered {len(tasks)} background tasks", section="TASKS")


# Обратная совместимость
class LoggerHandler(ComponentLogger):
    """Deprecated: используй ComponentLogger"""

    @staticmethod
    def log_pre_loading_handler(handlers: List[Dispatch]):
        ComponentLogger.log_pre_loading_handlers(handlers)

    @staticmethod
    def log_post_loading_handler(handlers: List[Dispatch]):
        ComponentLogger.log_post_loading_handlers(handlers)
