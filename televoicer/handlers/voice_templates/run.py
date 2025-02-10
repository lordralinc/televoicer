import re

from aiogram import F, Router, html, types
from aiogram.utils.i18n import gettext as _
from tortoise.expressions import Q

from televoicer import models, utils

__all__ = ("router",)
router = Router()


@router.message(
    utils.multiregexp(
        F.text,
        r"^гшаб (?P<name>[\S ]+)$",
        r"^vt (?P<name>[\S ]+)$",
        flags=re.IGNORECASE,
    )
    .group("name")
    .as_("name")
)
async def show_voice_template(message: types.Message, user: models.User, name: str):
    template = await models.VoiceTemplate.get_or_none(user=user, name=name)
    if template is None:
        return await message.reply(
            _("💔 Voice template {name} not found.").format(name=html.bold(html.quote(name)))
        )
    await message.reply_voice(template.file_id)


@router.inline_query(
    utils.multiregexp(
        F.query,
        r"гшаб (?P<name>[\S ]+)$",
        r"vt (?P<name>[\S ]+)$",
        flags=re.IGNORECASE,
    )
    .group("name")
    .as_("name")
    | utils.multiregexp(F.query, r"гшаб$", r"vt$", r"гшаб $", r"vt $", flags=re.IGNORECASE)
)
async def show_user_templates(
    inline_query: types.InlineQuery, user: models.User, name: str | None = None
):
    offset = int(inline_query.offset) if inline_query.offset else 0
    q = Q(user=user)
    if name:
        q &= Q(name__icontains=name)

    qs = models.VoiceTemplate.filter(q)
    templates_count = await qs.count()
    templates = await qs.limit(50).offset(offset)
    await inline_query.answer(
        [
            types.InlineQueryResultCachedVoice(
                id=f"tv:vt:{template.id.hex}",
                title=template.name,
                voice_file_id=template.file_id,
            )
            for template in templates
        ],
        next_offset=str(offset + 50) if templates_count > offset + 50 else None,
    )
