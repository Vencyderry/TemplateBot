import datetime
import json

from typing import Union

from bot.models.models import User


def decode(value):
    """Функция декодер жсон.
    Преобрзует строку в dict/list."""
    value = value.replace("\'", "\"")

    result = json.loads(value)
    return result


def digit(number: Union[str, int]) -> str:
    """Функция разделяющая число на разряды"""

    if isinstance(number, str):
        number = int(number)

    return "{:,}".format(number)


def format_user_info(user: User) -> str:
    name = f"{user.first_name} {user.last_name or ''}".strip()
    if user.username:
        return f'<a href="https://t.me/{user.username}">{name}</a>'
    return name


def format_date(date_value):
    """Форматирует дату из строки ISO 8601 в dd.mm.yyyy"""
    if date_value is None:
        return "Не указана"

    # Если это уже datetime объект
    if hasattr(date_value, 'strftime'):
        try:
            return date_value.strftime('%d.%m.%Y')
        except:
            return str(date_value)

    # Если это строка в формате "2025-09-23 13:53:20.624153+03:00"
    if isinstance(date_value, str):
        try:
            # Парсим ISO строку с временной зоной
            dt = datetime.datetime.fromisoformat(date_value.replace('Z', '+00:00'))
            return dt.strftime('%d.%m.%Y')
        except (ValueError, AttributeError):
            # Если не получается распарсить, возвращаем как есть (обрезаем до даты)
            return date_value[:10] if len(date_value) >= 10 else date_value

    # Любой другой тип
    return str(date_value)
# class MessageManager:
#     @staticmethod
#     async def save_message(message: Message):
#
#         """Сохраняет сообщение в БД"""
#         if not hasattr(message, "chat") or message.chat.type != 'private':
#             return
#
#         try:
#             user, created = User.get_or_create_user(
#                 telegram_id=message.chat_id,
#                 first_name=message.from_user.first_name,
#                 username=message.from_user.username.unwrap_or_none(),
#                 last_name=message.from_user.last_name.unwrap_or_none()
#             )
#
#             # Сохраняем сообщение в БД
#             UserMessage.create(
#                 user=user,
#                 message_id=message.message_id,
#                 chat_id=message.chat.id
#             )
#
#             logger.debug(
#                 f"💾 Сообщение {message.message_id} сохранено для пользователя {user.telegram_id}",
#                 extra={'message_id': message.message_id, 'user_id': user.telegram_id}
#             )
#
#         except IntegrityError:
#             # Игнорируем если сообщение уже существует (дубликат)
#             logger.debug(f"Сообщение {message.message_id} уже существует в БД")
#         except Exception as e:
#             logger.error(f"❌ Ошибка сохранения сообщения: {e}")
#
#     @staticmethod
#     async def delete_messages(chat_id: int, user_id: int = None):
#         """Немедленно удаляет сообщения из БД и Telegram"""
#         try:
#             # Сначала находим сообщения для удаления
#             query = UserMessage.select().where(UserMessage.chat_id == chat_id)
#
#             if user_id:
#                 user = User.get(User.telegram_id == user_id)
#                 query = query.where(UserMessage.user == user)
#
#             messages_to_delete = list(query)
#
#             if not messages_to_delete:
#                 logger.debug(f"Нет сообщений для удаления в чате {chat_id}")
#                 return
#
#             # Удаляем сообщения из Telegram
#             deleted_from_tg = 0
#             for user_message in messages_to_delete:
#                 try:
#                     await api.delete_message(
#                         message_id=user_message.message_id,
#                         chat_id=user_message.chat_id
#                     )
#                     deleted_from_tg += 1
#                     logger.debug(
#                         f"🗑️ Сообщение {user_message.message_id} удалено из Telegram",
#                         extra={'message_id': user_message.message_id, 'chat_id': chat_id}
#                     )
#                 except Exception as e:
#                     logger.warning(
#                         f"⚠️ Не удалось удалить сообщение {user_message.message_id} из Telegram: {e}",
#                         extra={'message_id': user_message.message_id, 'error': str(e)}
#                     )
#
#             delete_query = UserMessage.delete().where(UserMessage.chat_id == chat_id)
#
#             if user_id:
#                 delete_query = delete_query.where(UserMessage.user == user)
#
#             deleted_from_db = delete_query.execute()
#
#             logger.debug(
#                 f"✅ Удалено {deleted_from_db} сообщений из БД ({deleted_from_tg} из Telegram) для chat_id {chat_id}",
#                 extra={
#                     'chat_id': chat_id,
#                     'deleted_from_db': deleted_from_db,
#                     'deleted_from_tg': deleted_from_tg
#                 }
#             )
#
#         except Exception as e:
#             logger.error(f"❌ Ошибка удаления сообщений: {e}")
#
#     @staticmethod
#     async def delete_single_message(chat_id: int, message_id: int):
#         """Удаляет одно конкретное сообщение"""
#         try:
#             # Пытаемся удалить из Telegram
#             try:
#                 await api.delete_message(
#                     message_id=message_id,
#                     chat_id=chat_id
#                 )
#                 logger.debug(f"🗑️ Сообщение {message_id} удалено из Telegram")
#             except Exception as e:
#                 logger.warning(f"⚠️ Не удалось удалить сообщение {message_id} из Telegram: {e}")
#
#             # Удаляем из БД
#             deleted_count = (UserMessage
#                              .delete()
#                              .where(
#                 (UserMessage.chat_id == chat_id) &
#                 (UserMessage.message_id == message_id)
#             )
#                              .execute())
#
#             if deleted_count > 0:
#                 logger.debug(f"✅ Сообщение {message_id} удалено из БД")
#             else:
#                 logger.debug(f"ℹ️ Сообщение {message_id} не найдено в БД")
#
#         except Exception as e:
#             logger.error(f"❌ Ошибка удаления сообщения {message_id}: {e}")
#
#     @staticmethod
#     def get_user_message_count(user_id: int):
#         """Возвращает количество сообщений пользователя"""
#         try:
#             user = User.get(User.telegram_id == user_id)
#             return UserMessage.select().where(UserMessage.user == user).count()
#         except DoesNotExist:
#             return 0
#
#     @staticmethod
#     def cleanup_old_messages(days: int = 1):
#         """Очищает сообщения старше N дней"""
#         try:
#             cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)
#
#             deleted_count = (UserMessage
#                              .delete()
#                              .where(UserMessage.created_at < cutoff_date)
#                              .execute())
#
#             logger.info(
#                 f"🧹 Очищено {deleted_count} старых сообщений (старше {days} дней)",
#                 extra={'deleted_count': deleted_count, 'days': days}
#             )
#
#             return deleted_count
#
#         except Exception as e:
#             logger.error(f"❌ Ошибка очистки старых сообщений: {e}")
#             return 0
