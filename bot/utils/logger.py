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


class LoggerHandler:

    @staticmethod
    def log_pre_loading_handler(handlers: List[Dispatch]):
        """Логирует начало загрузки хендлеров"""
        logger.info("Starting handler setup...", section="HANDLERS")
        LoggerHandler.log_handler_loading(handlers)

    @staticmethod
    def log_post_loading_handler(handlers: List[Dispatch]):
        """Логирует завершение загрузки хендлеров"""
        logger.success(f"Successfully loaded {len(handlers)} dispatchers", section="HANDLERS")

        total_message_handlers = sum(len(dp.message.handlers) for dp in handlers)
        total_callback_handlers = sum(len(dp.callback_query.handlers) for dp in handlers)

        logger.success(
            f"Total handlers: {total_message_handlers} message, {total_callback_handlers} callback",
            section="HANDLERS"
        )

    @staticmethod
    def log_handler_loading(handlers: List[Dispatch]):
        """Логирует информацию о загружаемых хендлерах"""
        for i, dp in enumerate(handlers):
            # Получаем метаданные диспетчера
            dp_name = getattr(dp, 'title', f'Dispatcher_{i}')

            log_message_dispatcher = f"Loading handlers <"

            # Логируем количество хендлеров каждого типа
            message_count = len(dp.message.handlers)
            callback_count = len(dp.callback_query.handlers)

            if message_count >= 0:
                log_message_dispatcher += f"{message_count} message"
            if callback_count >= 0:
                log_message_dispatcher += f"|{callback_count} callback"
            log_message_dispatcher += f"> dispatcher - [{dp_name}]"
            logger.success(log_message_dispatcher, section="HANDLERS")

    @staticmethod
    def get_dispatcher_info(dp: Dispatch, index: int) -> dict:
        """Получает информацию о диспетчере"""
        return {
            'title': getattr(dp, 'title', f'Dispatcher_{index}'),
            'description': getattr(dp, 'description', 'No description'),
            'folder': getattr(dp, 'folder', 'unknown'),
            'message_handlers': len(dp.message.handlers),
            'callback_handlers': len(dp.callback_query.handlers)
        }
