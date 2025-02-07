import io
import re
import typing
from functools import reduce
from tempfile import NamedTemporaryFile

from aiogram import types
from magic_filter import MagicFilter
from pydub import AudioSegment

from televoicer.dispatcher import bot

__all__ = (
    "CONVERTER_FORMATS",
    "FileNotFound",
    "MimeNotSupported",
    "cast",
    "convert_audio",
    "get_audio",
    "mimes_to_format",
    "multiregexp",
)

type CONVERTER_FORMATS = typing.Literal["mp3", "wav", "ogg"]


@typing.overload
def cast[T](value: T | None) -> T: ...
@typing.overload
def cast[T](value: typing.Any, d: T) -> T: ...


def cast[T](value: typing.Any, d: T | None = None) -> T:
    return value


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
            audio.export(ogg_buffer, format=output_format, parameters=["-ac", "1"])
            ogg_data = ogg_buffer.getvalue()

        return ogg_data

    except Exception as e:
        raise RuntimeError(f"Ошибка при конвертации {input_format} в {output_format}") from e


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
    await bot.download_file(cast(tg_file.file_path), dest)
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
