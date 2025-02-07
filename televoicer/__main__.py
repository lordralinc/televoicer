import logging
import os

import tortoise
from aiogram.utils.i18n import I18n, SimpleI18nMiddleware
from dotenv import load_dotenv
from rich.logging import RichHandler

from .dispatcher import bot, dp
from .handlers import router

load_dotenv()


__all__ = ()

logging.basicConfig(
    level="NOTSET", format="%(message)s", datefmt="[%X]", handlers=[RichHandler()]
)


@dp.startup()
async def on_startup():
    await tortoise.Tortoise.init(
        db_url=os.environ.get('DATABASE_URL', "sqlite://db.sqlite3"), modules={"models": ["televoicer.models"]}
    )
    await tortoise.Tortoise.generate_schemas()


i18n = I18n(path="locales", default_locale="en", domain="messages")


if __name__ == "__main__":
    dp.message.outer_middleware(SimpleI18nMiddleware(i18n))
    dp.inline_query.outer_middleware(SimpleI18nMiddleware(i18n))
    dp.include_router(router)
    dp.run_polling(bot)
