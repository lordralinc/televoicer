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


class ShowVoiceTemplate(CallbackData, prefix="televoicer"):
    act: typing.Literal["svtl"]
    page: int = 1


@router.message(Command("vts"))
@router.message(
    utils.multiregexp(F.text, r"^гшабы$", r"^vts$", flags=re.IGNORECASE)
    | utils.multiregexp(
        F.text, r"^гшабы (?P<page>\d+)$", r"^vts (?P<page>\d+)$", flags=re.IGNORECASE
    )
    .group("page")
    .cast(int)
    .as_("page")
)
@router.callback_query(ShowVoiceTemplate.filter(F.act == "svtl"))
async def show_voice_templates_list(
    message: types.Message | types.CallbackQuery,
    user: models.User,
    page: int = 1,
    callback_data: ShowVoiceTemplate | None = None,
):
    if callback_data:
        page = callback_data.page

    qs = models.VoiceTemplate.filter(user=user)

    paginator = utils.Paginator(qs, 10)
    if await paginator.total_count == 0:
        return await (message.reply if isinstance(message, types.Message) else message.answer)(
            _("💔 You don't have any voice templates yet."),
        )

    page_data = await paginator.get_page(page)

    builder = InlineKeyboardBuilder()
    for icon, page_index in page_data.page_range():
        builder.button(
            text=icon,
            callback_data=ShowVoiceTemplate(act="svtl", page=page_index),
        )

    if isinstance(message, types.Message):
        return await message.reply(
            html.bold(
                _("❤️ Your voice templates ({page}/{total_page}):\n").format(
                    page=page, total_page=await paginator.total_pages
                )
            )
            + "\n".join(f"- {html.code(html.quote(it.name))}" for it in page_data.items),
            reply_markup=builder.as_markup(),
        )
    await typing.cast(types.Message, message.message).edit_text(
        text=html.bold(
            _("❤️ Your voice templates ({page}/{total_page}):\n").format(
                page=page, total_page=await paginator.total_pages
            )
        )
        + "\n".join(f"- {html.code(html.quote(it.name))}" for it in page_data.items),
    )
    await typing.cast(types.Message, message.message).edit_reply_markup(
        reply_markup=builder.as_markup()
    )
