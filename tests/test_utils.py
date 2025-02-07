import pathlib

import pytest

from televoicer.utils import CONVERTER_FORMATS, convert_audio

DATA_FOLDER = pathlib.Path(__file__).parent / "data"
FORMATS: list[tuple[pathlib.Path, CONVERTER_FORMATS]] = [
    (DATA_FOLDER / "audio.mp3", "mp3"),
    (DATA_FOLDER / "audio.wav", "wav"),
]


@pytest.mark.parametrize(
    ("data", "input_format", "output_format"),
    [
        pytest.param(t[0].read_bytes(), t[1], of, id=f"{t[1]}:{of}")
        for t in FORMATS
        for of in ["ogg", "mp3", "wav"]
    ],
)
def test_convert_audio(
    data: bytes, input_format: CONVERTER_FORMATS, output_format: CONVERTER_FORMATS
):
    convert_audio(data, input_format, output_format)
