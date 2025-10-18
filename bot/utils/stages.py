from typing import List, Union, Type, Dict, Any

from telegrinder import Message, CallbackQuery, ABCRule
from telegrinder.bot.rules import CallbackDataEq

from bot.rules.rules import StateRule


class Stage(ABCRule):
    def __init__(self, name: str):
        self.name = name
        super().__init__()

    def __str__(self) -> str:
        """Return stage name as string for assignments like user.current_state = stage"""
        return self.name

    def check(self, event: Union[Message, CallbackQuery]) -> bool:
        if isinstance(event, CallbackQuery):
            rule = CallbackDataEq(self.name)
            payload = event.data.unwrap_or_none()
            if payload is None:
                raise Exception("Event data payload is None")
            return rule.check(payload)
        elif isinstance(event, Message):
            rule = StateRule(self.name)
            result = rule.check(event)
            return result
        return False


class Stages:
    def __init__(self, state: str):
        self.state: str = state
        self.stages: List[Stage] = []

    def get_state_with_stage(self, stage):
        stage = Stage(self.state + ":" + stage)
        self.stages.append(stage)
        return stage

    def get_main_stage(self):
        return Stage(self.state)

    def get_back_stage(self):
        return self.get_state_with_stage("back")

    def get_all_stages(self):
        return self.stages


class StagesMeta(type):
    """
    Метакласс для автоматической генерации stages из атрибутов класса.
    Преобразует строковые атрибуты в объекты Stage.
    """
    def __new__(mcs, name: str, bases: tuple, namespace: Dict[str, Any]):
        # Получаем handler_name из атрибута класса
        handler_name = namespace.get('__handler__')

        if handler_name is None:
            # Если класс не определяет __handler__, просто создаем обычный класс
            return super().__new__(mcs, name, bases, namespace)

        # Создаем экземпляр Stages для управления stage'ами
        stages_manager = Stages(handler_name)

        # Автоматически создаем стандартные stages
        namespace['MAIN'] = stages_manager.get_main_stage()
        namespace['BACK'] = stages_manager.get_back_stage()

        # Собираем все stage-атрибуты (строки в верхнем регистре)
        stage_names = []
        for attr_name, attr_value in list(namespace.items()):
            # Пропускаем служебные атрибуты и уже созданные
            if attr_name.startswith('_') or attr_name in ('MAIN', 'BACK'):
                continue

            # Если атрибут - это строка или None, создаем для него Stage
            if isinstance(attr_value, str) or attr_value is None:
                # Используем имя атрибута в lowercase как имя stage
                stage_name = attr_name.lower()
                namespace[attr_name] = stages_manager.get_state_with_stage(stage_name)
                stage_names.append(attr_name)

        # Добавляем список всех stages
        namespace['ALL'] = stages_manager.get_all_stages()
        namespace['_stages'] = stages_manager
        namespace['_stage_names'] = stage_names

        return super().__new__(mcs, name, bases, namespace)


class BaseStages(metaclass=StagesMeta):
    """
    Базовый класс для декларативного определения stages.

    Использование:

    class MyHandlerStages(BaseStages):
        __handler__ = 'my_handler'

        # Автоматически создаются MAIN и BACK

        # Определяем кастомные stages (имя атрибута станет именем stage)
        NAME = None      # Создаст stage 'my_handler:name'
        EMAIL = None     # Создаст stage 'my_handler:email'
        PHONE = None     # Создаст stage 'my_handler:phone'

    Доступ:
        MyHandlerStages.MAIN   -> 'my_handler'
        MyHandlerStages.NAME   -> 'my_handler:name'
        MyHandlerStages.ALL    -> [все stages]
    """
    __handler__ = None  # Должен быть переопределен в подклассах

