from aiogram import Router

from . import start, voice_template_packs, voice_templates

__all__ = ("router",)
router = Router()
router.include_routers(
    start.router,
    voice_template_packs.router,
    voice_templates.router,
)
