from typing import ClassVar

from bot.utils import Handlers, BaseStages
from bot.utils.stages import Stage


class ApplicationStages(BaseStages):
    """
    Stages для хендлера Application.

    Автоматически создаются:
    - MAIN: 'application'
    - BACK: 'application:back'
    - ALL: список всех stages
    """
    __handler__ = Handlers.APPLICATION

    NAME: ClassVar[Stage]
    NUMBER: ClassVar[Stage]
    DESCRIPTION: ClassVar[Stage]


class ApplicationService:
    """Сервис для работы с ApplicationStages"""
    stages = ApplicationStages


