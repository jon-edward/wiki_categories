import datetime
import os
from tempfile import NamedTemporaryFile
from typing import Dict

import wiki_data_dump as wdd
from wiki_data_dump.mirrors import MirrorType

from category_tree.generate.category_tree_data import CategoryTreeData, MetaDict
from category_tree.generate.download import (
    download_page_table,
    download_category_links_table,
    download_category_info,
)
from category_tree.generate.parse import (
    parse,
    parse_page_table_line,
    parse_category_links_line,
    parse_category_line,
)


class _TemporaryFileManager:
    file_name: str

    def __init__(self, file_name: str):
        self.file_name = file_name

    def __enter__(self) -> str:
        return self.file_name

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.unlink(self.file_name)


def fetch_category_tree_data(
    language: str, *, data_dump: wdd.WikiDump = None
) -> CategoryTreeData:
    if data_dump is None:
        data_dump = wdd.WikiDump(MirrorType.YOUR)

    file_buffer = NamedTemporaryFile(delete=False)
    file_buffer.close()

    meta: Dict[str, MetaDict] = {}

    pagetable_data = download_page_table(language, data_dump)
    pagetable_updated: datetime.date = pagetable_data.updated_date

    meta["pagetable"] = {"updated": pagetable_updated}

    id_to_name = {
        item.item_id: item.name
        for item in parse(pagetable_data.lines, parse_page_table_line)
    }

    name_to_id = {v: k for k, v in id_to_name.items()}

    categorylinks_data = download_category_links_table(language, data_dump)
    categorylinks_updated: datetime.date = categorylinks_data.updated_date

    meta["categorylinks"] = {"updated": categorylinks_updated}

    edges = []

    for category_link in parse(categorylinks_data.lines, parse_category_links_line):
        linked_int_parent = name_to_id.get(category_link.parent_name, None)
        if category_link.child_id in id_to_name and linked_int_parent is not None:
            edges.append((linked_int_parent, category_link.child_id))

    category_data = download_category_info(language, data_dump)
    category_updated: datetime.date = category_data.updated_date

    meta["category"] = {"updated": category_updated}

    id_to_page_count = {}

    for category_info in parse(category_data.lines, parse_category_line):
        if category_info.name in name_to_id:
            #  Each subcategory is counted as a page as well.
            id_to_page_count[name_to_id[category_info.name]] = (
                category_info.page_count - category_info.subcategory_count
            )

    return CategoryTreeData(
        language=language,
        meta=meta,
        id_to_name=id_to_name,
        id_to_page_count=id_to_page_count,
        edges=edges,
    )
