from peewee import DoesNotExist
from telegrinder import CallbackQuery
from telegrinder import ABCMiddleware

from bot.models.models import User
from bot.instance import get_app


class CallbackQueryAnswerMiddleware(ABCMiddleware):
    """Middleware для обработки calbackquery"""
    async def post(self, event: CallbackQuery) -> None:
        await event.answer("✔️")  # Отвечаем по дефолту на нажатие кнопок


class UserUpdateMiddleware(ABCMiddleware):
    """Middleware для обновления данных пользователя"""

    async def post(self, event: CallbackQuery):
        """Выполняется ДО обработчиков"""

        app = get_app()
        # Пропускаем апдейты без информации о пользователе
        if not hasattr(event, 'from_user') or not event.from_user:
            return True

        user_data = event.from_user

        try:
            # Ищем пользователя в базе
            user = User.get(User.telegram_id == user_data.id)

            # Проверяем, изменились ли данные
            needs_update = (
                    user.username != user_data.username.unwrap_or_none() or
                    user.first_name != user_data.first_name or
                    user.last_name != user_data.last_name.unwrap_or_none()
            )

            if needs_update:
                # Обновляем данные
                user.username = user_data.username.unwrap_or_none() or user.username
                user.first_name = user_data.first_name or user.first_name
                user.last_name = user_data.last_name.unwrap_or_none() or user.last_name
                user.save()

        except DoesNotExist:
            # Пользователь не найден - это нормально для новых пользователей
            pass
        except Exception as e:
            app.logger.error(f"Error updating user data: {e}", "middleware")


