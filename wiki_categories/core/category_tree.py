from __future__ import annotations

import json
from dataclasses import asdict
from typing import Optional, TextIO

import networkx

from wiki_categories.core.resources import ResourceConfig
from wiki_categories.core.serializable import CategoryData, CategoryTreeData, TreeEdge, SerializedCategoryTreeData


__all__ = (
    "CategoryTree",
)


class CategoryTree(networkx.DiGraph):

    def dict(self) -> dict:
        """
        Convert this CategoryTree object to a plain dict.

        :return: The deserialized dict.
        """
        return self.to_data().dict()

    @classmethod
    def from_dict(cls, d: SerializedCategoryTreeData) -> CategoryTree:
        """
        Creates a CategoryTree from a plain dict.

        :param d: The dict object to be used for creation.
        :return: Created CategoryTree object.
        """
        return cls.from_data(CategoryTreeData.from_dict(d))

    @classmethod
    def from_data(cls, data: CategoryTreeData) -> CategoryTree:
        """
        Create a CategoryTree from a CategoryTreeData object.

        :param data: The incoming CategoryTreeData object.
        :return: Created CategoryTree object.
        """

        this_graph: CategoryTree = cls([(t.child_id, t.parent_id) for t in data.edges])

        for d in data.categories:
            this_graph.add_node(d.category_id, **asdict(d))

        return this_graph

    def to_data(self) -> CategoryTreeData:
        """
        Convert this CategoryTree object to a CategoryTreeData object.

        :return: Converted CategoryTreeData.
        """

        categories = [
            CategoryData(**self.nodes[n]) for n in self.nodes
        ]

        edges = [TreeEdge(*x) for x in self.edges]

        return CategoryTreeData(categories, edges)

    @classmethod
    def for_langauge(
            cls,
            language: str,
            resource_config: Optional[ResourceConfig] = None) -> CategoryTree:
        """
        Create a CategoryTree object from a given language descriptor.

        :param language: Language descriptor ('en', 'de', etc.).
        :param resource_config: A config that allows you to modify parameters for fetching resources.
        :return: Created CategoryTree object.
        """

        return cls.from_data(
            CategoryTreeData.for_language(
                language,
                resource_config
            )
        )

    @classmethod
    def load(cls, fp: TextIO) -> CategoryTree:
        """
        Create a CategoryTree object from a readable file wrapper.

        :param fp: The JSON-serialized CategoryTreeData file wrapper to read from.
        :return: Created CategoryTree object.
        """
        return cls.from_data(CategoryTreeData.from_dict(json.load(fp)))

    def dump(self, fp: TextIO) -> None:
        """
        Write this CategoryTree object to a file wrapper.

        :param fp: The JSON-serialized CategoryTreeData file wrapper to write to.
        :return:
        """
        json.dump(self.dict(), fp, ensure_ascii=False, indent=1)
