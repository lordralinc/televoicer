import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

__all__ = (
    "bot",
    "dp",
)

logger = logging.getLogger(__name__)


storage = MemoryStorage()

bot = Bot(
    token=os.environ["TELEGRAM_API_KEY"],
    default=DefaultBotProperties(
        parse_mode="html", disable_notification=True, link_preview_is_disabled=True
    ),
)
dp = Dispatcher(storage=storage)
