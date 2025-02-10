import io
import math
import re
import typing
from functools import reduce
from tempfile import NamedTemporaryFile

import tortoise
from aiogram import types
from magic_filter import MagicFilter
from pydub import AudioSegment
from tortoise.queryset import QuerySet

from televoicer.dispatcher import bot

__all__ = (
    "CONVERTER_FORMATS",
    "FileNotFound",
    "MimeNotSupported",
    "convert_audio",
    "get_audio",
    "mimes_to_format",
    "multiregexp",
    "require",
)

type CONVERTER_FORMATS = typing.Literal["mp3", "wav", "ogg"]


def require[T](value: T | None, *, only_type: bool = True) -> T:
    if not only_type and value is None:
        raise ValueError("Value is None")
    return value  # type: ignore


def convert_audio(
    data: bytes, input_format: CONVERTER_FORMATS, output_format: CONVERTER_FORMATS
) -> bytes:
    try:
        with NamedTemporaryFile(suffix=f".{input_format}", delete=True) as temp_file:
            temp_file.write(data)
            temp_file.flush()
            audio = AudioSegment.from_file(temp_file.name, format=input_format)
            if audio.channels == 2:  # noqa: PLR2004
                audio = audio.set_channels(1)
            ogg_buffer = io.BytesIO()
            audio.export(
                ogg_buffer, format=output_format, codec="libopus", parameters=["-ac", "1"]
            )
            ogg_data = ogg_buffer.getvalue()

        return ogg_data

    except Exception as e:
        raise RuntimeError(f"Error: {input_format} -> {output_format}") from e


mimes_to_format: dict[str, CONVERTER_FORMATS] = {
    "audio/ogg": "ogg",
    "audio/mpeg": "mp3",
    "audio/wav": "wav",
    "audio/vnd.wave": "wav",
}


class FileNotFound(ValueError): ...


class MimeNotSupported(ValueError):
    def __init__(self, mime: str, *args: object) -> None:
        super().__init__(*args)
        self.mime = mime


async def get_audio(file: types.Audio | types.Document | types.Voice | None) -> bytes:
    if not file:
        raise FileNotFound
    if file.mime_type is None:
        raise MimeNotSupported("unknown")
    file_format = mimes_to_format.get(file.mime_type)
    if not file_format:
        raise MimeNotSupported(file.mime_type)
    tg_file = await bot.get_file(file.file_id)
    dest = io.BytesIO()
    await bot.download_file(require(tg_file.file_path), dest)
    if file_format != "ogg":
        return convert_audio(dest.read(), file_format, "ogg")
    return dest.read()


def multiregexp(
    init_filter: MagicFilter,
    *regexp_patters: str | re.Pattern[str],
    reduce_mode: typing.Literal["OR", "AND"] = "OR",
    mode: str | None = None,
    search: bool | None = None,
    flags: int | re.RegexFlag = 0,
) -> MagicFilter:
    if not regexp_patters:
        raise ValueError("regexp_patters must be set")
    return reduce(
        lambda a, b: (a | b if reduce_mode == "OR" else a & b),
        [
            init_filter.regexp(pattern, mode=mode, search=search, flags=flags)
            for pattern in regexp_patters
        ],
    )


class Paginator[T: tortoise.Model]:

    class PaginatorCache(typing.TypedDict):
        prepared: bool
        count: int
        pages: dict[int, "PaginatorResponse"]

    def __init__(self, qs: QuerySet[T], count: int = 10) -> None:
        self.qs = qs
        self.count = count
        self._cache = self.PaginatorCache(prepared=False, count=-1, pages={})

    @property
    def cache(self) -> PaginatorCache:
        return self._cache

    @property
    async def total_count(self) -> int:
        if not self.cache["prepared"]:
            await self.prepare()
        return self.cache["count"]

    @property
    async def total_pages(self) -> int:
        if not self.cache["prepared"]:
            await self.prepare()
        return math.ceil(self.cache["count"] / self.count)

    async def prepare(self) -> None:
        self._cache["count"] = await self.qs.count()
        self._cache["prepared"] = True

    async def get_page(self, page: int = 1) -> "PaginatorResponse[T]":
        if not self._cache["prepared"]:
            await self.prepare()

        try:
            return self._cache["pages"][page]
        except KeyError:
            qs = self.qs.limit(self.count).offset((page - 1) * self.count)
            response = PaginatorResponse(
                self,
                page,
                await qs,
            )
            self._cache["pages"][page] = response
            return response


class PaginatorResponse[T: tortoise.Model]:
    def __init__(self, paginator: Paginator[T], page: int, items: list[T]) -> None:
        self.paginator = paginator
        self.page = page
        self.items = items

    @property
    def has_next(self) -> bool:
        return self.paginator.cache["count"] > self.page * self.paginator.count

    @property
    def has_prev(self) -> bool:
        return self.page != 1

    async def get_next(self) -> "PaginatorResponse[T]":
        return await self.paginator.get_page(self.page + 1)

    async def get_prev(self) -> "PaginatorResponse[T]":
        return await self.paginator.get_page(self.page - 1)

    def page_range(
        self,
        start_icon: str = "<<",
        end_icon: str = ">>",
        prev_icon: str = "<",
        next_icon: str = ">",
    ) -> list[tuple[str, int]]:
        if self.paginator.cache["count"] == 0:
            return []
        total_pages = math.ceil(self.paginator.cache["count"] / self.paginator.count)

        links: list[tuple[str, int]] = []

        if self.page > 2:  # noqa: PLR2004
            links.append((start_icon, 1))
        if self.page > 1:
            links.append((prev_icon, self.page - 1))
            links.append((str(self.page), self.page))
        else:
            links.append((str(self.page), self.page))
        if self.page < total_pages:
            links.append((next_icon, self.page + 1))
        if self.page < total_pages - 1:
            links.append((end_icon, total_pages))
        return links
