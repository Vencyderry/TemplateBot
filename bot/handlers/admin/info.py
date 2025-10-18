from telegrinder import Message
from telegrinder.bot.rules import IsGroup
from telegrinder.rules import Text

from bot.core import BotApplication, Dispatch
from bot.utils import Handlers
from bot.models.models import User

dp = Dispatch(title=Handlers.ADMIN_INFO,
              permission=User.ADMIN,
              description="Команда выдающая информацию о событии")


@dp.message(Text("/info") & IsGroup())
@dp.wrap_handler(is_full_command=True)
async def admin_info(event: Message, app: BotApplication, user: User):
    # Основная информация о чате и отправителе
    chat = event.chat
    sender = event.from_user

    # Формируем базовую информацию
    info_lines = [
        "<b>📊 Информация о событии:</b>",
        f"• <b>Тип чата:</b> {chat.type}",
        f"• <b>ID чата:</b> <code>{chat.id}</code>",
        f"• <b>ID отправителя команды:</b> <code>{sender.id}</code>",
        f"• <b>Имя отправителя:</b> {sender.first_name}" + (f" {sender.last_name}" if sender.last_name else "")
    ]

    # Добавляем юзернейм если есть
    if sender.username.unwrap_or_none():
        info_lines.append(f"• <b>Юзернейм отправителя:</b> @{sender.username.unwrap()}")

    # Проверяем, является ли сообщение ответом
    if event.reply_to_message.unwrap_or_none():
        reply = event.reply_to_message.unwrap()
        info_lines.extend([
            "\n<b>🔄 Информация о пересланном сообщении:</b>",
            f"• <b>ID исходного сообщения:</b> <code>{reply.message_id}</code>"
        ])

        # Информация об авторе пересланного сообщения
        if reply.from_user:
            info_lines.append(f"• <b>ID автора сообщения:</b> <code>{reply.from_user.id}</code>")
            if reply.from_user.username.unwrap_or_none():
                info_lines.append(f"• <b>Юзернейм автора:</b> @{reply.from_user.username.unwrap()}")
        else:
            info_lines.append("• <b>Автор:</b> Не пользователь (канал/бот)")

        # Проверяем наличие пересланного из другого чата
        if reply.forward_origin.unwrap_or_none():
            info_lines.append(
                f"• <b>ID исходного отправителя:</b> <code>{reply.forward_origin.unwrap().v.sender_user.id}</code>")
            if reply.forward_origin.unwrap().v.sender_user.username.unwrap_or_none():
                info_lines.append(
                    f"• <b>Юзернейм исходного отправителя:</b> @{reply.forward_origin.unwrap().v.sender_user.username.unwrap()}")

    # Добавляем информацию о дате
    info_lines.append(f"\n<b>📅 Дата сообщения:</b> {event.date.strftime('%Y-%m-%d %H:%M:%S')}")

    await event.answer("\n".join(info_lines),
                       parse_mode="HTML")
