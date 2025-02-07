from aiogram import F, Router, html, types
from aiogram.filters import Command
from aiogram.utils.i18n import gettext as _

from televoicer import models, utils

__all__ = ("router",)
router = Router()


@router.message(
    (
        F.audio
        | F.document
        | (F.reply_to_message & (F.reply_to_message.audio | F.reply_to_message.document))
    )
    & (
        (
            F.caption
            & utils.multiregexp(
                F.caption,
                r"^\+гшаб (?P<name>[a-zA-ZА-Яа-яёЁ0-9 \.\-\+\!]+)$",
                r"^\+vt (?P<name>[a-zA-ZА-Яа-яёЁ0-9 \.\-\+\!]+)$",
            )
        )
        | (
            F.text
            & utils.multiregexp(
                F.text,
                r"^\+гшаб (?P<name>[a-zA-ZА-Яа-яёЁ0-9 \.\-\+\!]+)$",
                r"^\+vt (?P<name>[a-zA-ZА-Яа-яёЁ0-9 \.\-\+\!]+)$",
            )
        )
    )
    .group("name")
    .as_("name")
)
async def save_voice_template(message: types.Message, name: str):
    if await models.VoiceTemplate.exists(
        user_id=utils.cast(message.from_user).id,
        name=name,
    ):
        return await message.reply(
            _("💔 The voice template {name} already exists.").format(name=html.bold(name))
        )

    file = message.audio or message.document
    if message.reply_to_message and not file:
        file = message.reply_to_message.audio or message.reply_to_message.document
    msg = await message.reply(
        _("❤️ Voice template {name} is being created...").format(name=html.bold(name))
    )
    try:
        file_content = await utils.get_audio(file)
    except utils.FileNotFound:
        return await msg.edit_text(
            _("💔 You must attach {formats} or {format_last} audio.").format(
                formats=", ".join(list(set(utils.mimes_to_format.values()))[:-1]),
                format_last=list(set(utils.mimes_to_format.values()))[-1],
            )
        )
    except utils.MimeNotSupported as e:
        return await msg.edit_text(
            _("💔 Audio in format {mime} not supported. Use {formats} or {format_last}.").format(
                mime=e.mime,
                formats=", ".join(list(set(utils.mimes_to_format.values()))[:-1]),
                format_last=list(set(utils.mimes_to_format.values()))[-1],
            )
        )
    await msg.delete()
    vt = await models.VoiceTemplate(
        user_id=utils.cast(message.from_user).id,
        name=name,
    )
    voice = await message.reply_voice(
        types.BufferedInputFile(file_content, "audio.ogg"),
        caption=_("❤️ Voice template {name} is being created...").format(name=html.bold(name)),
    )
    vt.file_id = utils.cast(voice.voice).file_id
    await vt.save()
    await voice.edit_caption(
        caption=_("❤️ Voice template {name} created!").format(name=html.bold(name))
    )


@router.message(Command("vts"))
@router.message(utils.multiregexp(F.text, r"^гшабы$", r"^vts$"))
async def show_voice_templates_list(message: types.Message):
    templates = await models.VoiceTemplate.filter(user_id=utils.cast(message.from_user).id)
    if not templates:
        return await message.reply(
            _("💔 You don't have any voice templates yet."),
        )
    await message.reply(
        html.bold(_("❤️ Your voice templates:\n"))
        + "\n".join(f"- {html.code(it.name)}" for it in templates),
    )


@router.message(
    utils.multiregexp(
        F.text,
        r"^гшаб (?P<name>[a-zA-ZА-Яа-яёЁ0-9 \.\-\+\!]+)$",
        r"^vt (?P<name>[a-zA-ZА-Яа-яёЁ0-9 \.\-\+\!]+)$",
    )
    .group("name")
    .as_("name")
)
async def show_voice_template(message: types.Message, name: str):
    template = await models.VoiceTemplate.get_or_none(
        user_id=utils.cast(message.from_user).id, name=name
    )
    if template is None:
        return await message.reply(
            _("💔 Voice template {name} not found.").format(name=html.bold(name))
        )
    await message.reply_voice(template.file_id)


@router.inline_query(
    utils.multiregexp(
        F.query,
        r"гшаб (?P<name>[a-zA-ZА-Яа-яёЁ0-9 \.\-\+\!]+)$",
        r"vt (?P<name>[a-zA-ZА-Яа-яёЁ0-9 \.\-\+\!]+)$",
    )
    .group("name")
    .as_("name")
)
async def show_user_templates(inline_query: types.InlineQuery, name: str):
    offset = int(inline_query.offset) if inline_query.offset else 0
    templates_count = await models.VoiceTemplate.filter(
        name__icontains=name, user_id=utils.cast(inline_query.from_user).id
    ).count()
    templates = (
        await models.VoiceTemplate.filter(
            name__icontains=name, user_id=utils.cast(inline_query.from_user).id
        )
        .limit(50)
        .offset(offset)
    )
    await inline_query.answer(
        [
            types.InlineQueryResultCachedVoice(
                id=f"tv:vt:{template.id.hex}",
                title=_("Voice template {name}").format(name=template.name),
                voice_file_id=template.file_id,
            )
            for template in templates
        ],
        next_offset=str(offset + 50) if templates_count > offset + 50 else None,
    )
