import re

from aiogram import F, Router, html
from aiogram.types import Message
from aiogram.utils.i18n import gettext as _

from televoicer import models, utils

__all__ = ("router",)
router = Router()


@router.message(
    utils.multiregexp(
        F.text,
        r"^пак удалить (?P<shortcode>[a-zA-Z0-9]+)$",
        r"^pack delete (?P<shortcode>[a-zA-Z0-9]+)$",
        flags=re.IGNORECASE,
    )
    .group("shortcode")
    .as_("shortcode")
)
async def remove_voice_pack(message: Message, shortcode: str, user: models.User):
    pack = await models.VoiceTemplatePack.get_or_none(shortcode=shortcode, author=user)
    if pack is None:
        return await message.reply(
            _("💔 Voice pack with shortcode {shortcode} not found!").format(
                shortcode=html.bold(shortcode)
            )
        )
    await pack.delete()
    await message.reply(
        _("❤️ Template pack {pack_name} has been successfully deleted!").format(
            pack_name=html.bold(pack.name),
        )
    )
