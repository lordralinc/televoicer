import re

import pydantic
from aiogram import F, Router, html
from aiogram.types import Message
from aiogram.utils.i18n import gettext as _

from televoicer import models, utils

__all__ = ("router",)
router = Router()


class AddVoiceToPackRequest(pydantic.BaseModel):
    shortcode: str
    name: str


@router.message(
    utils.multiregexp(
        F.text,
        r"^пак добавить (?P<shortcode>\w+) (?P<name>[\S ]+)$",
        r"^pack add (?P<shortcode>\w+) (?P<name>[\S ]+)$",
        flags=re.IGNORECASE,
    )
    .groupdict()
    .cast(AddVoiceToPackRequest.model_validate)
    .as_("request")
)
async def add_voice_to_pack(message: Message, request: AddVoiceToPackRequest, user: models.User):
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
            _("💔 Template {name} not found!").format(name=html.bold(html.quote(request.name)))
        )
    if await pack.templates.filter(id=voice.id).exists():
        return await message.reply(
            _("💔 Template {name} is already in the pack!").format(
                name=html.bold(html.quote(request.name))
            )
        )
    await pack.templates.add(voice)
    await message.reply(
        _(
            "❤️ Template {template_name} has been successfully added to the pack {pack_name}!"
        ).format(
            template_name=html.bold(html.quote(request.name)),
            pack_name=html.bold(html.quote(pack.name)),
        )
    )
