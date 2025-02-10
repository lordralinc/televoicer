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


class ShowVoiceTemplatePacks(CallbackData, prefix="televoicer"):
    act: typing.Literal["svtpl"]
    page: int = 1


@router.message(Command("vtps"))
@router.message(
    utils.multiregexp(
        F.text,
        r"^мои паки$",
        r"^my packs$",
        flags=re.IGNORECASE,
    )
    | utils.multiregexp(
        F.text,
        r"^мои паки (?P<page>\d+)$",
        r"^my packs (?P<page>\d+)$",
        flags=re.IGNORECASE,
    )
    .group("page")
    .cast(int)
    .as_("page")
)
@router.callback_query(ShowVoiceTemplatePacks.filter(F.act == "svtpl"))
async def add_voice_to_pack(
    message: types.Message | types.CallbackQuery,
    user: models.User,
    page: int = 1,
    callback_data: ShowVoiceTemplatePacks | None = None,
):
    if callback_data:
        page = callback_data.page
    qs = models.VoiceTemplatePack.filter(author=user)
    paginator = utils.Paginator(qs, 10)
    if await paginator.total_count == 0:
        return await (message.reply if isinstance(message, types.Message) else message.answer)(
            _("💔 You don't have any voice template packs yet."),
        )
    page_data = await paginator.get_page(page)
    builder = InlineKeyboardBuilder()
    for icon, page_index in page_data.page_range():
        builder.button(
            text=icon,
            callback_data=ShowVoiceTemplatePacks(act="svtpl", page=page_index),
        )
    if isinstance(message, types.Message):
        return await message.reply(
            html.bold(
                _("❤️ Your voice template packs ({page}/{total_page}):\n").format(
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
            _("❤️ Your voice template packs ({page}/{total_page}):\n").format(
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
