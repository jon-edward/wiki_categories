from collections.abc import Collection
from typing import TypedDict, Tuple


class SerializedCategory(TypedDict):
    category_id: int
    name: str
    page_count: int


class SerializedCategoryTree(TypedDict):
    categories: Collection[SerializedCategory]
    edges: Collection[Tuple[int, int]]
