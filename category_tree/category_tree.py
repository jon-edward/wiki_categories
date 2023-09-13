import logging
import statistics
from typing import Set, Optional

import networkx as nx

from category_tree.generate.category_tree_data import CategoryTreeData
from category_tree.wiki_utils.hidden_category_id import hidden_category_id
from category_tree.wiki_utils.main_topic_classifications import main_topic_classifications


_ROOT_ID = 0
_ROOT_NAME = "__root__"


class CategoryTree:
    graph: nx.DiGraph
    data: CategoryTreeData

    def __init__(self, from_data: CategoryTreeData):
        self.graph = nx.DiGraph()
        self.graph.add_edges_from(from_data.edges)
        self.data = from_data

        logging.info(f"[{self.data.language}] Initial category tree has {len(self.graph)} categories.")

    def add_root(self):
        main_topics = main_topic_classifications(self.data.language)
        self.graph.add_edges_from((_ROOT_ID, x) for x in main_topics)

    def trim_hidden(self):
        hidden_category = hidden_category_id(self.data.language)
        all_hidden = tuple(x for x in self.graph.neighbors(hidden_category))

        if all_hidden:
            num_excluded = len(all_hidden)
            logging.info(f"[{self.data.language}] Excluding {num_excluded} "
                         f"hidden categor{'y' if num_excluded == 1 else 'ies'}, ")

        self.graph.remove_nodes_from(all_hidden)

    @property
    def protected_categories(self) -> Set[int]:
        return {x for x in (_ROOT_ID,) + tuple(self.graph.neighbors(_ROOT_ID))}

    def trim_by_page_count_percentile(self, percentile: int):
        protected = self.protected_categories

        dataset = tuple(x for x in self.data.id_to_page_count.values())

        cutoff = max(int(statistics.quantiles(dataset, n=100)[percentile]), 1)

        exclude = tuple(
            x for x in self.graph.nodes if
            x not in protected and
            self.data.id_to_page_count.get(x, 0) < cutoff)

        if exclude:
            num_excluded = len(exclude)
            logging.info(f"[{self.data.language}] Excluding {num_excluded} "
                         f"categor{'y' if num_excluded == 1 else 'ies'}, "
                         f"they have less than {cutoff} page{'' if cutoff == 1 else 's'}.")

        self.graph.remove_nodes_from(exclude)

    def trim_by_max_depth(self, max_depth: Optional[int]):
        short_graph = nx.dfs_tree(self.graph, source=_ROOT_ID, depth_limit=max_depth)

        exclude = tuple(x for x in self.graph if x not in short_graph)

        if exclude:
            num_excluded = len(exclude)
            logging.info(f"[{self.data.language}] Excluding {num_excluded} "
                         f"categor{'y' if num_excluded == 1 else 'ies'}, "
                         f"they are at depth greater than {max_depth if max_depth is not None else 'infinity'}.")

        self.graph.remove_nodes_from(exclude)

    def trim_by_id_without_name(self):
        exclude = tuple(
            x for x in self.graph.nodes if x != _ROOT_ID and x not in self.data.id_to_name)

        if exclude:
            num_excluded = len(exclude)
            logging.info(f"[{self.data.language}] Excluding {num_excluded} "
                         f"categor{'y' if num_excluded == 1 else 'ies'} "
                         "without a found name.")

        self.graph.remove_nodes_from(exclude)

    def to_dict(self):
        category_dict = {}

        undirected_graph = nx.Graph(self.graph)

        for node in self.graph.nodes:
            all_neighbors = tuple(undirected_graph.neighbors(node))
            children = {x for x in all_neighbors if self.graph.has_edge(node, x)}

            category_dict[node] = {
                "name": _ROOT_NAME if node == _ROOT_ID else self.data.id_to_name[node],
                "parents": [x for x in all_neighbors if x not in children],
                "children": list(children)
            }

        return {"language": self.data.language, "categories": category_dict}
