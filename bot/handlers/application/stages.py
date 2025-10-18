from bot.utils import Handlers, BaseStages


class ApplicationStages(BaseStages):
    """
    Stages для хендлера Application.

    Автоматически создаются:
    - MAIN: 'application'
    - BACK: 'application:back'
    - ALL: список всех stages
    """
    __handler__ = Handlers.APPLICATION

    # Кастомные stages для заполнения заявки
    NAME = None
    NUMBER = None
    DESCRIPTION = None


class ApplicationService:
    """Сервис для работы с ApplicationStages"""
    stages = ApplicationStages


