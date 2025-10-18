import datetime
import json

from typing import Dict

from bot.services import UserService
from bot.instance import get_app

from peewee import (
    SqliteDatabase,
    Model,
    CharField,
    TextField,
    IntegerField,
    BooleanField,
    ForeignKeyField,
    DateTimeField,
    BigIntegerField,
    DecimalField,
    DateField,
    DoesNotExist,
)


def get_app_tz():
    """Ленивый импорт app.tz для избежания циклических импортов."""
    return get_app().tz


def get_project_name():
    """Ленивый импорт project_name из настроек."""
    from bot.core.config import settings
    return settings.project_name


class JSONField(TextField):
    """
    Поле для хранения JSON-данных.
    """
    def db_value(self, value):
        return json.dumps(value) if value is not None else None

    def python_value(self, value):
        return json.loads(value) if value is not None else None


def get_database_path():
    """Автоматически определяет путь к БД через настройки."""
    from bot.core.config import settings
    return settings.get_database_path()


# Создаем подключение к БД
db_path = get_database_path()

db = SqliteDatabase(db_path)


class BaseModel(Model):
    class Meta:
        database = db


class User(BaseModel):
    ADMIN = 'admin'
    DEFAULT = 'default'
    ROLES = [ADMIN, DEFAULT]

    telegram_id = BigIntegerField(unique=True)
    username = CharField(null=True)
    first_name = CharField()
    last_name = CharField(null=True)
    role = CharField(choices=ROLES, default=DEFAULT)
    state = CharField(null=True)
    menu = JSONField(default={})  # данные о меню пользователя
    phone = CharField(null=True)
    email = CharField(null=True)
    language = CharField(default='ru')
    is_subscribed = BooleanField(default=False)
    created_at = DateTimeField(default=lambda: datetime.datetime.now(tz=get_app_tz()))
    last_activity = DateTimeField(default=lambda: datetime.datetime.now(tz=get_app_tz()))

    class Meta:
        table_name = 'users'

    # Короткие алиасы
    get_or_create_user = UserService.get_or_create_user

    @property
    def current_state(self):
        return self.state

    @current_state.setter
    def current_state(self, value):
        self.state = value
        self.save()

    def reset_state(self):
        self.state = None
        self.save()


class Application(BaseModel):
    NEW = 'new'
    PROCESSING = 'processing'
    APPROVED = 'approved'
    DELIVERY = 'delivery'
    COMPLETED = 'completed'
    REJECTED = 'rejected'

    _STATUS_METADATA: Dict[str, Dict[str, str]] = {
        NEW: {'text': 'Новая', 'icon': '⏳'},
        PROCESSING: {'text': 'В работе', 'icon': '⚙️'},
        APPROVED: {'text': 'Куплен', 'icon': '🟢'},
        DELIVERY: {'text': 'В пути', 'icon': '🚛'},
        COMPLETED: {'text': 'Доставлен', 'icon': '✅'},
        REJECTED: {'text': 'Отклонена', 'icon': '❌'}
    }

    # Для Peewee (обратная совместимость)
    CHOICES = [(status, metadata['text'])
               for status, metadata in _STATUS_METADATA.items()]

    user = ForeignKeyField(User, backref='applications')
    status = CharField(choices=CHOICES, default=NEW)
    car_model = CharField(null=True)
    price = DecimalField(null=True)
    currency = CharField(default='₽')
    country = TextField(null=True)
    phone = TextField(null=True)
    comments = TextField(null=True)
    bitrix_lead_id = IntegerField(null=True)  # ID лида в Bitrix24
    message_id_admin_chat = IntegerField(null=True)
    created_at = DateTimeField(default=lambda: datetime.datetime.now(tz=get_app_tz()))
    updated_at = DateTimeField(default=lambda: datetime.datetime.now(tz=get_app_tz()))

    class Meta:
        table_name = 'applications'

    def change_status(self, new_status):
        """Безопасное изменение статуса с автодополнением"""
        valid_statuses = [choice[0] for choice in self.CHOICES]
        if new_status not in valid_statuses:
            raise ValueError(f"Неверный статус: {new_status}")

        self.status = new_status
        self.updated_at = datetime.datetime.now(tz=get_app_tz())
        self.save()
        return self

    def get_status_display(self) -> str:
        """Получить отображение статуса"""
        return self._STATUS_METADATA.get(self.status, {}).get('text', 'Неизвестно')

    def get_status_icon(self) -> str:
        """Получить иконку статуса"""
        return self._STATUS_METADATA.get(self.status, {}).get('icon', '⚪')

    @classmethod
    def get_application_by_id(cls, lead_id):
        try:
            return cls.get_by_id(lead_id)
        except DoesNotExist:
            return None


class CommandStats(BaseModel):
    command_name = CharField(unique=True)  # Название команды
    execution_count = IntegerField(default=0)  # Количество выполнений
    last_execution = DateTimeField(null=True)  # Последнее выполнение
    total_users = IntegerField(default=0)  # Уникальных пользователей
    created_at = DateTimeField(default=lambda: datetime.datetime.now(tz=get_app_tz()))
    updated_at = DateTimeField(default=lambda: datetime.datetime.now(tz=get_app_tz()))

    class Meta:
        table_name = 'command_stats'


class CommandUserStats(BaseModel):
    command_name = CharField()
    user_id = BigIntegerField()
    executed_at = DateTimeField(default=lambda: datetime.datetime.now(tz=get_app_tz()))

    class Meta:
        table_name = 'command_user_stats'
        indexes = (
            (('command_name', 'user_id'), False),
        )


class UserMessage(BaseModel):
    user = ForeignKeyField(User, backref='messages')
    message_id = IntegerField()
    chat_id = BigIntegerField()
    created_at = DateTimeField(default=lambda: datetime.datetime.now(tz=get_app_tz()))

    class Meta:
        table_name = 'user_messages'
        indexes = (
            (('user', 'message_id'), True),  # Уникальная пара
            (('chat_id',), False),           # Для быстрого поиска по чату
        )




