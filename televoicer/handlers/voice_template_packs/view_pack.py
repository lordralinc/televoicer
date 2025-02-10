import re
import typing

from aiogram import F, Router, html, types
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.i18n import gettext as _
from aiogram.utils.keyboard import InlineKeyboardBuilder

from televoicer import models, utils

__all__ = ("router",)
router = Router()


class ViewVoicePackCallbackData(CallbackData, prefix="televoicer"):
    act: typing.Literal["vvp"] = "vvp"
    shortcode: str


class ViewVoicePackTemplatesCallbackData(CallbackData, prefix="televoicer"):
    act: typing.Literal["vvpt"] = "vvpt"
    shortcode: str
    page: int


class ChangePrivacyVoicePackCallbackData(CallbackData, prefix="televoicer"):
    act: typing.Literal["cpvp"] = "cpvp"
    shortcode: str
    privacy: models.VoiceTemplatePack.Privacy


class RegenerateShortcodeVoicePackCallbackData(CallbackData, prefix="televoicer"):
    act: typing.Literal["rscvp"] = "rscvp"
    shortcode: str


class DeleteVoicePackCallbackData(CallbackData, prefix="televoicer"):
    act: typing.Literal["dvp"] = "dvp"
    shortcode: str
    force: bool


async def get_pack_or_notify(
    shortcode: str,
    target: types.Message | types.CallbackQuery,
    user: models.User | None = None,
) -> models.VoiceTemplatePack | None:
    if user:
        pack = await models.VoiceTemplatePack.get_or_none(shortcode=shortcode, author=user)
    else:
        pack = await models.VoiceTemplatePack.get_or_none(shortcode=shortcode)
    if pack is None:
        error_text = _("💔 Voice pack with shortcode {shortcode} not found!").format(
            shortcode=html.bold(shortcode)
        )
        if isinstance(target, types.CallbackQuery):
            await target.answer(error_text)
        else:
            await target.reply(text=error_text)
    return pack


async def send_or_edit_message(
    target: types.Message | types.CallbackQuery,
    text: str,
    reply_markup: types.InlineKeyboardMarkup | None = None,
):
    if isinstance(target, types.CallbackQuery):
        message = typing.cast(types.Message, target.message)
        await message.edit_text(text=text)
        if reply_markup is not None:
            await message.edit_reply_markup(reply_markup=reply_markup)
    else:
        await target.reply(text, reply_markup=reply_markup)


async def _view_voice_pack(
    target: types.Message | types.CallbackQuery,
    user: models.User,
    pack: models.VoiceTemplatePack,
):
    await pack.fetch_related("author", "templates")
    author = pack.author

    builder = InlineKeyboardBuilder()
    builder.button(
        text=_("view templates"),
        callback_data=ViewVoicePackTemplatesCallbackData(shortcode=pack.shortcode, page=1),
    )
    if author == user:
        builder.button(
            text=_("change privacy"),
            callback_data=ChangePrivacyVoicePackCallbackData(
                shortcode=pack.shortcode,
                privacy=(
                    models.VoiceTemplatePack.Privacy.PRIVATE
                    if pack.privacy == models.VoiceTemplatePack.Privacy.PUBLIC
                    else models.VoiceTemplatePack.Privacy.PUBLIC
                ),
            ),
        )
        builder.button(
            text=_("regenerate shortcode"),
            callback_data=RegenerateShortcodeVoicePackCallbackData(shortcode=pack.shortcode),
        )
        builder.button(
            text=_("delete"),
            callback_data=DeleteVoicePackCallbackData(shortcode=pack.shortcode, force=False),
        )
        builder.adjust(1, 2, 1)

    pack_info = _(
        "📢 {mode} voice pack {name} ({shortcode}) by {user_link}\n"
        "📊 Usage count: {usage_count}\n"
        "📝 Templates count: {templates_count}\n"
    ).format(
        mode=(
            _("Private")
            if pack.privacy == models.VoiceTemplatePack.Privacy.PRIVATE
            else _("Public")
        ),
        name=html.bold(pack.name),
        shortcode=html.code(pack.shortcode),
        user_link=html.link(author.username, f"tg://user?id={author.id}"),
        usage_count=html.italic(str(pack.usage_count)),
        templates_count=html.italic(str(await pack.templates.all().count())),
    )

    await send_or_edit_message(target, pack_info, reply_markup=builder.as_markup())


@router.message(
    utils.multiregexp(
        F.text,
        r"^пак (?P<shortcode>\w+)$",
        r"^pack (?P<shortcode>\w+)$",
        flags=re.IGNORECASE,
    )
    .group("shortcode")
    .as_("shortcode")
)
@router.callback_query(ViewVoicePackCallbackData.filter(F.act == "vvp"))
async def view_voice_pack(
    target: types.Message | types.CallbackQuery,
    user: models.User,
    shortcode: str | None = None,
    callback_data: ViewVoicePackCallbackData | None = None,
):
    shortcode = typing.cast(str, shortcode or (callback_data and callback_data.shortcode))
    pack = await get_pack_or_notify(shortcode, target)
    if pack is None:
        return
    await _view_voice_pack(target, user, pack)


@router.callback_query(ViewVoicePackTemplatesCallbackData.filter(F.act == "vvpt"))
async def show_templates(
    callback_query: types.CallbackQuery, callback_data: ViewVoicePackTemplatesCallbackData
):
    pack = await get_pack_or_notify(callback_data.shortcode, callback_query)
    if pack is None:
        return
    await callback_query.answer()
    paginator = utils.Paginator(pack.templates.all(), 5)
    page = await paginator.get_page(callback_data.page)
    builder = InlineKeyboardBuilder()
    builder.button(
        text=_("<< back"),
        callback_data=ViewVoicePackCallbackData(shortcode=callback_data.shortcode),
    )
    for icon, index in page.page_range():
        builder.button(
            text=icon,
            callback_data=ViewVoicePackTemplatesCallbackData(
                shortcode=callback_data.shortcode, page=index
            ),
        )
    builder.adjust(1, len(page.page_range()))
    for it in page.items:
        await utils.require(callback_query.message).answer_voice(
            it.file_id, caption=f"{pack.name} | {it.name}"
        )
    total_pages = await paginator.total_pages
    await utils.require(callback_query.message).answer(
        _("❤️ Voice templates in the {pack_name} pack ({page}/{total_pages})").format(
            pack_name=html.bold(pack.name),
            page=callback_data.page,
            total_pages=total_pages,
        ),
        reply_markup=builder.as_markup(),
    )


@router.callback_query(ChangePrivacyVoicePackCallbackData.filter(F.act == "cpvp"))
async def change_privacy(
    callback_query: types.CallbackQuery,
    callback_data: ChangePrivacyVoicePackCallbackData,
    user: models.User,
):
    pack = await get_pack_or_notify(callback_data.shortcode, callback_query, user)
    if pack is None:
        return
    pack.privacy = callback_data.privacy
    await pack.save(update_fields=["privacy"])
    await _view_voice_pack(callback_query, user, pack)


@router.callback_query(RegenerateShortcodeVoicePackCallbackData.filter(F.act == "rscvp"))
async def regenerate_shortcode(
    callback_query: types.CallbackQuery,
    callback_data: RegenerateShortcodeVoicePackCallbackData,
    user: models.User,
):
    pack = await get_pack_or_notify(callback_data.shortcode, callback_query, user)
    if pack is None:
        return
    pack.shortcode = models.VoiceTemplatePack.generate_shortcode()
    await pack.save(update_fields=["shortcode"])
    await _view_voice_pack(callback_query, user, pack)


@router.callback_query(DeleteVoicePackCallbackData.filter(F.act == "dvp"))
async def delete_voice_pack(
    callback_query: types.CallbackQuery,
    callback_data: DeleteVoicePackCallbackData,
    user: models.User,
):
    pack = await get_pack_or_notify(callback_data.shortcode, callback_query, user)
    if pack is None:
        return
    if callback_data.force:
        await pack.delete()
        await callback_query.answer(
            text=_("💔 Voice pack {name} (shortcode: {shortcode}) has been deleted!").format(
                name=pack.name, shortcode=callback_data.shortcode
            )
        )
        return
    builder = InlineKeyboardBuilder()
    callback_data.force = True
    builder.button(text=_("YES, DELETE"), callback_data=callback_data)
    builder.button(
        text=_("NO, DON'T DELETE"),
        callback_data=ViewVoicePackCallbackData(shortcode=callback_data.shortcode),
    )
    warning_text = (
        html.bold(_("⚠️ Warning!"))
        + "\n\n"
        + _(
            "This action is irreversible. Once deleted, the voice pack cannot be restored. "
            "Statistics will be permanently deleted, but templates will remain."
        )
    )
    await typing.cast(types.Message, callback_query.message).edit_text(warning_text)
    await typing.cast(types.Message, callback_query.message).edit_reply_markup(
        reply_markup=builder.as_markup()
    )
