from typing import List, Union

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

