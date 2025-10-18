from typing import Union, TYPE_CHECKING

from bot.models.models import User
from bot.instance import get_app
from telegrinder import Message, APIError, CallbackQuery

if TYPE_CHECKING:
    from telegrinder import API


class MenuManager:
    """Менеджер для управления меню и сообщениями бота."""

    def __init__(self, api: 'API'):
        """
        Инициализация MenuManager.

        Args:
            api: API клиент для взаимодействия с Telegram
        """
        self.api = api

    @staticmethod
    def _ensure_menu_structure(user: User) -> None:
        """Гарантирует, что у пользователя есть корректная структура меню."""
        if user.menu == {} or user.menu is None:
            user.menu = {"menu_message_id": 0, "messages_ids": []}

    def set_menu_message_id(self, event: Message | CallbackQuery, user: User) -> None:
        """
        Устанавливает ID основного сообщения меню.

        Args:
            event: Событие с сообщением
            user: Пользователь
        """
        self._ensure_menu_structure(user)
        message_id = event.message_id
        if isinstance(event, CallbackQuery):
            message_id = message_id.unwrap()

        user.menu["menu_message_id"] = message_id
        user.save()

    def get_menu_message_id(self, user: User) -> int:
        """
        Получает ID основного сообщения меню.

        Args:
            user: Пользователь

        Returns:
            ID сообщения меню
        """
        self._ensure_menu_structure(user)
        return user.menu["menu_message_id"]

    async def append_message(
        self,
        event: Message,
        user: User,
        auto_clean: bool = True
    ) -> None:
        """
        Добавляет сообщение в список для последующего удаления.

        Args:
            event: Сообщение для добавления
            user: Пользователь
            auto_clean: Автоматически удалить ВСЕ накопленные сообщения после добавления (по умолчанию True)
                       True - после добавления нового сообщения удаляет все накопленные + сохраняет
                       False - только добавляет в список без удаления (нужно вызвать clean_chat вручную)

        Примеры:
            # Паттерн 1: Автоматическая очистка (по умолчанию)
            result = await app.api.edit_message_text(...)
            await app.menu_manager.append_message(result, user)  # Автоматически удалит старые

            # Паттерн 2: Накопление нескольких сообщений
            await app.menu_manager.append_message(msg1, user, auto_clean=False)
            await app.menu_manager.append_message(msg2, user, auto_clean=False)
            await app.menu_manager.clean_chat(event, user)  # Удалит все разом
        """
        app = get_app()
        try:
            if event is None:
                return

            if event.chat.type != "private":
                return

            self._ensure_menu_structure(user)

            # Добавляем новое сообщение
            user.menu["messages_ids"].append(event.message_id)

            # Если auto_clean=True, сначала удаляем старые сообщения
            if auto_clean and user.menu["messages_ids"]:
                chat_id = event.chat_id
                for message_id in user.menu["messages_ids"]:
                    try:
                        await self.api.delete_message(chat_id=chat_id, message_id=message_id)
                    except APIError as e:
                        if e.code == 429:
                            app.logger.error("❗️[ERROR] Rate limit exceeded. Consider implementing message deletion queue with delay.")
                        else:
                            app.logger.debug(f"Failed to delete message {message_id}: {e}")
                            continue

                # Очищаем список
                user.menu["messages_ids"] = []

            user.save()

        except AttributeError:
            pass

    async def clean_chat(self, event: Union[Message, CallbackQuery], user: User, delete_menu_message: bool = False):
        """
        Удаляет все накопленные сообщения из чата.

        Args:
            event: Событие для определения chat_id
            user: Пользователь
            delete_menu_message: Удалить ли также основное сообщение меню
        """
        app = get_app()
        self._ensure_menu_structure(user)

        chat_id = event.chat_id
        if isinstance(event, CallbackQuery):
            chat_id = event.chat_id.unwrap()

        if delete_menu_message:
            user.menu["messages_ids"].append(user.menu["menu_message_id"])

        if user.menu["messages_ids"]:
            for message_id in user.menu["messages_ids"]:
                try:
                    await self.api.delete_message(chat_id=chat_id, message_id=message_id)
                except APIError as e:
                    if e.code == 429:
                        app.logger.error("❗️[ERROR] Rate limit exceeded. Consider implementing message deletion queue with delay.")
                    else:
                        app.logger.debug(f"Failed to delete message {message_id}: {e}")
                        continue

            # Очищаем список и сохраняем один раз в конце
            user.menu["messages_ids"] = []
            user.save()
