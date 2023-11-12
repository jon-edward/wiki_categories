from __future__ import annotations

from typing import Dict, List, Tuple, Union

import networkx
import numpy as np
import pandas as pd

from wiki_categories.core.assets import Assets


__all__ = (
    "CategoryTree",
    "less_than_page_count_percentile"
)


def less_than_page_count_percentile(
        cat_tree: CategoryTree,
        page_percentile: int) -> List[int]:

    cutoff = np.percentile(list(cat_tree.nodes[x]["page_count"] for x in cat_tree.nodes), page_percentile)

    return [x for x in cat_tree.nodes if cat_tree.nodes[x]["page_count"] < cutoff]


class CategoryTree(networkx.DiGraph):

    def __init__(self, assets_or_dataframes: Union[Assets, Tuple[pd.DataFrame, pd.DataFrame], None] = None, *,
                 delete_without_attributes: bool = True, **attr):

        super().__init__(**attr)

        if assets_or_dataframes is None:
            return

        if isinstance(assets_or_dataframes, Assets):
            self._add_assets(assets_or_dataframes)
        elif isinstance(assets_or_dataframes, tuple):
            self._add_dataframes(assets_or_dataframes)
        else:
            raise TypeError(f"Invalid type for CategoryTree input: {type(assets_or_dataframes)}")

        #  Delete nodes without attributes

        if not delete_without_attributes:
            return

        for n in self.nodes:
            if not self.nodes[n]:
                print(n)
                self.remove_node_reconstruct(n)

    def _add_dataframes(self, dataframes: Tuple[pd.DataFrame, pd.DataFrame]):
        category_iter = zip(dataframes[0]["category_id"], dataframes[0]["name"], dataframes[0]["page_count"])

        for category_id, name, page_count in category_iter:
            self.add_node(category_id, category_id=category_id, name=name, page_count=page_count)

        self.add_edges_from(zip(dataframes[1]["from_id"], dataframes[1]["to_id"]))

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

        ordered_items = [(k, v) for k, v in id_to_name.items()]

        categories = pd.DataFrame(
            {
                "category_id": [c[0] for c in ordered_items],
                "name": [c[1] for c in ordered_items],
                "page_count": [id_to_page_count[c[0]] for c in ordered_items]
            }
        )

        edges = pd.DataFrame(
            {
                "from_id": [e[0] for e in _edges],
                "to_id": [e[1] for e in _edges]
            }
        )

        self._add_dataframes((categories, edges))

    def to_dataframes(self) -> (pd.DataFrame, pd.DataFrame):
        """
        Convert graph structure to pandas.DataFrames.

        :return: (categories DataFrame, edges DataFrame)
        """

        attr_list = [self.nodes[x] for x in self.nodes]

        categories_dict = {
            "category_id": [a["category_id"] for a in attr_list],
            "name": [a["name"] for a in attr_list],
            "page_count": [a["page_count"] for a in attr_list]
        }

        categories = pd.DataFrame(categories_dict)

        edge_list = [e for e in self.edges]

        edges_dict = {
            "from_id": [e[0] for e in edge_list],
            "to_id": [e[1] for e in edge_list]
        }

        edges = pd.DataFrame(edges_dict)

        return categories, edges

    def remove_node_reconstruct(self, category_id: int):
        successors = self.successors(category_id)
        predecessors = self.predecessors(category_id)

        new_edges = tuple((p, s) for p in predecessors for s in successors)

        self.add_edges_from(new_edges)
        self.remove_node(category_id)

