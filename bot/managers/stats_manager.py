from peewee import *
import datetime
from typing import Dict, List, Tuple

from bot.instance import get_app
from bot.models.models import CommandStats, CommandUserStats, User


class StatsManager:
    @staticmethod
    def track_user_action(command_name: str, user_id: int) -> bool:
        """
        Отслеживает действие пользователя в системе статистики.
        Сохраняет запись о выполнении команды в CommandUserStats.

        :param command_name: Название команды/диспетчера
        :param user_id: ID пользователя в Telegram
        :return: True если статистика успешно обновлена
        """
        try:
            app = get_app()

            # Отслеживаем выполнение команды
            StatsManager.track_command_execution(command_name, user_id)

            app.logger.debug(
                f"📊 Statistics tracked: {command_name} for user {user_id}", "statistics"
            )

            return True

        except Exception as e:
            get_app().logger.error(
                f"❌ Statistics tracking failed for {command_name}: {e}", "statistics"
            )
            return False

    @staticmethod
    def track_command_execution(command_name: str, user_id: int):
        """Отслеживает выполнение команды (общая статистика)"""
        try:
            # Обновляем CommandStats
            app_tz = get_app().tz
            command_stats, created = CommandStats.get_or_create(
                command_name=command_name,
                defaults={
                    'execution_count': 1,
                    'total_users': 1,
                    'last_execution': datetime.datetime.now(tz=app_tz)
                }
            )

            if not created:
                command_stats.execution_count += 1

                # Проверяем уникальность пользователя
                user_executed = CommandUserStats.select().where(
                    (CommandUserStats.command_name == command_name) &
                    (CommandUserStats.user_id == user_id)
                ).exists()

                if not user_executed:
                    command_stats.total_users += 1

                command_stats.last_execution = datetime.datetime.now(tz=app_tz)
                command_stats.updated_at = datetime.datetime.now(tz=app_tz)
                command_stats.save()

            # Записываем выполнение пользователем
            CommandUserStats.create(
                command_name=command_name,
                user_id=user_id,
                executed_at=datetime.datetime.now(tz=app_tz)
            )

            return True

        except Exception as e:
            get_app().logger.error(f"❌ Error spectate command {e}", "stats_manager")
            return False

    @staticmethod
    def get_command_stats(command_name: str = None) -> Dict:
        """Получает статистику по командам"""
        try:
            if command_name:
                # Статистика конкретной команды
                stats = CommandStats.get(CommandStats.command_name == command_name)
                return {
                    'command_name': stats.command_name,
                    'execution_count': stats.execution_count,
                    'total_users': stats.total_users,
                    'last_execution': stats.last_execution,
                    'avg_per_user': stats.execution_count / stats.total_users if stats.total_users > 0 else 0
                }
            else:
                # Общая статистика по всем командам
                total_stats = CommandStats.select(
                    fn.SUM(CommandStats.execution_count).alias('total_executions'),
                    fn.SUM(CommandStats.total_users).alias('total_unique_users'),
                    fn.COUNT(CommandStats.command_name).alias('total_commands')
                ).get()

                return {
                    'total_executions': total_stats.total_executions or 0,
                    'total_unique_users': total_stats.total_unique_users or 0,
                    'total_commands': total_stats.total_commands or 0
                }

        except DoesNotExist:
            return {}
        except Exception as e:
            get_app().logger.error(f"❌ Error getting statistics commands {e}", "stats_manager")
            return {}

    @staticmethod
    def get_top_commands(limit: int = 10) -> List[Tuple[str, int]]:
        """Возвращает самые популярные команды"""
        try:
            commands = (CommandStats
                        .select()
                        .order_by(CommandStats.execution_count.desc())
                        .limit(limit))

            return [(cmd.command_name, cmd.execution_count) for cmd in commands]

        except Exception as e:
            get_app().logger.error(f"❌ Error getting tops commands {e}", "stats_manager")
            return []

    @staticmethod
    def get_command_usage_trend(days: int = 7) -> Dict:
        """Статистика использования команд по дням"""
        trend_data = {}

        for i in range(days):
            date = datetime.date.today() - datetime.timedelta(days=i)

            try:
                daily_usage = (CommandUserStats
                               .select(fn.COUNT(CommandUserStats.user_id).alias('count'))
                               .where(fn.DATE(CommandUserStats.executed_at) == date)
                               .scalar())

                trend_data[date.strftime('%Y-%m-%d')] = daily_usage or 0

            except Exception as e:
                trend_data[date.strftime('%Y-%m-%d')] = 0

        return trend_data

    @staticmethod
    def get_user_stats(user_id: int) -> Dict[str, int]:
        """
        Получает статистику пользователя на основе CommandUserStats.
        Возвращает количество выполнений каждой команды.

        :param user_id: ID пользователя в Telegram
        :return: Словарь {название_команды: количество_выполнений}
        """
        try:
            # Группируем по командам и считаем количество выполнений
            stats = (CommandUserStats
                    .select(
                        CommandUserStats.command_name,
                        fn.COUNT(CommandUserStats.id).alias('count')
                    )
                    .where(CommandUserStats.user_id == user_id)
                    .group_by(CommandUserStats.command_name))

            return {stat.command_name: stat.count for stat in stats}

        except Exception as e:
            get_app().logger.error(f"❌ Error getting user stats: {e}", "stats_manager")
            return {}

    @staticmethod
    def get_user_command_count(user_id: int, command_name: str) -> int:
        """
        Получает количество выполнений конкретной команды пользователем.

        :param user_id: ID пользователя в Telegram
        :param command_name: Название команды
        :return: Количество выполнений
        """
        try:
            count = (CommandUserStats
                    .select()
                    .where(
                        (CommandUserStats.user_id == user_id) &
                        (CommandUserStats.command_name == command_name)
                    )
                    .count())

            return count

        except Exception as e:
            get_app().logger.error(f"❌ Error getting user command count: {e}", "stats_manager")
            return 0


class AdminStatsUtils:
    @staticmethod
    def get_global_stats_message() -> str:
        """Возвращает сообщение с глобальной статистикой"""
        try:
            command_stats = StatsManager.get_command_stats()
            top_commands = StatsManager.get_top_commands(5)

            message = (
                "🌐 Глобальная статистика бота:\n"
                f"• 📊 Всего выполнено команд: {command_stats.get('total_executions', 0)}\n"
                f"• 👥 Уникальных пользователей: {command_stats.get('total_unique_users', 0)}\n"
                f"• 🎯 Всего команд отслеживается: {command_stats.get('total_commands', 0)}\n\n"
                "🔥 Топ-5 самых популярных команд:\n"
            )

            for i, (cmd, count) in enumerate(top_commands, 1):
                message += f"{i}. {cmd}: {count} выполнений\n"

            return message

        except Exception as e:
            return f"❌ Ошибка получения статистики: {e}"

    @staticmethod
    def get_detailed_stats_message() -> str:
        """Подробная статистика для админов"""
        try:
            top_commands = StatsManager.get_top_commands(10)
            trend = StatsManager.get_command_usage_trend(7)

            message = "📈 Детальная статистика:\n\n"
            message += "🎯 Топ-10 команд:\n"

            for i, (cmd, count) in enumerate(top_commands, 1):
                cmd_stats = StatsManager.get_command_stats(cmd)
                avg = cmd_stats.get('avg_per_user', 0)
                message += f"{i}. {cmd}: {count} (👥{cmd_stats.get('total_users', 0)}, 📊{avg:.1f}/user)\n"

            message += "\n📅 Использование за последние 7 дней:\n"
            for date, count in sorted(trend.items()):
                message += f"• {date}: {count} команд\n"

            return message

        except Exception as e:
            return f"❌ Ошибка получения детальной статистики: {e}"

    @staticmethod
    async def get_command_stats_message(title) -> str:
        """Возвращает сообщение со статистикой команды"""
        try:
            stats = StatsManager.get_command_stats(title)
            if not stats:
                return f"📊 Статистика команды '{title}': нет данных"

            return (
                f"📊 Статистика команды '{title}':\n"
                f"• 🎯 Выполнений: {stats['execution_count']}\n"
                f"• 👥 Уникальных пользователей: {stats['total_users']}\n"
                f"• 📈 Среднее на пользователя: {stats['avg_per_user']:.1f}\n"
                f"• ⏰ Последнее выполнение: {stats['last_execution'].strftime('%d.%m.%Y %H:%M') if stats['last_execution'] else 'никогда'}"
            )

        except Exception as e:
            return f"❌ Ошибка получения статистики команды '{title}'"

