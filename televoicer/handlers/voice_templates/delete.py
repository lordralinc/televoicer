import re

from aiogram import F, Router, html, types
from aiogram.utils.i18n import gettext as _

from televoicer import models, utils

__all__ = ("router",)
router = Router()


@router.message(
    utils.multiregexp(
        F.text,
        r"^\-гшаб (?P<name>[\S ]+)$",
        r"^\-vt (?P<name>[\S ]+)$",
        flags=re.IGNORECASE,
    )
    .group("name")
    .as_("name")
)
async def delete_voice_template(message: types.Message, user: models.User, name: str):
    template = await models.VoiceTemplate.get_or_none(user=user, name=name)
    if template is None:
        return await message.reply(
            _("💔 Voice template {name} not found.").format(name=html.bold(html.quote(name)))
        )
    await template.delete()
    await message.reply(
        _("💔 Voice template {name} deteled.").format(name=html.bold(html.quote(name)))
    )
