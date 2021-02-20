import itertools
import random
from typing import List, Tuple

from components.filters._base import FilterBase
from components.library import chunks


class BasicSparkleFilter(FilterBase):
    mults = [.20, .40, .60, .80, 1.00]

    @classmethod
    def _do_sparkle(cls, val: Tuple[int, int, int]) -> Tuple[int, int, int]:
        return int(random.choice(cls.mults) * val)

    @classmethod
    def do_filter(cls, id: int, payload: List[int]):
        chunked = chunks(payload, 3)
        return list(itertools.chain.from_iterable([cls._do_sparkle(chunk) for chunk in chunked]))
