import ast
import dataclasses
import re
from typing import List, TypeVar, Callable, Any, Iterable

_category_re = re.compile(rb"\(\d+,('(?:[^']|\\')*'),(\d+),(\d+),\d+\)")


@dataclasses.dataclass
class CategoryInfo:
    name: str
    page_count: int
    subcategory_count: int


def parse_category_line(line: bytes) -> List[CategoryInfo]:
    hits = _category_re.findall(line)
    parsed = []

    for _name, _pages, _subcategories in hits:
        try:
            _name = ast.literal_eval(_name.decode())
        except UnicodeDecodeError:
            _name = ast.literal_eval(_name.decode(encoding="latin"))

        _pages = int(_pages)
        _subcategories = int(_subcategories)

        parsed.append(CategoryInfo(_name, _pages, _subcategories))

    return parsed


_category_links_re = re.compile(
    rb"\((\d+),('(?:[^']|\\')*'),(?:'(?:[^']|\\')*',){4}'subcat'\)"
)


@dataclasses.dataclass
class CategoryLink:
    child_id: int
    parent_name: str


def parse_category_links_line(line: bytes) -> List[CategoryLink]:
    hits = _category_links_re.findall(line)
    parsed = []

    for _id, _name in hits:
        _id = int(_id)
        _name = ast.literal_eval(_name.decode())
        parsed.append(CategoryLink(_id, _name))

    return parsed


_page_re = re.compile(rb"\((\d+),14,('(?:[^']|\\')*'),")


@dataclasses.dataclass
class PageTableItem:
    item_id: int
    name: str


def parse_page_table_line(line: bytes) -> List[PageTableItem]:
    hits = _page_re.findall(line)
    parsed = []

    for _id, _name in hits:
        _id = int(_id)
        _name = ast.literal_eval(_name.decode())
        parsed.append(PageTableItem(_id, _name))

    return parsed


T = TypeVar("T")


def parse(
    lines: Iterable[bytes], parse_line_func: Callable[[bytes], List[T]]
) -> List[T]:
    hits: List[Any] = []

    for line in lines:
        hits.extend(parse_line_func(line))

    return hits
