import gzip
import pathlib
from typing import Collection, Tuple

import networkx as nx
import pandas as pd
from wiki_data_dump import WikiDump
from wiki_data_dump.mirrors import MirrorType

from wiki_categories.core import CategoryTree
from wiki_categories.core.category_tree import less_than_page_count_percentile
from wiki_categories.core.wiki_utils import id_for_category_str_by_lang, CategoryNotFound


def _split_lines(text: str) -> Tuple[str, ...]:
    return tuple(x.strip() for x in text.splitlines() if x.strip())


_default_languages = _split_lines("""
    en
    ceb
    de
    sv
    fr
    nl
    ru
    es
    it
    arz
    pl
    ja
    zh
    vi
    uk
    ar
    pt
    fa
    ca
    sr
    ko
    no
    ce
    fi
    tr
    hu
    cs
    tt
    sh
    ro
    eu
    ms
    eo
""")

_preferred_excluded_parents = _split_lines("""
   Category:Hidden categories
   Category:Tracking categories
   Category:Container categories
   Category:Noindexed pages
   Category:Wikipedia 1.0 assessments
   Category:Wikipedia administration
   Category:Articles by importance
   Category:Articles by quality
   Category:Wikipedia categories
   Category:Stub categories
   Category:WikiProject templates
""")


def save_graph_run(
        src_tree: CategoryTree,
        save_dir: pathlib.Path,
        lang: str,
        excluded_branches: Collection[str],
        mutate_src: bool = True):

    if not mutate_src:
        src_tree = src_tree.copy()
        #  Shallow copy is sufficient. Node attributes may be shared.

    total_excluded = set()

    for excluded in excluded_branches:
        try:
            excluded_id = id_for_category_str_by_lang(lang, excluded, "en")
        except CategoryNotFound:
            continue

        total_excluded.update(src_tree.successors(excluded_id))
        total_excluded.add(excluded_id)

    src_tree.remove_nodes_from(total_excluded)

    reachable = nx.dfs_tree(src_tree)
    src_tree.remove_nodes_from([x for x in src_tree if x not in reachable])

    to_remove = less_than_page_count_percentile(src_tree, 65)

    for n in to_remove:
        src_tree.remove_node_reconstruct(n)

    categories_df, edges_df = src_tree.to_dataframes()

    with gzip.open(save_dir.joinpath("categories.csv.gz"), "w") as f:
        categories_df.to_csv(f)

    with gzip.open(save_dir.joinpath("edges.csv.gz"), "w") as f:
        edges_df.to_csv(f)



if __name__ == '__main__':
    # _src_tree = CategoryTree(Assets("en", wiki_dump=WikiDump(mirror=MirrorType.WIKIMEDIA)))

    # with open("./../../_data/en/category_tree.full.json", 'r', encoding="utf-8") as f:
    #     cat_df, edges_df = _src_tree.to_dataframes()
    #
    #     cat_df.to_csv("./../../_data/en/categories.csv")
    #     edges_df.to_csv("./../../_data/en/edges.csv")

    _src_tree = CategoryTree((pd.read_csv("./../../_data/en/categories.csv"),
                              pd.read_csv("./../../_data/en/edges.csv")))

    print(_src_tree)
    print(CategoryTree(_src_tree.to_dataframes()))

    print(nx.utils.graphs_equal(CategoryTree(_src_tree.to_dataframes()), _src_tree))

    # save_trimmed(_src_tree, pathlib.Path("./../../_data/en"), "en", _preferred_excluded_parents)
