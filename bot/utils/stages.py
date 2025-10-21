"""
Система управления stages для Telegram bot handlers.
"""

from typing import ClassVar, List, Union

from telegrinder import ABCRule, CallbackQuery, Message
from telegrinder.bot.rules import CallbackDataEq

from bot.rules.rules import StateRule


class Stage(ABCRule):
    """Stage (состояние) в flow handler'а."""

    def __init__(self, name: str):
        self.name = name
        super().__init__()

    def __str__(self) -> str:
        """Возвращает имя для user.state = stage."""
        return self.name

    def __repr__(self) -> str:
        return f"Stage({self.name!r})"

    def check(self, event: Union[Message, CallbackQuery]) -> bool:
        """Проверяет, соответствует ли событие этому stage."""
        if isinstance(event, CallbackQuery):
            rule = CallbackDataEq(self.name)
            payload = event.data.unwrap_or_none()
            if payload is None:
                raise ValueError("Event data payload is None")
            return rule.check(payload)
        elif isinstance(event, Message):
            rule = StateRule(self.name)
            return rule.check(event)
        return False


class BaseStages:
    """
    Базовый класс для stages с полной поддержкой IDE.

    Использование:

    ```python
    class OrderStages(BaseStages):
        __handler__ = "orders"

        # Определяем кастомные stages (IDE их видит!)
        PRODUCT_NAME: ClassVar[Stage]
        QUANTITY: ClassVar[Stage]
        CONFIRM: ClassVar[Stage]

    # Автоматически доступны:
    OrderStages.MAIN          # Stage("orders")
    OrderStages.BACK          # Stage("orders:back")
    OrderStages.PRODUCT_NAME  # Stage("orders:product_name")
    OrderStages.QUANTITY      # Stage("orders:quantity")
    OrderStages.CONFIRM       # Stage("orders:confirm")
    OrderStages.ALL           # список всех stages
    ```
    """

    # Эти атрибуты будут у ВСЕХ подклассов
    __handler__: ClassVar[str]
    MAIN: ClassVar[Stage]
    BACK: ClassVar[Stage]
    ALL: ClassVar[List[Stage]]

    def __init_subclass__(cls, **kwargs):
        """Автоматически создает stages при наследовании."""
        super().__init_subclass__(**kwargs)

        # Получаем имя handler'а
        handler_name = getattr(cls, '__handler__', None)
        if handler_name is None:
            return

        # Создаем MAIN и BACK
        cls.MAIN = Stage(handler_name)
        cls.BACK = Stage(f"{handler_name}:back")

        # Собираем кастомные stages
        custom_stages: List[Stage] = [cls.BACK]

        # Ищем все аннотированные атрибуты
        annotations = getattr(cls, '__annotations__', {})
        for attr_name in annotations:
            # Пропускаем служебные
            if attr_name.startswith('_') or attr_name in ('MAIN', 'BACK', 'ALL', '__handler__'):
                continue

            # Создаем stage
            stage_name = attr_name.lower()
            stage = Stage(f"{handler_name}:{stage_name}")
            setattr(cls, attr_name, stage)
            custom_stages.append(stage)

        # Сохраняем все stages
        cls.ALL = custom_stages
