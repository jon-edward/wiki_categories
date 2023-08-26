import json
import pathlib

from category_tree.generate.category_tree_data import CategoryTreeData


def deserialize(category_tree_json_file: pathlib.Path) -> CategoryTreeData:
    with open(category_tree_json_file, 'r', encoding="utf-8") as f:
        return CategoryTreeData.from_dict(json.load(f))
