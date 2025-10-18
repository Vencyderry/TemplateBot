from telegrinder import CallbackQuery, Message

from bot.core import BotApplication, Dispatch, CommandExecutionMode
from bot.models.models import User
from bot.utils import Handlers
from bot.handlers.application.stages import ApplicationService

dp = Dispatch(title=Handlers.APPLICATION,
              description="Команда заполнения заявки")


@dp.callback_query(ApplicationService.stages.MAIN)
@dp.wrap_handler(mode=CommandExecutionMode.MAIN)
async def application_start(event: CallbackQuery, app: BotApplication, user: User):
    await event.edit_text(text="Main State")
    user.current_state = ApplicationService.stages.NAME


@dp.message(ApplicationService.stages.NAME)
@dp.wrap_handler(mode=CommandExecutionMode.FINAL)
async def application_start(event: Message, app: BotApplication, user: User):
    menu_message = app.menu_manager.get_menu_message_id(user)
    await app.api.edit_message_text(text=f"Name State {event.text.unwrap_or("None")}",
                                    chat_id=event.chat_id,
                                    message_id=menu_message)

