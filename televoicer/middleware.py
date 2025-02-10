import collections
import collections.abc
import typing

import aiogram
from aiogram.types import CallbackQuery, InlineQuery, Message, TelegramObject

from televoicer import models

__all__ = ("CreateUserMiddleware",)


class CreateUserMiddleware(aiogram.BaseMiddleware):
    async def __call__(
        self,
        handler: collections.abc.Callable[
            [TelegramObject, dict[str, typing.Any]], collections.abc.Awaitable[typing.Any]
        ],
        event: TelegramObject,
        data: dict[str, typing.Any],
    ) -> typing.Any:  # pragma: no cover
        if isinstance(event, Message | CallbackQuery | InlineQuery) and event.from_user:
            user = await models.User.get_or_none(id=event.from_user.id)

            if not user:
                user = await models.User.create(
                    id=event.from_user.id, username=event.from_user.full_name
                )
            if user.username != event.from_user.full_name:
                user.username = event.from_user.full_name
                await user.save(update_fields=["username"])
            data["user"] = user
        return await handler(event, data)
