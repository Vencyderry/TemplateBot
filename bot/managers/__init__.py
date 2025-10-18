"""Менеджеры для управления функциональностью бота."""

from bot.managers.menu_manager import MenuManager
from bot.managers.stats_manager import StatsManager, AdminStatsUtils

__all__ = [
    'MenuManager',
    'StatsManager',
    'AdminStatsUtils',
]
