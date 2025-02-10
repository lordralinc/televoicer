from aiogram import Router

from . import create, delete, run, show

__all__ = ("router",)
router = Router()

router.include_routers(
    create.router,
    delete.router,
    run.router,
    show.router,
)
