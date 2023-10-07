import json
import pathlib

from ..providers import CategoryTreeGraph


def serialize(category_tree: CategoryTreeGraph, to_file: pathlib.Path):
    data = category_tree.data

    id_to_name = {
        node: data.id_to_name[node] for node in category_tree.graph
    }

    id_to_page_count = {
        node: data.id_to_page_count[node] for node in category_tree.graph
    }

    edges = [e for e in category_tree.graph.edges]

    with open(to_file, 'w', encoding='utf-8') as f:
        json.dump({
            "id_to_name": id_to_name,
            "id_to_page_count": id_to_page_count,
            "edges": edges
        }, f, ensure_ascii=False, indent=1)

