from typing import List

from bot.utils import Handlers, Stages, Stage


class ApplicationStages:
    _stages = Stages(Handlers.APPLICATION)

    MAIN: Stage = _stages.get_main_stage()
    BACK: Stage = _stages.get_back_stage()
    ALL: List[Stage] = _stages.get_all_stages()

    NAME: Stage = _stages.get_state_with_stage("name")
    NUMBER: Stage = _stages.get_state_with_stage("number")
    DESCRIPTION: Stage = _stages.get_state_with_stage("description")


class ApplicationService:
    stages: ApplicationStages = ApplicationStages()


