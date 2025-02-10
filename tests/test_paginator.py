import random

import pytest

from televoicer.utils import Paginator


class QS:

    def __init__(self, count: int = 100) -> None:
        self._limit = 1
        self._count = count

    def limit(self, limit: int) -> "QS":
        return self

    def offset(self, offset: int) -> "QS":
        return self

    async def count(self) -> int:
        return self._count

    def __await__(self):
        async def _inner() -> list[int]:
            return [random.randint(0, 100_000) for _ in range(self._limit)]

        return _inner().__await__()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("count", "ppcount", "page", "expect_range", "next_page", "prev_page"),
    [
        (3, 3, 1, [("1", 1)], None, None),
        (10, 3, 1, [("1", 1), (">", 2), (">>", 4)], 2, None),
        (10, 3, 2, [("<", 1), ("2", 2), (">", 3), (">>", 4)], 3, 1),
        (13, 3, 3, [("<<", 1), ("<", 2), ("3", 3), (">", 4), (">>", 5)], 4, 2),
    ],
)
async def test_paginator(
    count: int,
    ppcount: int,
    page: int,
    expect_range: list[tuple[str, int]],
    next_page: int | None,
    prev_page: int | None,
):
    paginator = Paginator(QS(count), ppcount)  # type: ignore
    page_data = await paginator.get_page(page)

    assert page_data.page_range() == expect_range, "Ranges not equals"
    if next_page is None:
        assert not page_data.has_next, "Next page exists"
    else:
        assert page_data.has_next, "Next page not exists"
        assert (await page_data.get_next()).page == next_page, "Next page is not equals"
    if prev_page is None:
        assert not page_data.has_prev, "Prev page exists"
    else:
        assert page_data.has_prev, "Prev page not exists"
        assert (await page_data.get_prev()).page == prev_page, "Prev page is not equals"
