from __future__ import annotations

from dataclasses import dataclass, asdict, astuple
from typing import TypedDict, Collection, Tuple, cast, Dict, List

from dacite import Config, from_dict

from wiki_categories.core.resources import CategoryTableData, CategoryLinksData, PageTableData, ProgressManager, \
    get_category_table_resource_data, get_category_links_resource_data, get_page_table_resource_data, ResourceConfig

__all__ = (
    "CategoryData",
    "SerializedCategoryData",
    "TreeEdge",
    "CategoryTreeData",
    "SerializedCategoryTreeData"
)


@dataclass(frozen=True)
class CategoryData:
    """
    Dataclass that contains data about a given category.
    """

    category_id: int
    name: str
    page_count: int


class SerializedCategoryData(TypedDict):
    """
    Mirrors CategoryData, used for type checking.
    """

    category_id: int
    name: str
    page_count: int


@dataclass(frozen=True)
class TreeEdge:
    """
    Dataclass that defines an edge from one category id to another.
    """

    child_id: int
    parent_id: int


def _tree_edge_type_hook(value: Collection[int]) -> TreeEdge:
    return TreeEdge(*value)


def _dacite_config() -> Config:
    return Config(type_hooks={TreeEdge: _tree_edge_type_hook},)


class SerializedCategoryTreeData(TypedDict):
    """
    CategoryTreeData converted to a dict.
    """

    categories: Collection[SerializedCategoryData]
    edges: Collection[Tuple[int, int]]


@dataclass(frozen=True)
class CategoryTreeData:
    """
    Dataclass that contains node and edge data to construct a category graph.
    """

    categories: Collection[CategoryData]
    edges: Collection[TreeEdge]

    def dict(self) -> SerializedCategoryTreeData:
        """
        Alternative to dataclasses.asdict, deconstructs TreeEdge objects into a tuple to save space
        in its serialized form.
        """

        return {
            "categories": [asdict(c) for c in self.categories],
            "edges": [cast(Tuple[int, int], astuple(e)) for e in self.edges]
        }

    @classmethod
    def from_dict(cls, d: SerializedCategoryTreeData) -> CategoryTreeData:
        """
        Creates a CategoryTreeData object from a dict.
        """

        return from_dict(cls, d, config=_dacite_config())

    @classmethod
    def from_resource_data(
            cls,
            category_table_data: CategoryTableData,
            category_links_data: CategoryLinksData,
            page_table_data: PageTableData) -> CategoryTreeData:
        """
        Construct 
        :param category_table_data:
        :param category_links_data:
        :param page_table_data:
        :return:
        """

        id_to_name: Dict[int, str] = {
            item.page_id: item.name for item in page_table_data.process()
        }

        name_to_id: Dict[str, int] = {
            v: k for k, v in id_to_name.items()
        }

        edges: List[(int, int)] = []

        for category_link in category_links_data.process():
            linked_int_parent = name_to_id.get(category_link.parent_name, None)

            if category_link.child_id in id_to_name and linked_int_parent is not None:
                edges.append((linked_int_parent, category_link.child_id))

        id_to_page_count: Dict[int, int] = {}

        for category in category_table_data.process():
            if category.name in name_to_id:
                #  Each subcategory is counted as a page.

                id_to_page_count[name_to_id[category.name]] = (
                        category.pages - category.subcategories
                )

        categories = tuple(CategoryData(k, v, id_to_page_count[k]) for k, v in id_to_name.items())
        tree_edges = tuple(
            TreeEdge(*e) for e in edges
        )

        return cls(categories, tree_edges)

    @classmethod
    def for_language(
            cls,
            language: str,
            resource_config: ResourceConfig) -> CategoryTreeData:

        resource_args = (language, resource_config)

        return cls.from_resource_data(
            get_category_table_resource_data(
                *resource_args
            ),
            get_category_links_resource_data(
                *resource_args
            ),
            get_page_table_resource_data(
                *resource_args
            )
        )
