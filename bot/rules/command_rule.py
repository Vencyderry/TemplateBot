from typing import Any, Callable, List, Union, Optional, Type
from telegrinder import Message
from telegrinder.node.base import is_generator
from telegrinder.rules import ABCRule
from telegrinder.types import ChatType

from bot.models.models import User


class Argument:
    """Класс для описания аргумента команды"""

    def __init__(
            self,
            name: str,
            types: List[Union[Type, Callable[[str], Any]]],
            optional: bool = False,
            from_reply: bool = False
    ):
        self.name = name
        self.types = types
        self.optional = optional
        self.from_reply = from_reply


_command_args_storage = {}


class CommandRule(ABCRule):
    """Универсальное правило для валидации команд"""

    def __init__(
            self,
            command: str,
            *args: Argument,
            prefix: str = "/",
            is_group: bool = False,
    ):
        self.command = command
        self.args = args
        self.prefix = prefix
        self.expected_args = [arg for arg in args if not arg.from_reply]
        self.reply_args = [arg for arg in args if arg.from_reply]
        self.is_group = is_group

    async def check(self, message: Message) -> bool:
        if self.is_group:
            if message.chat.type != ChatType.GROUP:
                return False

        if not message.text.unwrap_or_none() or not message.text.unwrap().startswith(self.prefix):
            return False

        parts = message.text.unwrap().split()
        if not parts or parts[0] != f"{self.prefix}{self.command}":
            return False

        # Извлекаем аргументы из текста (исключая команду)
        text_args = parts[1:]
        parsed_args = {}
        error_message = None

        # Обрабатываем аргументы из reply
        for arg in self.reply_args:
            if arg.from_reply:
                if message.reply_to_message.unwrap_or_none() and message.reply_to_message.unwrap_or_none().from_user:
                    user = User.get_or_none(User.telegram_id == message.reply_to_message.unwrap_or_none().from_user.id)
                    # Проверяем типы для user
                    validation_result = self.validate_argument(user, arg.types, arg.name)
                    if validation_result.is_valid:
                        parsed_args[arg.name] = validation_result.value
                    else:
                        error_message = validation_result.error
                        break
                elif not arg.optional:
                    error_message = f"Аргумент {arg.name} должен быть указан через reply сообщение"
                    break
                else:
                    parsed_args[arg.name] = None

        if error_message:
            await message.answer(error_message)
            return False

        # Обрабатываем обычные аргументы из текста
        arg_index = 0
        for i, arg in enumerate(self.expected_args):
            if arg_index >= len(text_args):
                if not arg.optional:
                    error_message = f"Аргумент {arg.name} не указан"
                    break
                parsed_args[arg.name] = None
                continue

            value = text_args[arg_index]
            validation_result = self.validate_argument(value, arg.types, arg.name)

            if not validation_result.is_valid:
                error_message = validation_result.error
                break

            parsed_args[arg.name] = validation_result.value
            arg_index += 1

        # Проверяем лишние аргументы
        if not error_message and arg_index < len(text_args):
            error_message = "Указано слишком много аргументов"

        if error_message:
            await self.send_usage_instruction(message, error_message)
            return False

        storage_key = self.get_command_args_storage_key(message)
        _command_args_storage[storage_key] = parsed_args
        return True

    @staticmethod
    def get_command_args_storage_key(message: Message) -> str:
        """Генерирует уникальный ключ для хранения аргументов команды"""
        return f"{message.chat_id}:{message.message_id}"

    @classmethod
    def extract_arguments_from_ctx(cls, message: Message, **kwargs) -> dict[str, Any] | None:
        """Метод для извлечения аргументов команды из временного хранилища"""
        if isinstance(message, Message):
            storage_key = cls.get_command_args_storage_key(message)
            if storage_key in _command_args_storage:
                command_args = _command_args_storage[storage_key]

                # Обновляем kwargs аргументами команды
                kwargs.update(command_args)

                # Удаляем из хранилища после использования
                del _command_args_storage[storage_key]
                return kwargs
        return kwargs

    def validate_argument(self, value: Any, types: List, arg_name: str) -> 'ValidationResult':
        """Валидирует значение аргумента против списка типов"""
        for type_validator in types:
            try:
                if type_validator is None:
                    # None тип - всегда валиден (для опциональных)
                    return ValidationResult(True, value)
                elif type_validator is int:
                    # Валидация int
                    if isinstance(value, int) or (isinstance(value, str) and value.isdigit()):
                        return ValidationResult(True, int(value))
                elif type_validator is float:
                    # Валидация float
                    if isinstance(value, float):
                        return ValidationResult(True, value)
                    elif isinstance(value, int):
                        return ValidationResult(True, float(value))
                    elif isinstance(value, str):
                        try:
                            # Заменяем запятые на точки для поддержки разных форматов
                            normalized = value.replace(',', '.')
                            # Пробуем преобразовать в float
                            float_value = float(normalized)
                            return ValidationResult(True, float_value)
                        except (ValueError, TypeError):
                            pass
                elif type_validator is str:
                    # Валидация str
                    return ValidationResult(True, str(value))
                elif callable(type_validator):
                    # Кастомная валидация
                    result = type_validator(value)
                    if result is not None:
                        return ValidationResult(True, result)
                elif isinstance(value, type_validator):
                    # Проверка типа
                    return ValidationResult(True, value)
            except (ValueError, TypeError):
                continue

        expected_types = [self.get_type_name(t) for t in types]
        error_msg = f"Аргумент {arg_name} должен быть одного из типов: {', '.join(expected_types)}"
        return ValidationResult(False, None, error_msg)

    def get_type_name(self, type_validator) -> str:
        """Возвращает читаемое имя типа"""
        if type_validator is int:
            return "число"
        elif type_validator is float:
            return "дробь"
        elif type_validator is str:
            return "строка"
        elif type_validator is None:
            return "опциональный"
        elif callable(type_validator):
            return "кастомный тип"
        else:
            return str(type_validator)

    async def send_usage_instruction(self, message: Message, error: str):
        """Отправляет инструкцию по использованию команды"""
        args_description = []
        for arg in self.args:
            optional_str = " (опционально)" if arg.optional else ""
            type_str = f"<{self.get_type_name(arg.types[0])}>" if arg.types else "<любой>"
            args_description.append(f"{arg.name}{type_str}{optional_str}")

        usage = f"{self.prefix}{self.command} {' '.join(args_description)}"
        instruction = f"❌ {error}\n\n💡 Использование:\n{usage}"

        await message.answer(instruction)


class ValidationResult:
    """Результат валидации аргумента"""

    def __init__(self, is_valid: bool, value: Any = None, error: str = ""):
        self.is_valid = is_valid
        self.value = value
        self.error = error


# Вспомогательные функции для валидации
def user_validator(value: Any) -> Optional[User]:
    """Валидатор для пользователя (из mention или объекта User)"""
    if isinstance(value, User):
        return value
    elif isinstance(value, str) and value.startswith('@'):
        # надо добавить логику поиска пользователя по username
        return User(id=0, first_name=value)  # Заглушка
    return None


def int_validator(s: str) -> Optional[int]:
    """Валидатор для целых чисел"""
    if s.isdigit():
        return int(s)
    return None


def float_validator(s: str) -> Optional[float]:
    """Валидатор для чисел с плавающей точкой"""
    try:
        return float(s)
    except ValueError:
        return None

