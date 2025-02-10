from aiogram import Router

from . import (
    add_voice,
    create,
    global_pack_list,
    import_pack,
    packs_list,
    remove_pack,
    remove_voice,
    view_pack,
)

__all__ = ("router",)
router = Router()
router.include_routers(
    create.router,
    global_pack_list.router,
    add_voice.router,
    import_pack.router,
    packs_list.router,
    remove_pack.router,
    remove_voice.router,
    view_pack.router,
)
