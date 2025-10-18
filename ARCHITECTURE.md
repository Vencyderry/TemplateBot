# Архитектура проекта

## Структура директорий

```
TelegramBusinessAssistant/
├── bot/
│   ├── core/                  # Ядро приложения
│   ├── handlers/              # Обработчики событий
│   ├── middlewares/           # Middleware
│   ├── models/                # Модели базы данных
│   ├── services/              # Бизнес-логика
│   ├── managers/              # Менеджеры функциональности
│   ├── rules/                 # Правила для хендлеров
│   ├── keyboards/             # Клавиатуры
│   └── utils/                 # Утилиты
├── logs/                      # Логи
└── README.md
```

## Описание модулей

### 📦 `bot/core/` - Ядро приложения

Центральные компоненты для инициализации и конфигурации бота.

```python
from bot.core import BotApplication, Dispatch, get_app, settings
```

**Файлы:**
- `application.py` - Главный класс `BotApplication`
- `components.py` - Контейнер компонентов `BotComponents`
- `config.py` - Настройки приложения
- `context.py` - Контекст приложения (`get_app`, `set_app`)
- `dispatch.py` - Кастомный диспетчер `Dispatch`

**Когда использовать:**
- Инициализация бота
- Получение глобального экземпляра `app`
- Настройка конфигурации

---

### 🎯 `bot/handlers/` - Обработчики событий

Логика обработки сообщений и callback-запросов.

```python
from bot.handlers.application.stages import ApplicationService
from bot.handlers.start_bot import dp
```

**Структура:**
```
handlers/
├── start_bot.py              # Стартовые команды (/start)
├── admin/
│   ├── stats.py              # Статистика (было handler_stats.py)
│   └── info.py               # Информация (было handler_info.py)
└── application/
    ├── handlers.py           # Хендлеры заявок (было handler.py)
    └── stages.py             # Стадии заявок (было service.py)
```

**Когда использовать:**
- Добавление новых команд
- Обработка callback-запросов
- Логика взаимодействия с пользователем

---

### 🔧 `bot/managers/` - Менеджеры

Классы для управления специфической функциональностью (было `bot/modules/`).

```python
from bot.managers import MenuManager, StatsManager
```

**Файлы:**
- `menu_manager.py` - Управление меню и удаление сообщений
- `stats_manager.py` - Сбор статистики

**Когда использовать:**
- Сложная логика управления состоянием
- Работа с Telegram API (удаление сообщений, редактирование)
- Агрегация данных и статистики

---

### 🛠 `bot/utils/` - Утилиты

Вспомогательные функции и классы без состояния.

```python
from bot.utils import Handlers, Stage, Stages, setup_logging, AlignedLogger
```

**Файлы:**
- `logger.py` - Кастомный логгер
- `stages.py` - Классы для работы со стадиями (`Stage`, `Stages`)
- `constants.py` - Константы (было `handlers.py`)
- `ctx_storage.py` - Хранилище контекста
- `tools.py` - Вспомогательные инструменты

**Когда использовать:**
- Логирование
- Определение стадий бота
- Общие константы

---

### 💾 `bot/models/` - Модели базы данных

ORM модели и работа с БД.

```python
from bot.models.models import User
from bot.models.database import start_database
```

**Файлы:**
- `models.py` - ORM модели (User, и т.д.)
- `database.py` - Инициализация БД (было `start.py`)
- `migrations.py` - Миграции

**Когда использовать:**
- Работа с пользователями
- Сохранение данных
- Миграции схемы БД

---

### 🏢 `bot/services/` - Бизнес-логика

Сервисы для работы с внешними API и бизнес-логикой.

```python
from bot.services import UserService, BitrixService
```

**Файлы:**
- `user_service.py` - Работа с пользователями
- `bitrix_service.py` - Интеграция с Bitrix24

**Когда использовать:**
- Интеграция с внешними сервисами
- Сложная бизнес-логика
- Обработка данных

---

### ⚙️ `bot/middlewares/` - Middleware

Промежуточная обработка запросов.

```python
from bot.middlewares.registry import Middlewares
```

**Файлы:**
- `message.py` - Middleware для сообщений
- `callback_query.py` - Middleware для callback
- `registry.py` - Регистрация middleware (было `middlewares.py`)

**Когда использовать:**
- Логирование запросов
- Проверка прав доступа
- Предобработка данных

---

### ⌨️ `bot/keyboards/` - Клавиатуры

Все клавиатуры бота в одном месте.

```python
from bot.keyboards.main import some_keyboard
```

**Файлы:**
- `main.py` - Основные клавиатуры (было `modules/keyboards.py`)

**Когда использовать:**
- Создание inline-клавиатур
- Reply-клавиатуры
- Переиспользуемые кнопки

---

### 📋 `bot/rules/` - Правила

Кастомные правила для фильтрации событий.

```python
from bot.rules.rules import StateRule
from bot.rules.command_rule import CommandRule
```

**Файлы:**
- `rules.py` - Правило проверки состояния (было `rules.py`)
- `command_rule.py` - Правило команд

**Когда использовать:**
- Фильтрация событий по состоянию
- Кастомная логика проверки
- Сложные условия обработки

---

## Примеры использования

### Создание нового хендлера

```python
# bot/handlers/my_feature/handlers.py
from telegrinder import Message
from bot.core import BotApplication, Dispatch
from bot.models.models import User
from bot.utils import Handlers

dp = Dispatch(title=Handlers.MY_FEATURE,
              description="Описание функции")

@dp.message()
async def my_handler(event: Message, app: BotApplication, user: User):
    await event.answer("Hello!")
```

### Добавление менеджера

```python
# bot/managers/my_manager.py
from telegrinder import API

class MyManager:
    def __init__(self, api: API):
        self.api = api
    
    async def do_something(self, user_id: int):
        await self.api.send_message(chat_id=user_id, text="Done!")
```

### Использование утилит

```python
from bot.utils import setup_logging, Handlers
from bot.core import get_app

# Логирование
setup_logging("logs")

# Получение app из любого места
app = get_app()
app.logger.info("Starting...")
```

## Миграция с предыдущей версии

### Изменения импортов

| Старый импорт | Новый импорт |
|--------------|--------------|
| `from bot.modules import MenuManager` | `from bot.managers import MenuManager` |
| `from bot.modules import Handlers` | `from bot.utils import Handlers` |
| `from bot.executor import Dispatch` | `from bot.core import Dispatch` |
| `from bot.config import settings` | `from bot.core.config import settings` |
| `from bot.context import get_app` | `from bot.core.context import get_app` |
| `from bot.application import BotApplication` | `from bot.core.application import BotApplication` |
| `from bot.models.start import start_database` | `from bot.models.database import start_database` |
| `from bot.middlewares.middlewares import Middlewares` | `from bot.middlewares.registry import Middlewares` |

### Переименованные файлы

| Старое имя | Новое имя |
|-----------|-----------|
| `bot/executor/executor.py` | `bot/core/dispatch.py` |
| `bot/modules/menu_manager.py` | `bot/managers/menu_manager.py` |
| `bot/modules/handlers.py` | `bot/utils/constants.py` |
| `bot/handlers/admin/handler_stats.py` | `bot/handlers/admin/stats.py` |
| `bot/handlers/application/handler.py` | `bot/handlers/application/handlers.py` |
| `bot/handlers/application/service.py` | `bot/handlers/application/stages.py` |
| `bot/models/start.py` | `bot/models/database.py` |
| `bot/middlewares/middlewares.py` | `bot/middlewares/registry.py` |

## Принципы организации

1. **Разделение ответственности** - каждый модуль имеет чёткое назначение
2. **Ядро отдельно** - всё необходимое для запуска в `bot/core/`
3. **Менеджеры vs Утилиты** - классы с состоянием в `managers/`, функции в `utils/`
4. **Явные имена** - `stats.py` вместо `handler_stats.py` (папка уже указывает на хендлер)
5. **Flat is better than nested** - избегаем глубокой вложенности

## Лучшие практики

✅ **DO:**
- Импортируйте из `bot.core` для работы с приложением
- Используйте `bot.utils` для констант и вспомогательных функций
- Создавайте менеджеры для сложной логики с состоянием
- Группируйте связанные хендлеры в подпапки

❌ **DON'T:**
- Не импортируйте напрямую из внутренних модулей
- Не смешивайте бизнес-логику с хендлерами
- Не дублируйте код - выносите в утилиты или менеджеры
- Не забывайте обновлять `__init__.py` при добавлении новых модулей
