from playhouse.migrate import SqliteMigrator, migrate

# Ваша база данных (замените на свою)
from bot.models.models import *
from bot.instance import get_app


class MigrationHistory(Model):
    name = CharField(unique=True)
    applied_at = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = db


# Создаем таблицу для истории миграций при инициализации
MigrationHistory.create_table(safe=True)

# Словарь миграций
MIGRATIONS = {
    'drop_user_stats_table': lambda: Migrations.drop_table('user_stats'),
}


class Migrations:

    @staticmethod
    def column_exists(table_name, column_name):
        """Проверяет существование колонки в таблице"""
        columns = db.get_columns(table_name)
        return any(col.name == column_name for col in columns)

    @staticmethod
    def table_exists(table_name):
        """Проверяет существование таблицы"""
        return table_name in db.get_tables()

    @classmethod
    def add_column(cls, table_name, column_name, field_type):
        """Добавляет колонку если она не существует"""
        if not cls.column_exists(table_name, column_name):
            migrator = SqliteMigrator(db)
            migrate(
                migrator.add_column(table_name, column_name, field_type)
            )
            get_app().logger.info(f"Added column {column_name} to table {table_name}", "migrations")

    @classmethod
    def drop_column(cls, table_name, column_name):
        """Удаляет колонку если она существует"""
        if cls.column_exists(table_name, column_name):
            migrator = SqliteMigrator(db)
            migrate(
                migrator.drop_column(table_name, column_name)
            )
            get_app().logger.info(f"Column {column_name} deleted from table {table_name}", "migrations")

    @classmethod
    def rename_column(cls, table_name, old_name, new_name):
        """Переименовывает колонку если она существует"""
        if cls.column_exists(table_name, old_name):
            migrator = SqliteMigrator(db)
            migrate(
                migrator.rename_column(table_name, old_name, new_name)
            )
            get_app().logger.info(f"Column {old_name} renamed to {new_name}", "migrations")

    @staticmethod
    def add_index(table_name, columns, unique=False):
        """Добавляет индекс"""
        migrator = SqliteMigrator(db)
        migrate(
            migrator.add_index(table_name, columns, unique=unique)
        )
        get_app().logger.info(f"Index for {columns} added to table {table_name}", "migrations")

    @classmethod
    def drop_table(cls, table_name):
        """Удаляет таблицу если она существует"""
        if cls.table_exists(table_name):
            db.execute_sql(f'DROP TABLE IF EXISTS {table_name}')
            get_app().logger.info(f"Table {table_name} dropped successfully", "migrations")
        else:
            get_app().logger.info(f"Table {table_name} does not exist, skipping", "migrations")

    @classmethod
    def apply_migrations(cls):
        """Применяет все невыполненные миграции"""
        get_app().logger.info(f"Checking migrations...", "migrations")

        applied_migrations = set()
        try:
            applied_migrations = {m.name for m in MigrationHistory.select()}
        except Exception as e:
            get_app().logger.error(f"Error reading migration history: {e}", "migrations")
            return

        for migration_name, migration_func in MIGRATIONS.items():
            if migration_name not in applied_migrations:
                try:
                    migration_func()
                    MigrationHistory.create(name=migration_name)
                    get_app().logger.success(f"Migration {migration_name} applied successfully", "migrations")
                except Exception as e:
                    get_app().logger.error(f"Error in migration {migration_name}: {e}", "migrations")

