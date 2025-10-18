from bot.core.config import settings
from bot.models.models import *
from bot.models.migrations import MigrationHistory, Migrations


def start_database():
    """Запуск базы данных"""
    from bot.instance import get_app

    app = get_app()
    with db:
        db.create_tables(
            [User,
             Application,
             SpecialOffer,
             CurrencyRate,
             UsefulVideo,
             FAQ,
             CommandUserStats,
             CommandStats,
             UserMessage,
             MigrationHistory
             ], safe=True)

        app.logger.info(f"Database <{settings.project_name}> ready", "database")

    Migrations.apply_migrations()  # выполняем миграции если есть
