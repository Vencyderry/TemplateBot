"""
Точка входа в приложение Telegram бота.
"""
from bot.core.config import settings
from bot.instance import init_app
from bot.handlers import handlers
from bot.middlewares import middlewares


def main():
    app = init_app(log_dir=settings.log_dir, skip_updates=settings.skip_updates)
    app.setup(handlers=handlers,
              middlewares=middlewares)
    app.run()


if __name__ == "__main__":
    main()
