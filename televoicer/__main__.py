import logging
import os
import pathlib

import tortoise
from aiogram.utils.i18n import I18n, SimpleI18nMiddleware
from dotenv import load_dotenv
from rich.logging import RichHandler

from televoicer.commands import set_commands
from televoicer.middleware import CreateUserMiddleware

from .dispatcher import bot, dp
from .handlers import router

load_dotenv(pathlib.Path(".env"))


__all__ = ()

logging.basicConfig(
    level=logging.NOTSET if os.environ.get("DEBUG", "0") == "1" else logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler()],
)


@dp.startup()
async def on_startup():
    await tortoise.Tortoise.init(
        db_url=os.environ.get("DATABASE_URL", "sqlite://db.sqlite3"),
        modules={"models": ["televoicer.models"]},
    )
    await tortoise.Tortoise.generate_schemas()
    await set_commands(i18n)


@dp.shutdown()
async def on_shutdown():
    await tortoise.Tortoise.close_connections()


i18n = I18n(path="locales", default_locale="en", domain="messages")
i18n_middleware = SimpleI18nMiddleware(i18n)

if __name__ == "__main__":
    dp.message.outer_middleware(i18n_middleware)
    dp.inline_query.outer_middleware(i18n_middleware)
    dp.callback_query.outer_middleware(i18n_middleware)
    dp.message.middleware(CreateUserMiddleware())
    dp.callback_query.middleware(CreateUserMiddleware())
    dp.inline_query.middleware(CreateUserMiddleware())
    dp.include_router(router)
    dp.run_polling(bot)
