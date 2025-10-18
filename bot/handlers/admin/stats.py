from telegrinder import Message
from telegrinder.bot.rules import IsGroup
from telegrinder.rules import Text

from bot.core import BotApplication, Dispatch, CommandExecutionMode
from bot.managers import AdminStatsUtils
from bot.models.models import User

dp = Dispatch(title="admin_stats",
              permission=User.ADMIN,
              description="Команда проверки админ статистики")


@dp.message(Text("/stats") & IsGroup())
@dp.wrap_handler(mode=CommandExecutionMode.FULL)
async def stats_handler(event: Message, app: BotApplication, user: User):
    """Показать статистику"""
    stats_message = AdminStatsUtils.get_global_stats_message()

    await event.answer(stats_message)


@dp.message(Text("/stats_detailed") & IsGroup())
@dp.wrap_handler(mode=CommandExecutionMode.FULL)
async def detailed_stats_handler(event: Message, app: BotApplication, user: User):
    """Подробная статистика"""
    detailed_message = AdminStatsUtils.get_detailed_stats_message()

    await event.answer(detailed_message)

