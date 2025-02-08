from aiogram import Router, html, types
from aiogram.filters import Command
from aiogram.utils.i18n import gettext as _

__all__ = ("router",)
router = Router()


@router.message(Command("start"))
async def on_start_handler(message: types.Message):
    await message.reply(
        _(
            "🌟 Hi! I'm Televoicer, your voice archive!\nSource code: github.com/lordralinc/televoicer\n\n{url}"
        ).format(
            url=html.link(
                _("Learn more about me in the guide"),
                _("https://teletype.in/@lordralinc/televoicer_en"),
            )
        ),
    )
