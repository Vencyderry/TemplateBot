from telegrinder import InlineKeyboard, InlineButton, Message, CallbackQuery
from telegrinder.rules import Text, IsPrivate, CallbackDataEq

from bot.core import BotApplication, Dispatch
from bot.models.models import User
from bot.utils import Handlers

dp = Dispatch(title="start",
              description="Команда запуска бота")

kb = (
    InlineKeyboard()
    .add(InlineButton("Оставить заявку", callback_data=Handlers.APPLICATION)).row()
).get_markup()


@dp.message(Text(["/start", "/menu"], ignore_case=True) & IsPrivate())
@dp.wrap_handler(is_full_command=True)
async def start_message(event: Message, app: BotApplication, user: User) -> None:
    user.current_state = "start"
    response = await event.answer(
        text=f"Вам доступен следующий функционал:",
        reply_markup=kb
    )
    await app.menu_manager.clean_chat(event, user, delete_menu_message=True)  # Чистим чат от предыдущих сообщений
    app.menu_manager.set_menu_message_id(response.unwrap(), user)  # Сохраняем сообщение для меню


@dp.callback_query(CallbackDataEq("start") & IsPrivate())
@dp.wrap_handler(is_full_command=True)
async def start_cq(event: CallbackQuery, app: BotApplication, user: User) -> None:
    user.current_state = "start"
    await app.menu_manager.clean_chat(event, user)  # Чистим чат от предыдущих сообщений

    await app.api.edit_message_text(
        text=f"Вам доступен следующий функционал:",
        chat_id=event.chat_id,
        message_id=event.message.unwrap().v.message_id,
        reply_markup=kb
    )
