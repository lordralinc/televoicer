import re
import uuid

from aiogram import F, Router, html, types
from aiogram.filters import CommandObject, CommandStart
from aiogram.utils.i18n import gettext as _

from televoicer import models, utils

__all__ = ("router",)
router = Router()

MAX_TEMPLATES_LEN = 5


async def _import_pack(message: types.Message, shortcode: str, user: models.User):
    pack = await models.VoiceTemplatePack.get_or_none(shortcode=shortcode)

    if not pack:
        return await message.reply(
            _("💔 Voice pack with shortcode {shortcode} not found!").format(
                shortcode=html.bold(shortcode)
            )
        )
    my_templates = await models.VoiceTemplate.filter(user=user).values_list(
        "origin_template_id", "name"
    )
    my_templates_ids = {it[0] for it in my_templates}
    my_templates_names = {it[1] for it in my_templates}

    pack_templates = await pack.templates.all()

    templates_to_add = []
    templates_not_includes = []
    for template in pack_templates:
        if template.id in my_templates_ids:
            templates_not_includes.append(template)
            continue
        _name = template.name
        index = 1
        while _name in my_templates_names:
            _name = f"{template.name} {index}"
            index += 1
        templates_to_add.append(
            models.VoiceTemplate(
                id=uuid.uuid4(),
                user=user,
                name=_name,
                origin_template=template,
                file_id=template.file_id,
            )
        )
    if templates_to_add:
        await models.VoiceTemplate.bulk_create(templates_to_add)

    text = []
    if templates_to_add:
        pack.usage_count += 1
        await pack.save(update_fields=["usage_count"])
        text.append(
            _("❤️ Added {count} new voice templates: {templates}").format(
                count=len(templates_to_add),
                templates=", ".join(html.bold(t.name) for t in templates_to_add[:5])
                + ("..." if len(templates_to_add) > MAX_TEMPLATES_LEN else ""),
            )
        )
    if templates_not_includes:
        text.append(
            _("💔 Skipped {count} already existing templates: {templates}").format(
                count=len(templates_not_includes),
                templates=", ".join(html.bold(t.name) for t in templates_not_includes[:5])
                + ("..." if len(templates_not_includes) > MAX_TEMPLATES_LEN else ""),
            )
        )
    if text:
        await message.reply("\n".join(text))
    else:
        await message.reply(_("💔 No new templates were added."))


@router.message(
    utils.multiregexp(
        F.text,
        r"^пак импорт (?P<shortcode>[a-zA-Z0-9]+)$",
        r"^pack import (?P<shortcode>[a-zA-Z0-9]+)$",
        flags=re.IGNORECASE,
    )
    .group("shortcode")
    .as_("shortcode")
)
async def add_voice_to_pack(message: types.Message, shortcode: str, user: models.User):
    await _import_pack(message, shortcode, user)


@router.message(
    CommandStart(deep_link=True, deep_link_encoded=True, magic=F.args.startswith("avp:"))
)
async def handle_start_command(message: types.Message, command: CommandObject, user: models.User):
    await _import_pack(message, utils.require(command.args).replace("avp:", ""), user)
