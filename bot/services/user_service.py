import datetime
from typing import Optional

from peewee import BigIntegerField
from telegrinder import logger


class UserService:

    _user_model = None

    @classmethod
    def _get_user_model(cls):
        if cls._user_model is None:
            from bot.models.models import User
            cls._user_model = User
        return cls._user_model

    @classmethod
    def get_or_create_user(cls, telegram_id, first_name, username=None, last_name=None):
        User = cls._get_user_model()  # ✅ Получаем модель

        user, created = User.get_or_create(
            telegram_id=telegram_id,
            defaults={
                'first_name': first_name,
                'username': username,
                'last_name': last_name,
            }
        )
        if not created:
            from bot.instance import get_app
            user.last_activity = datetime.datetime.now(tz=get_app().tz)
            user.save()
        return user, created

    @classmethod
    def set_state(
            cls,
            telegram_id: BigIntegerField,
            state: Optional[str]
    ) -> bool:
        try:
            User = cls._get_user_model()  # ✅ Получаем модель
            user = User.get(User.telegram_id == telegram_id)

            user.state = state
            user.save()
            return True

        except Exception as e:
            logger.error(f"Error in set_state for user {telegram_id}: {e}")
            return False
