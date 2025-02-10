import re
import typing

from aiogram import F, Router, html, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.i18n import gettext as _

from televoicer import models, utils

__all__ = ("router",)
router = Router()

MIME_FORMATS = list(set(utils.mimes_to_format.values()))


def extract_file(message: types.Message) -> types.Document | types.Voice | types.Audio | None:
    if message.audio or message.document or message.voice:
        return message.audio or message.document or message.voice
    if message.reply_to_message:
        return (
            message.reply_to_message.audio
            or message.reply_to_message.document
            or message.reply_to_message.voice
        )
    return None


async def handle_audio(
    message: types.Message, file: types.Document | types.Voice | types.Audio, template_name: str
):
    msg = await message.reply(
        _("❤️ Voice template {name} is being created...").format(
            name=html.bold(html.quote(template_name))
        )
    )

    try:
        file_content = await utils.get_audio(file)
    except utils.FileNotFound:
        return await msg.edit_text(
            _("💔 You must attach {formats} or {format_last} audio.").format(
                formats=", ".join(MIME_FORMATS[:-1]),
                format_last=MIME_FORMATS[-1],
            )
        )
    except utils.MimeNotSupported as e:
        return await msg.edit_text(
            _("💔 Audio in format {mime} not supported. Use {formats} or {format_last}.").format(
                mime=e.mime,
                formats=", ".join(MIME_FORMATS[:-1]),
                format_last=MIME_FORMATS[-1],
            )
        )

    await msg.delete()

    voice = await message.reply_voice(
        types.BufferedInputFile(file_content, "audio.ogg"),
        caption=_("❤️ Voice template {name} is being created...").format(
            name=html.bold(html.quote(template_name))
        ),
    )

    vt = await models.VoiceTemplate.create(
        user_id=utils.require(message.from_user).id,
        name=template_name,
        file_id=utils.require(voice.voice).file_id,
    )
    await voice.edit_caption(
        _("❤️ Voice template {name} created!").format(name=html.bold(html.quote(vt.name)))
    )


@router.message(
    (
        F.audio
        | F.document
        | F.voice
        | (
            F.reply_to_message
            & (F.reply_to_message.audio | F.reply_to_message.document | F.reply_to_message.voice)
        )
    )
    & (
        (F.caption | F.text)
        & utils.multiregexp(
            F.caption | F.text,
            r"^\+гшаб (?P<name>[\S ]+)$",
            r"^\+vt (?P<name>[\S ]+)$",
            flags=re.IGNORECASE,
        )
    )
    .group("name")
    .as_("name")
)
async def save_voice_template(message: types.Message, user: models.User, name: str):
    if await models.VoiceTemplate.exists(user=user, name=name):
        return await message.reply(
            _("💔 The voice template {name} already exists.").format(
                name=html.bold(html.quote(name))
            )
        )

    file = extract_file(message)
    if file:
        await handle_audio(message, file, name)


class Form(StatesGroup):
    name = State()


@router.message(
    F.audio
    | F.document
    | F.voice
    | (
        F.reply_to_message
        & (F.reply_to_message.audio | F.reply_to_message.document | F.reply_to_message.voice)
    )
)
async def save_voice_template_audio(message: types.Message, user: models.User, state: FSMContext):
    file = extract_file(message)
    if not file:
        return await message.reply(_("💔 No valid audio file found."))

    template_name = (
        file.file_name.split(".", 1)[0]
        if message.media_group_id and not isinstance(file, types.Voice) and file.file_name
        else ""
    )

    if message.media_group_id and template_name:
        if await models.VoiceTemplate.exists(user=user, name=template_name):
            return await message.reply(
                _("💔 The voice template {name} already exists.").format(
                    name=html.bold(html.quote(template_name))
                )
            )
        await handle_audio(message, file, template_name)
    else:
        voice = await message.reply_voice(
            types.BufferedInputFile(await utils.get_audio(file), "audio.ogg"),
            caption=_("❤️ Enter name for template or type /cancel to cancel request"),
        )
        await state.set_state(Form.name)
        await state.update_data(file_id=utils.require(voice.voice).file_id)


@router.message(Form.name)
async def save_voice_template_name(message: types.Message, user: models.User, state: FSMContext):
    file_id = typing.cast(str, (await state.get_data()).get("file_id"))
    template_name = message.text or ""

    if await models.VoiceTemplate.exists(user=user, name=template_name):
        return await message.reply(
            _("💔 The voice template {name} already exists.").format(
                name=html.bold(html.quote(template_name))
            )
            + "\n\n"
            + _("❤️ Enter name for template or type /cancel to cancel request")
        )

    vt = await models.VoiceTemplate.create(user=user, name=template_name, file_id=file_id)
    await message.reply(
        _("❤️ Voice template {name} created!").format(name=html.bold(html.quote(vt.name)))
    )
    await state.clear()
