from typing import List

import networkx

from wiki_categories.core.category_tree import CategoryTree
from wiki_categories.core.wiki_utils import hidden_category_id, contents_category_id

__all__ = (
    "remove_by_hidden",
    "remove_by_connected_to_root"
)


def remove_by_hidden(language: str, cat_tree: CategoryTree) -> List[int]:
    """
    Remove all children of the "Category:Hidden categories" category.

    :param language: Language descriptor ('en', 'de', etc.).
    :param cat_tree: Tree to be modified in-place.
    :return: A list of removed category ids.
    """

    hidden_id = hidden_category_id(language)

    hidden_cats = list(x for x in cat_tree[hidden_id].keys())
    cat_tree.remove_nodes_from(hidden_cats)

    return hidden_cats


def remove_by_connected_to_root(language: str, cat_tree: CategoryTree) -> List[int]:
    """
    Remove all categories that cannot be reachable by any path from the language's
    equivalent of "Category:Contents" in the English Wikipedia - this acts as the root node
    of the category tree.

    :param language: Language descriptor ('en', 'de', etc.).
    :param cat_tree: Tree to modified in-place.
    :return: A list of removed category ids.
    """

    contents_id = contents_category_id(language)

    root_connected_tree = networkx.dfs_tree(cat_tree, source=contents_id)
    root_disconnected = [x for x in cat_tree.nodes if x not in root_connected_tree]

    cat_tree.remove_nodes_from(root_disconnected)

    return root_disconnected
