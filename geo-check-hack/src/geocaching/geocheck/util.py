from typing import List


def in_groups_of(lst: List, size: int) -> List[List]:
    return [lst[i:i + size] for i in range(0, len(lst), size)]
