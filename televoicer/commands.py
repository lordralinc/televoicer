from aiogram.types import BotCommand, BotCommandScopeDefault
from aiogram.utils.i18n import I18n

from televoicer.dispatcher import bot

__all__ = ("set_commands",)


async def set_commands(i18n: I18n):

    for locale_key, locale in i18n.locales.items():
        commands = [
            BotCommand(command="help", description=locale.gettext("Show help")),
            BotCommand(command="vts", description=locale.gettext("View your templates")),
            BotCommand(
                command="vtps", description=locale.gettext("View your voice template packs")
            ),
            BotCommand(
                command="gvtps", description=locale.gettext("Browse public voice template packs")
            ),
            BotCommand(command="cancel", description=locale.gettext("Cancel current action")),
        ]
        await bot.set_my_commands(commands, BotCommandScopeDefault(), language_code=locale_key)
