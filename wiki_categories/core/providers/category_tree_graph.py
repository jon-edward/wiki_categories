import networkx as nx
import requests

from .category_tree_data import CategoryTreeData
from .resources import ProgressManager

import wiki_data_dump as wdd


class CategoryTreeGraph:
    graph: nx.DiGraph
    _data: CategoryTreeData

    def __init__(self, data: CategoryTreeData):
        self._data = data

        self.graph = nx.DiGraph()

        for _id, name in data.id_to_name.items():
            self.graph.add_node(_id, name=name, pages=data.id_to_page_count[_id])

        self.graph.add_edges_from(data.edges)

    @property
    def data(self):
        return self._data

    @classmethod
    def from_language(
            cls,
            language: str,
            wiki_dump: wdd.WikiDump,
            session: requests.Session,
            progress_manager: ProgressManager
    ):

        graph = CategoryTreeGraph(
            CategoryTreeData.from_language(
                language,
                wiki_dump,
                session,
                progress_manager
            )
        )

        return graph


