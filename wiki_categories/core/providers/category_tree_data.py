import dataclasses
from typing import Dict, List, Tuple

import requests
import wiki_data_dump as wdd

from .resource_data import CategoryData, \
    CategoryLinkData, \
    PageTableData

from .resources import ProgressManager


@dataclasses.dataclass
class CategoryTreeData:
    id_to_name: Dict[int, str]
    id_to_page_count: Dict[int, int]
    edges: List[Tuple[int, int]]

    @classmethod
    def from_resource_data(
            cls,
            category_data: CategoryData,
            category_link_data: CategoryLinkData,
            page_table_data: PageTableData
    ):
        id_to_name: Dict[int, str] = {
            item.page_id: item.name for item in page_table_data.process()
        }

        name_to_id: Dict[str, int] = {
            v: k for k, v in id_to_name.items()
        }

        edges: List[(int, int)] = []

        for category_link in category_link_data.process():
            linked_int_parent = name_to_id.get(category_link.parent_name, None)

            if category_link.child_id in id_to_name and linked_int_parent is not None:
                edges.append((linked_int_parent, category_link.child_id))

        id_to_page_count: Dict[int, int] = {}

        for category in category_data.process():
            if category.name in name_to_id:
                #  Each subcategory is counted as a page.

                id_to_page_count[name_to_id[category.name]] = (
                        category.pages - category.subcategories
                )

        return cls(id_to_name, id_to_page_count, edges)

    @classmethod
    def from_language(
            cls,
            language: str,
            wiki_dump: wdd.WikiDump,
            session: requests.Session,
            progress_manager: ProgressManager
    ):

        data = CategoryTreeData.from_resource_data(
            CategoryData.from_language_dump(language, wiki_dump, session, progress_manager),
            CategoryLinkData.from_language_dump(language, wiki_dump, session, progress_manager),
            PageTableData.from_language_dump(language, wiki_dump, session, progress_manager)
        )

        return data