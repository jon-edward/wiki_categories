import json

from wiki_data_dump import WikiDump
from wiki_data_dump.mirrors import MirrorType

from wiki_categories.core.assets import Assets
from wiki_categories.core.category_tree import CategoryTree


def main():
    tree = CategoryTree(Assets("de", wiki_dump=WikiDump(mirror=MirrorType.WIKIMEDIA)))

    with open("../_data/output.json", 'w') as f_buffer:
        json.dump(tree.dict(), f_buffer, ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
