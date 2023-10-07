import json
import pathlib

from ..providers import CategoryTreeGraph, CategoryTreeData


def deserialize(from_file: pathlib.Path) -> CategoryTreeGraph:
    with open(from_file, 'r', encoding="utf-8") as f:
        return CategoryTreeGraph(CategoryTreeData(**json.load(f)))
