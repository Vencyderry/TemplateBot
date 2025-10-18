"""
Конфигурация приложения через Pydantic Settings.

Переменные читаются из .env файла или переменных окружения.
Приоритет: переменные окружения > .env файл > значения по умолчанию
"""
from functools import lru_cache
from pathlib import Path
from typing import Optional

import pytz
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Настройки приложения с валидацией через Pydantic.

    Все настройки автоматически загружаются из .env файла или переменных окружения.
    """

    # === Telegram Bot Configuration ===
    bot_token: str = Field(
        ...,  # обязательное поле
        alias='BOT_TOKEN',
        description="Токен Telegram бота"
    )

    # === Admin Configuration ===
    chat_id_admin_group: int = Field(
        default=-1000000000000,
        alias='CHAT_ID_ADMIN_GROUP',
        description="ID группы администраторов"
    )

    # === Project Configuration ===
    project_name: str = Field(
        default='template_bot',
        alias='PROJECT_NAME',
        description="Название проекта"
    )

    # === Database Configuration ===
    database_path: Optional[str] = Field(
        default=None,
        alias='DATABASE_PATH',
        description="Путь к базе данных SQLite"
    )

    # === Timezone Configuration ===
    timezone: str = Field(
        default='Europe/Moscow',
        alias='TIMEZONE',
        description="Часовой пояс приложения"
    )

    # === Logging Configuration ===
    log_level: str = Field(
        default='INFO',
        alias='LOG_LEVEL',
        description="Уровень логирования (DEBUG, INFO, WARNING, ERROR)"
    )

    log_dir: str = Field(
        default='logs',
        alias='LOG_DIR',
        description="Директория для хранения логов"
    )

    # === Bot Behavior ===
    skip_updates: bool = Field(
        default=False,
        alias='SKIP_UPDATES',
        description="Пропускать ли накопленные обновления при запуске"
    )

    # Настройки загрузки конфигурации
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'  # игнорировать лишние поля в .env
    )

    @field_validator('bot_token')
    @classmethod
    def validate_bot_token(cls, v: str) -> str:
        """Валидация формата токена бота."""
        if not v or v == 'your_bot_token_here':
            raise ValueError(
                "BOT_TOKEN не установлен! "
            )
        if v.count(":") != 1 or not v.split(":")[0].isdigit():
            raise ValueError("Неверный формат токена бота")
        return v

    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Валидация уровня логирования."""
        allowed = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        v_upper = v.upper()
        if v_upper not in allowed:
            raise ValueError(f"log_level должен быть одним из: {allowed}")
        return v_upper

    def get_timezone(self) -> pytz.tzinfo.BaseTzInfo:
        """Получить объект timezone."""
        return pytz.timezone(self.timezone)

    def get_database_path(self) -> str:
        """
        Получить путь к базе данных с автоматическим определением.

        Приоритет:
        1. Явно указанный DATABASE_PATH
        2. Docker путь (/app/{project_name}.db)
        3. Локальный путь (корень проекта)
        """
        import os

        # Если путь явно указан
        if self.database_path:
            return self.database_path

        db_filename = f"{self.project_name}.db"

        # Проверяем Docker окружение
        docker_path = f'/app/{db_filename}'
        if os.path.exists('/app'):
            return docker_path

        # Локальный путь (корень проекта)
        project_root = Path(__file__).parent.parent.parent
        return str(project_root / db_filename)


@lru_cache()
def get_settings() -> Settings:
    """
    Получить singleton экземпляр настроек.

    Используется lru_cache для кэширования, чтобы не читать .env повторно.
    """
    return Settings()


# Экспортируем экземпляр настроек для обратной совместимости
settings = get_settings()
