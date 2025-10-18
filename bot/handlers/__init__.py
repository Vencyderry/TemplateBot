from bot.handlers import (
    start_bot
)

from bot.handlers import (
    admin,
    application
)

single_handlers = [
    start_bot.dp
]

groups_handlers = [
    single_handlers,
    admin.group_handlers,
    application.group_handlers
]

handlers = []

for group_handlers in groups_handlers:
    handlers.extend(group_handlers)

__all__ = ["handlers"]
