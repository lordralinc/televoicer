from aiogram import F, Router, html, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

__all__ = ("router",)
router = Router()


@router.message(CommandStart(magic=~F.args))
@router.message(Command("help"))
async def on_start_handler(message: types.Message):
    await message.reply(
        _(
            "🌟 Hi! I'm Televoicer, your voice archive!\nSource code: github.com/lordralinc/televoicer\n\n\n{url}"
        ).format(
            url=html.link(
                _("Learn more about me in the guide"),
                _("https://teletype.in/@lordralinc/televoicer_en"),
            )
        ),
    )


@router.message(Command("cancel"))
@router.message(F.text.casefold() == "cancel")
async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.clear()
    await message.answer(_("💔 Current request cancelled."))
