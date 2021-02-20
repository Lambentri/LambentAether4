from typing import List


class FilterBase:
    def do_filter(self, id: int, values: List[int]):
        raise NotImplemented("End user must implement a do_filter")
