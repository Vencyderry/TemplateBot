import typing

from telegrinder.types import ChatType
from telegrinder.bot.dispatch.context import Context
from telegrinder import CallbackQuery, ABCRule, Message
from telegrinder.rules import CallbackQueryDataRule

from typing import List, Union

from bot.models.models import User
from bot.instance import get_app


class CallbackDataEqs(CallbackQueryDataRule):
    def __init__(self, values: List[str]):
        self.values = values

    async def check(self, event: CallbackQuery, ctx: Context) -> bool:
        for value in self.values:
            if event.data.unwrap() == value:
                return True
        return False


class CallbackDataStartsWith(CallbackQueryDataRule):
    def __init__(self, value: str):
        self.value = value

    async def check(self, event: CallbackQuery, ctx: Context) -> bool:
        return event.data.unwrap().startswith(self.value)


class StateRule(ABCRule):
    """
    Универсальное правило для проверки состояния пользователя.
    Просто передаете состояние - все остальное автоматически.
    """

    def __init__(self, state: Union[str, List[str]]):
        self.state = state

    def check(self, event: Union[Message, CallbackQuery]) -> bool:
        app = get_app()
        try:
            # Автоматически определяем тип и параметры
            if isinstance(event, Message):
                # Для сообщений проверяем, что это приватный чат и есть текст
                if event.chat.type != ChatType.PRIVATE:
                    return False
                chat_id = event.chat_id
            else:
                # Для callback проверяем, что это приватный чат
                message = event.message.unwrap().v
                if message.chat.type != ChatType.PRIVATE:
                    return False
                chat_id = message.chat_id

            # Проверяем состояние пользователя
            user = User.get_or_none(User.telegram_id == chat_id)
            if user:
                if isinstance(self.state, list):
                    for state in self.state:
                        if user.current_state == state:
                            return True
                else:
                    return user.current_state == self.state
            return False
        except Exception:
            app.logger.exception("StateRule check failed", "rules")
            return False


