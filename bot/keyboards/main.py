from telegrinder import InlineKeyboard, InlineButton


class KeyboardManager:

    @staticmethod
    def get_keyboard_to_main_menu():
        keyboard = (
            InlineKeyboard()
            .add(InlineButton("Главное меню", callback_data="start")).row()
        ).get_markup()
        return keyboard

    @staticmethod
    def get_keyboard_to_back(callback_data: str):
        keyboard = (
            InlineKeyboard()
            .add(InlineButton("Вернуться назад", callback_data=callback_data.lower())).row()
        ).get_markup()
        return keyboard

    @staticmethod
    def get_keyboard_full(callback_data: str):
        keyboard = (
            InlineKeyboard()
            .add(InlineButton("Вернуться назад", callback_data=callback_data.lower())).row()
            .add(InlineButton("Главное меню", callback_data="start"))
        ).get_markup()
        return keyboard
