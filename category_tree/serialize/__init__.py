import json
import pathlib

from category_tree.generate.category_tree_data import CategoryTreeData


def serialize(category_tree_data: CategoryTreeData, to_file: pathlib.Path):
    with open(to_file, 'wb') as f:
        content = json.dumps(category_tree_data.to_dict(), ensure_ascii=False, indent=1)
        f.write(content.encode("utf-8"))
