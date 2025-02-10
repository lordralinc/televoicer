import re
import typing

import pydantic
from aiogram import F, Router, html
from aiogram.types import Message
from aiogram.utils.deep_linking import create_start_link
from aiogram.utils.i18n import gettext as _

from televoicer import models, utils
from televoicer.dispatcher import bot

__all__ = ("router",)
router = Router()


class PackCreateRequest(pydantic.BaseModel):
    name: str
    privacy: typing.Annotated[
        models.VoiceTemplatePack.Privacy,
        pydantic.Field(default=models.VoiceTemplatePack.Privacy.PRIVATE),
    ]

    @pydantic.field_validator("privacy", mode="before")
    @classmethod
    def validate_privacy(cls, value: str | int) -> models.VoiceTemplatePack.Privacy:
        if isinstance(value, str):
            lower_value = value.lower()
            if lower_value in {"приватный", "private"}:
                return models.VoiceTemplatePack.Privacy.PRIVATE
            if lower_value in {"публичный", "public"}:
                return models.VoiceTemplatePack.Privacy.PUBLIC
            raise ValueError("Invalid privacy value")
        return models.VoiceTemplatePack.Privacy(value)


@router.message(
    utils.multiregexp(
        F.text,
        r"^пак создать (?P<name>[\S ]+) (?P<privacy>публичный|приватный)$",
        r"^пак создать (?P<name>[\S ]+)$",
        r"^pack create (?P<name>[\S ]+) (?P<privacy>public|private)$",
        r"^pack create (?P<name>[\S ]+)$",
        flags=re.IGNORECASE,
    )
    .groupdict()
    .cast(PackCreateRequest.model_validate)
    .as_("request")
)
async def create_voice_pack(message: Message, request: PackCreateRequest, user: models.User):
    if await models.VoiceTemplatePack.exists(author=user, name=request.name):
        return await message.reply(
            _("💔 The voice template pack {name} already exists.").format(
                name=html.bold(request.name)
            )
        )
    pack = await models.VoiceTemplatePack.create(
        name=request.name,
        privacy=request.privacy,
        shortcode=models.VoiceTemplatePack.generate_shortcode(),
        author=user,
    )
    await message.reply(
        _(
            "❤️ Voice template pack {name} has been created!\n"
            "🔖 Shortcode: {shortcode}\n"
            "🔗 Link to add the pack: {add_url}\n\n"
            "✨ Use the {command} command to add templates to the pack!"
        ).format(
            name=html.bold(pack.name),
            shortcode=html.code(pack.shortcode),
            add_url=await create_start_link(bot, f"avp:{pack.shortcode}", encode=True),
            command=html.code(_("pack add {shortcode} name").format(shortcode=pack.shortcode)),
        )
    )
