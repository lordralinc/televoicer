from aiogram import Router

from . import start, voice_template

__all__ = ("router",)
router = Router()
router.include_routers(
    start.router,
    voice_template.router,
)
