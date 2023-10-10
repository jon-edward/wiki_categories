from __future__ import annotations

from typing import Dict, List, Collection, Tuple, Union

import networkx

from wiki_categories.core.assets import Assets
from wiki_categories.core.serialized import SerializedCategory, SerializedCategoryTree


__all__ = (
    "CategoryTree",
)


class CategoryTree(networkx.DiGraph):

    def __init__(self, assets_or_serialized: Union[Assets, SerializedCategoryTree, None] = None, **attr):
        super().__init__(**attr)

        if assets_or_serialized is None:
            return

        if isinstance(assets_or_serialized, Assets):
            self._add_assets(assets_or_serialized)
        elif isinstance(assets_or_serialized, dict):
            self._add_serialized(assets_or_serialized)
        else:
            raise TypeError(f"Invalid type for CategoryTree input: {type(assets_or_serialized)}")

    def _add_serialized(self, serialized_category_tree: SerializedCategoryTree):
        for category in serialized_category_tree["categories"]:
            self.add_node(category["category_id"], **category)
        self.add_edges_from(serialized_category_tree["edges"])

    def _add_assets(self, assets: Assets):

        id_to_name: Dict[int, str] = {
            item.page_id: item.name for item in assets.page_table_entries()
        }

        name_to_id: Dict[str, int] = {
            v: k for k, v in id_to_name.items()
        }

        _edges: List[(int, int)] = []

        for category_link in assets.category_links_entries():
            linked_int_parent = name_to_id.get(category_link.parent_name, None)

            if category_link.child_id in id_to_name and linked_int_parent is not None:
                _edges.append((linked_int_parent, category_link.child_id))

        id_to_page_count: Dict[int, int] = {}

        for category in assets.category_table_entries():
            if category.name in name_to_id:
                #  Each subcategory is counted as a page.

                id_to_page_count[name_to_id[category.name]] = (
                        category.pages - category.subcategories
                )

        categories: Collection[SerializedCategory] = tuple(
            {
                "category_id": k,
                "name": v,
                "page_count": id_to_page_count[k]
            } for k, v in id_to_name.items())

        edges: Collection[Tuple[int, int]] = tuple(_edges)

        self._add_serialized({"categories": categories, "edges": edges})

    def dict(self) -> SerializedCategoryTree:
        return {
            "categories": tuple(
                self.nodes[x] for x in self.nodes
            ),
            "edges": tuple(self.edges)
        }
