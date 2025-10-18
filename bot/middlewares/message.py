import traceback

from telegrinder import ABCMiddleware, Message
from telegrinder.types import ChatType

from bot.instance import get_app
from bot.models.models import User


class RegistrationMiddleware(ABCMiddleware):
    async def pre(self, event: Message) -> bool | None:

        app = get_app()
        try:
            if event.from_.unwrap_or_none() is not None:  # Если сообщение не пустое
                if event.from_user.id > 0:  # Если сообщение не от бота

                    if event.from_.unwrap().username.unwrap_or_none() is None:
                        username = event.from_.unwrap().id
                    else:
                        username = event.from_.unwrap().username.unwrap().lower()

                    user, created = User.get_or_create_user(event.from_.unwrap().id,
                                                            event.from_user.first_name,
                                                            event.from_user.username.unwrap_or_none(),
                                                            event.from_user.last_name.unwrap_or_none())

                    if created:
                        if username != event.from_.unwrap().id:
                            msg = f"[{username}|{event.from_.unwrap().id}]"
                        else:
                            msg = f"[{username}]"

                        app.logger.info(f"[REGISTRATION] User [{event.from_user.first_name}] "
                                    f"{msg} is registered with ID [{user.id}]", "middleware")
                return True

        except Exception:
            app.logger.error(f"Error in middleware <RegistrationMiddleware>\n{traceback.format_exc()}", "middleware")


class MessageDeleteMiddleware(ABCMiddleware):
    """Middleware для регистрации сообщений которые нужно удалять в лс"""
    async def post(self, event: Message) -> bool | None:
        app = get_app()
        if event.chat.type == ChatType.PRIVATE:
            user = User.get(User.telegram_id == event.from_user.id)
            await app.menu_manager.append_message(event, user)  # Сохраняем сообщение от пользователя во временный список и удаляем

