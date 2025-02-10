import re

import pydantic
from aiogram import F, Router, html
from aiogram.types import Message
from aiogram.utils.i18n import gettext as _

from televoicer import models, utils

__all__ = ("router",)
router = Router()


class RemVoiceToPackRequest(pydantic.BaseModel):
    shortcode: str
    name: str


@router.message(
    utils.multiregexp(
        F.text,
        r"^пак убрать (?P<shortcode>\w+) (?P<name>[\S ]+)$",
        r"^pack rem (?P<shortcode>\w+) (?P<name>[\S ]+)$",
        flags=re.IGNORECASE,
    )
    .groupdict()
    .cast(RemVoiceToPackRequest.model_validate)
    .as_("request")
)
async def remove_voice_from_pack(
    message: Message, request: RemVoiceToPackRequest, user: models.User
):
    pack = await models.VoiceTemplatePack.get_or_none(shortcode=request.shortcode, author=user)
    if pack is None:
        return await message.reply(
            _("💔 Voice pack with shortcode {shortcode} not found!").format(
                shortcode=html.bold(request.shortcode)
            )
        )
    voice = await models.VoiceTemplate.get_or_none(name=request.name, user=user)
    if voice is None:
        return await message.reply(
            _("💔 Template {name} not found!").format(name=html.bold(request.name))
        )
    if not await pack.templates.filter(id=voice.id).exists():
        return await message.reply(
            _("💔 Template {name} not exists in the pack!").format(name=html.bold(request.name))
        )
    await pack.templates.remove(voice)
    await message.reply(
        _(
            "❤️ Template {template_name} has been successfully remove from the pack {pack_name}!"
        ).format(
            template_name=html.bold(request.name),
            pack_name=html.bold(pack.name),
        )
    )
