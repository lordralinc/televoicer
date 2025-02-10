import re
import typing

from aiogram import F, Router, html, types
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.i18n import gettext as _
from aiogram.utils.keyboard import InlineKeyboardBuilder

from televoicer import models, utils

__all__ = ("router",)
router = Router()


class GlobalShowVoiceTemplatePacks(CallbackData, prefix="televoicer"):
    act: typing.Literal["gsvtpl"]
    page: int = 1


@router.message(Command("gvtps"))
@router.message(
    utils.multiregexp(
        F.text,
        r"^паки$",
        r"^packs$",
        flags=re.IGNORECASE,
    )
    | utils.multiregexp(
        F.text,
        r"^паки (?P<page>\d+)$",
        r"^packs (?P<page>\d+)$",
        flags=re.IGNORECASE,
    )
    .group("page")
    .cast(int)
    .as_("page")
)
@router.callback_query(GlobalShowVoiceTemplatePacks.filter(F.act == "gsvtpl"))
async def show_global_pack_list(
    message: types.Message | types.CallbackQuery,
    user: models.User,
    page: int = 1,
    callback_data: GlobalShowVoiceTemplatePacks | None = None,
):
    if callback_data:
        page = callback_data.page
    qs = models.VoiceTemplatePack.filter(privacy=models.VoiceTemplatePack.Privacy.PUBLIC).order_by(
        "-usage_count"
    )
    paginator = utils.Paginator(qs, 10)
    if await paginator.total_count == 0:
        return await (message.reply if isinstance(message, types.Message) else message.answer)(
            _("💔 Don't have any voice template packs yet."),
        )
    page_data = await paginator.get_page(page)
    builder = InlineKeyboardBuilder()
    for icon, page_index in page_data.page_range():
        builder.button(
            text=icon,
            callback_data=GlobalShowVoiceTemplatePacks(act="gsvtpl", page=page_index),
        )
    if isinstance(message, types.Message):
        return await message.reply(
            html.bold(
                _("❤️ Voice template packs ({page}/{total_page}):\n").format(
                    page=page, total_page=await paginator.total_pages
                )
            )
            + "\n".join(
                f"- {html.code(it.shortcode)} | {html.bold(it.name)} | {it.usage_count}"
                for it in page_data.items
            ),
            reply_markup=builder.as_markup(),
        )
    await typing.cast(types.Message, message.message).edit_text(
        text=html.bold(
            _("❤️ Voice template packs ({page}/{total_page}):\n").format(
                page=page, total_page=await paginator.total_pages
            )
        )
        + "\n".join(
            f"- {html.code(it.shortcode)} | {html.bold(it.name)} | {it.usage_count}"
            for it in page_data.items
        ),
    )
    await typing.cast(types.Message, message.message).edit_reply_markup(
        reply_markup=builder.as_markup()
    )
