import datetime
import inspect
import time

from functools import wraps
from pathlib import Path
from typing import Union, Tuple, Optional
from telegrinder import Message, CallbackQuery, Dispatch as BaseDispatch
from telegrinder.types import User as TelegrinderUser, ChatType
from telegrinder.types import Chat as TelegrinderChat

from bot.managers import StatsManager
from bot.instance import get_app
from bot.models.models import User
from bot.rules.command_rule import CommandRule


class Dispatch(BaseDispatch):
    """Кастомный диспетчер с метаданными для логирования"""

    def __init__(self,
                 title: Optional[str] = None,
                 description: Optional[str] = None,
                 permission: str = User.DEFAULT,
                 track_stat: bool = True):
        super().__init__()

        # Автоматически определяем папку если не указан title
        frame = inspect.currentframe().f_back
        filename = frame.f_code.co_filename
        if not title:
            title = Path(filename).parent.name

        self.title = title
        self.description = description or f"Handlers for {title}"
        self.folder = Path(filename).parent.name if 'filename' in locals() else title
        self.permission = permission
        self.track_stat = track_stat

    async def log_execution(self,
                            event: Union[Message, CallbackQuery],
                            db_user: User = None,
                            success: bool = True,
                            execution_time: float = None):
        """Логирование выполнения команд"""
        app = get_app()
        try:

            from_user, chat = self._extract_from_and_chat(event)
            if not from_user:
                return

            type_event = "MESSAGE" if isinstance(event, Message) else "CALLBACK_QUERY"
            log_message = f"Executed <{self.title}.{type_event}>"

            if db_user:
                username = f"@{db_user.username}" if db_user.username else db_user.telegram_id

                log_message += f" by {db_user.first_name} ({username})"

            if execution_time:
                time_ms = round(execution_time * 1000)
                log_message += f" in {time_ms}ms"

            if success:
                app.logger.info(log_message, "command", depth=3)
            else:
                app.logger.error(log_message, "command", depth=3)

        except Exception as e:
            app.logger.error(f"Logging failed for {self.title} {e}", depth=3)

    async def mark_statistics(self, event: Union[Message, CallbackQuery]):
        """Автоматический учет статистики"""
        if not self.track_stat:
            return

        try:
            from_user, chat = self._extract_from_and_chat(event)
            if not from_user:
                return

            # Используем автоматическое определение статистики через StatsManager
            StatsManager.track_user_action(self.title, from_user.id)

        except Exception as e:
            get_app().logger.error(
                f"❌ Statistics tracking failed for {self.title}: {e}", "statistics")

    def wrap_handler(self,
                     permission: str = User.DEFAULT,
                     track_stat: bool = None,
                     is_main_command: bool = False,
                     is_final_command: bool = False,
                     is_full_command: bool = False):
        """Декоратор с улучшенным логированием
        :param is_full_command: True - команда является полной (главной и финальной)
        :param is_final_command: True - после выполнения данная команда будет логировать и обновлять статистику
        :param is_main_command: True - после выполнения данная команда будет сбрасывать все стейты
        :param permission: Права доступа
        :type track_stat: bool Флаг для учета статистики
        """
        if track_stat is None:
            track_stat = self.track_stat

        if is_full_command:
            is_main_command = True
            is_final_command = True

        def decorator(func):
            @wraps(func)
            async def wrapper(event: Union[Message, CallbackQuery], *args, **kwargs):
                app = get_app()

                start_time = time.time()
                db_user = None
                success = False
                chat = None

                try:
                    from_user, chat = self._extract_from_and_chat(event)
                    if not from_user:
                        return None

                    db_user, created = User.get_or_create_user(from_user.id, from_user.first_name,
                                                               from_user.username.unwrap_or_none(),
                                                               from_user.last_name.unwrap_or_none())

                    # Проверка прав
                    if not self._check_permission(db_user, self.permission, permission):
                        if self.permission == User.ADMIN or permission == User.ADMIN:
                            if isinstance(event, Message):
                                await event.answer("❌ Нет прав доступа")
                            elif isinstance(event, CallbackQuery):
                                await event.answer("❌ Нет прав доступа")
                        return None


                    # Обновляем активность
                    db_user.last_activity = datetime.datetime.now(tz=app.tz)
                    db_user.state = self.title if is_main_command else db_user.state
                    db_user.save()

                    kwargs['app'] = app
                    kwargs['user'] = db_user
                    kwargs = CommandRule.extract_arguments_from_ctx(event, **kwargs)  # ищем аргументы в хранилище

                    # Выполняем функцию
                    result = await func(event, *args, **kwargs)
                    success = True

                    return result

                except Exception as e:
                    execution_time = time.time() - start_time
                    await self.log_execution(
                        event, db_user, False,
                        execution_time=execution_time
                    )
                    raise e

                finally:
                    execution_time = time.time() - start_time

                    if is_main_command:
                        if chat.type == ChatType.PRIVATE:
                            await app.menu_manager.clean_chat(event, db_user)

                    # Учитываем статистику и логируем если команда является финальной
                    if is_final_command:
                        await self.log_execution(
                            event, db_user, success,
                            execution_time=execution_time
                        )

                        if track_stat and success:
                            await self.mark_statistics(event)

            return wrapper

        return decorator

    @staticmethod
    def _check_permission(db_user, global_permission, local_permission):
        """Проверка прав пользователя"""
        if db_user.role == User.ADMIN:
            return True

        global_ok = (global_permission == User.DEFAULT) or (db_user.role == global_permission)
        local_ok = (local_permission == User.DEFAULT) or (db_user.role == local_permission)

        return global_ok and local_ok

    @staticmethod
    def _extract_from_and_chat(event) -> Tuple[Union[TelegrinderUser, None], Union[TelegrinderChat, None]]:
        """
        Извлечение отправителя и чата(from_ chat) из объекта (Message или CallbackQuery).

        :param event: Объект для извлечения отправителя.
        :return: Отправитель и чат(from_ chat) или None.
        """
        if isinstance(event, Message):
            return event.from_.unwrap(), event.chat
        elif isinstance(event, CallbackQuery):
            return event.from_, event.chat.unwrap()
        return None, None
