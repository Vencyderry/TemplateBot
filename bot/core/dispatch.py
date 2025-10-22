"""
Кастомный диспетчер с архитектурой на основе принципов SOLID.

Основные улучшения:
- Разделение ответственности (SRP)
- Dependency Injection для тестируемости
- Protocol-based design для расширяемости
- Полная типизация
- Контекстные менеджеры для управления ресурсами
"""

import datetime
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from pathlib import Path
from typing import (
    Any,
    AsyncIterator,
    Awaitable,
    Callable,
    Optional,
    Protocol,
    Tuple,
    TypeVar,
    Union,
)

from telegrinder import CallbackQuery, Dispatch as BaseDispatch, Message
from telegrinder.types import Chat as TelegrinderChat
from telegrinder.types import ChatType
from telegrinder.types import User as TelegrinderUser

from bot.instance import get_app
from bot.managers import StatsManager
from bot.models.models import User
from bot.rules.command_rule import CommandRule

# Type aliases
TEvent = Union[Message, CallbackQuery]
THandler = Callable[..., Awaitable[Any]]


class CommandExecutionMode(Enum):
    """Режимы выполнения команды."""

    INTERMEDIATE = "intermediate"  # Промежуточная команда в цепочке
    FINAL = "final"  # Финальная команда (логируется и учитывается в статистике)
    MAIN = "main"  # Главная команда (сбрасывает стейт)
    FULL = "full"  # Полная команда (main + final)


@dataclass(frozen=True)
class EventContext:
    """Неизменяемый контекст события с полной информацией."""

    event: TEvent
    telegram_user: TelegrinderUser
    chat: TelegrinderChat
    db_user: User
    is_new_user: bool
    app: Any  # Application instance

    @property
    def event_type(self) -> str:
        """Тип события для логирования."""
        return "MESSAGE" if isinstance(self.event, Message) else "CALLBACK_QUERY"


@dataclass
class ExecutionResult:
    """Результат выполнения handler'а."""

    success: bool
    execution_time: float
    result: Any = None
    error: Optional[Exception] = None
    context: Optional[EventContext] = None
    permission_denied: bool = False


class EventExtractor(Protocol):
    """Протокол для извлечения данных из события."""

    def extract(self, event: TEvent) -> Tuple[Optional[TelegrinderUser], Optional[TelegrinderChat]]:
        """Извлекает пользователя и чат из события."""
        ...


class PermissionChecker(Protocol):
    """Протокол для проверки прав доступа."""

    def check(self, user: User, required_permission: str) -> bool:
        """Проверяет права доступа пользователя."""
        ...


class ExecutionLogger(Protocol):
    """Протокол для логирования выполнения команд."""

    async def log(
        self,
        handler_title: str,
        context: EventContext,
        result: ExecutionResult,
    ) -> None:
        """Логирует выполнение команды."""
        ...


class StatisticsTracker(Protocol):
    """Протокол для учета статистики."""

    async def track(
        self,
        handler_title: str,
        context: EventContext,
    ) -> None:
        """Учитывает статистику выполнения."""
        ...


# === Конкретные реализации ===


class DefaultEventExtractor:
    """Стандартная реализация извлечения данных из события."""

    def extract(
        self, event: TEvent
    ) -> Tuple[Optional[TelegrinderUser], Optional[TelegrinderChat]]:
        """Извлекает from_user и chat из Message или CallbackQuery."""
        if isinstance(event, Message):
            return event.from_.unwrap(), event.chat  # type: ignore
        elif isinstance(event, CallbackQuery):
            return event.from_, event.chat.unwrap()
        return None, None


class RoleBasedPermissionChecker:
    """Проверка прав на основе ролей пользователя."""

    def __init__(self, global_permission: str):
        self.global_permission = global_permission

    def check(self, user: User, local_permission: str) -> bool:
        """
        Проверяет права доступа.

        Логика:
        - ADMIN имеет доступ ко всему
        - Иначе проверяем соответствие глобальным и локальным правам
        """
        if user.role == User.ADMIN:
            return True

        global_ok = (
            self.global_permission == User.DEFAULT
            or user.role == self.global_permission
        )
        local_ok = (
            local_permission == User.DEFAULT
            or user.role == local_permission
        )

        return global_ok and local_ok


class DefaultExecutionLogger:
    """Стандартная реализация логирования."""

    async def log(
        self,
        handler_title: str,
        context: EventContext,
        result: ExecutionResult,
    ) -> None:
        """Логирует выполнение команды с деталями."""
        try:
            app = context.app
            user = context.db_user

            # Формируем сообщение
            username = f"@{user.username}" if user.username else str(user.telegram_id)
            time_ms = round(result.execution_time * 1000)

            log_message = (
                f"Executed <{handler_title}.{context.event_type}> "
                f"by {user.first_name} ({username}) "
                f"in {time_ms}ms"
            )

            # Логируем в зависимости от результата
            if result.success:
                app.logger.info(log_message, "command", depth=3)
            else:
                app.logger.error(log_message, "command", depth=3)

        except Exception as e:
            context.app.logger.error(
                f"Logging failed for {handler_title}: {e}",
                depth=3
            )


class DefaultStatisticsTracker:
    """Стандартная реализация учета статистики."""

    async def track(
        self,
        handler_title: str,
        context: EventContext,
    ) -> None:
        """Учитывает статистику через StatsManager."""
        try:
            StatsManager.track_user_action(
                handler_title,
                context.telegram_user.id
            )
        except Exception as e:
            context.app.logger.error(
                f"Statistics tracking failed for {handler_title}: {e}",
                "statistics"
            )


class Dispatch(BaseDispatch):
    """
    Кастомный диспетчер.

    Принципы:
    - Single Responsibility: каждый компонент отвечает за одну вещь
    - Dependency Injection: все зависимости передаются извне
    - Open/Closed: легко расширяется через протоколы
    - Protocol-based: использует Protocol для слабой связанности
    """

    def __init__(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
        permission: str = User.DEFAULT,
        track_stat: bool = True,
        # Dependency Injection
        event_extractor: Optional[EventExtractor] = None,
        permission_checker: Optional[PermissionChecker] = None,
        logger: Optional[ExecutionLogger] = None,
        stats_tracker: Optional[StatisticsTracker] = None,
    ):
        super().__init__()

        # Метаданные
        self.title = title or self._infer_title()
        self.description = description or f"Handlers for {self.title}"
        self.permission = permission
        self.track_stat = track_stat

        # Зависимости (с дефолтными реализациями)
        self._event_extractor = event_extractor or DefaultEventExtractor()
        self._permission_checker = permission_checker or RoleBasedPermissionChecker(permission)
        self._logger = logger or DefaultExecutionLogger()
        self._stats_tracker = stats_tracker or DefaultStatisticsTracker()

    @staticmethod
    def _infer_title() -> str:
        """Определяет title на основе имени родительской директории."""
        import inspect

        frame = inspect.currentframe()
        if frame and frame.f_back:
            filename = frame.f_back.f_code.co_filename
            return Path(filename).parent.name
        return "unknown"

    @asynccontextmanager
    async def _execution_context(
        self, event: TEvent
    ) -> AsyncIterator[EventContext]:
        """
        Контекстный менеджер для подготовки контекста выполнения.

        Автоматически:
        - Извлекает пользователя и чат
        - Создает/получает пользователя из БД
        - Обновляет активность
        """
        # Извлекаем данные из события
        telegram_user, chat = self._event_extractor.extract(event)

        if not telegram_user or not chat:
            raise ValueError("Unable to extract user or chat from event")

        # Получаем/создаем пользователя в БД
        db_user, is_new = User.get_or_create_user(
            telegram_user.id,
            telegram_user.first_name,
            telegram_user.username.unwrap_or_none(),
            telegram_user.last_name.unwrap_or_none(),
        )

        # Обновляем время активности
        app = get_app()
        db_user.last_activity = datetime.datetime.now(tz=app.tz)

        try:
            yield EventContext(
                event=event,
                telegram_user=telegram_user,
                chat=chat,
                db_user=db_user,
                is_new_user=is_new,
                app=app,
            )
        finally:
            db_user.save()

    async def _check_permissions(
        self,
        context: EventContext,
        local_permission: str,
    ) -> bool:
        """Проверяет права доступа и отправляет сообщение при отказе."""
        has_permission = self._permission_checker.check(
            context.db_user,
            local_permission
        )

        if not has_permission:
            await context.event.answer("❌ Нет прав доступа")

        return has_permission

    async def _update_user_state(
        self,
        context: EventContext,
        mode: CommandExecutionMode,
    ) -> None:
        """Обновляет состояние пользователя в зависимости от режима."""
        if mode in (CommandExecutionMode.MAIN, CommandExecutionMode.FULL):
            context.db_user.state = self.title

    async def _cleanup_on_main_command(
        self,
        context: EventContext,
        mode: CommandExecutionMode,
    ) -> None:
        """Очищает чат при выполнении главной команды."""
        if mode not in (CommandExecutionMode.MAIN, CommandExecutionMode.FULL):
            return

        if context.chat.type != ChatType.PRIVATE:
            return

        await context.app.menu_manager.clean_chat(
            context.event,
            context.db_user
        )

    async def _log_and_track(
        self,
        context: EventContext,
        result: ExecutionResult,
        mode: CommandExecutionMode,
        track_stat: bool,
    ) -> None:
        """Логирует и учитывает статистику для финальных команд."""
        if mode not in (CommandExecutionMode.FINAL, CommandExecutionMode.FULL):
            return

        # Пропускаем логирование если отказано в доступе
        if result.permission_denied:
            return

        # Логируем выполнение
        await self._logger.log(self.title, context, result)

        # Учитываем статистику только при успехе
        if track_stat and result.success:
            await self._stats_tracker.track(self.title, context)

    def wrap_handler(
        self,
        permission: str = User.DEFAULT,
        track_stat: Optional[bool] = None,
        mode: CommandExecutionMode = CommandExecutionMode.INTERMEDIATE,
    ) -> Callable[[THandler], THandler]:
        """
        Декоратор для обработчиков.

        Args:
            permission: Уровень прав доступа
            track_stat: Флаг учета статистики (None = использовать из __init__)
            mode: Режим выполнения команды

        Режимы:
            INTERMEDIATE - промежуточная команда (без логирования)
            FINAL - финальная команда (логируется и учитывается)
            MAIN - главная команда (сбрасывает стейт и чистит чат)
            FULL - полная команда (MAIN + FINAL)
        """
        if track_stat is None:
            track_stat = self.track_stat

        def decorator(func: THandler) -> THandler:
            @wraps(func)
            async def wrapper(event: TEvent, *args: Any, **kwargs: Any) -> Any:
                start_time = time.time()
                result = ExecutionResult(success=False, execution_time=0.0)

                try:
                    # Создаем контекст выполнения
                    async with self._execution_context(event) as context:
                        result.context = context

                        # Проверяем права доступа
                        if not await self._check_permissions(context, permission):
                            result.permission_denied = True
                            return None

                        # Обновляем состояние пользователя
                        await self._update_user_state(context, mode)

                        # Подготавливаем аргументы для handler'а
                        kwargs['app'] = context.app
                        kwargs['user'] = context.db_user
                        kwargs = CommandRule.extract_arguments_from_ctx(event, **kwargs)

                        # Выполняем handler
                        result.result = await func(event, *args, **kwargs)
                        result.success = True

                        return result.result

                except Exception as e:
                    result.error = e
                    result.success = False
                    raise

                finally:
                    result.execution_time = time.time() - start_time

                    # Выполняем cleanup и логирование
                    if result.context:
                        await self._cleanup_on_main_command(result.context, mode)
                        await self._log_and_track(
                            result.context,
                            result,
                            mode,
                            track_stat
                        )

            return wrapper  # type: ignore

        return decorator
