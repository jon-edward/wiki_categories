import json
import pathlib

from wiki_categories.core.category_tree import CategoryTree
from wiki_categories.core.serializable import CategoryTreeData


def main():
    test_serialized = pathlib.Path("../_data/output_de.json")

    try:
        with open(test_serialized, 'r', encoding="utf-8") as f:
            tree = CategoryTree.load(f)
    
    except FileNotFoundError:
        with open(test_serialized, 'w', encoding="utf-8") as f:
            tree = CategoryTree.for_langauge("de")
            tree.dump(f)

    from wiki_categories.core.transform import remove_by_hidden

    print(len(remove_by_hidden("de", tree)))

    print(tree)

if __name__ == '__main__':
    main()
