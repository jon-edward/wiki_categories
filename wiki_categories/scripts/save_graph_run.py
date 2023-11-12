import datetime
import gzip
import json
import pathlib
import time
from typing import Collection, Tuple

import networkx as nx
import wiki_data_dump.mirrors
from wiki_data_dump.mirrors import MirrorType

from wiki_categories.core import CategoryTree, Assets
from wiki_categories.core.category_tree import less_than_page_count_percentile
from wiki_categories.core.wiki_utils import id_for_category_str_by_lang, CategoryNotFound


def _split_lines(text: str) -> Tuple[str, ...]:
    return tuple(x.strip() for x in text.splitlines() if x.strip())


default_languages = _split_lines("""
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
   Category:All redirect categories
""")


def save_graph_run(
        src_tree: CategoryTree,
        save_dir: pathlib.Path,
        root_id: int,
        lang: str,
        excluded_branches: Collection[str],
        page_percentile: int,
        max_depth: int,
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

    reachable = nx.dfs_tree(src_tree, source=root_id, depth_limit=max_depth)
    src_tree.remove_nodes_from([x for x in src_tree if x not in reachable])

    to_remove = less_than_page_count_percentile(src_tree, page_percentile)

    for n in to_remove:
        if n == root_id:
            continue
        src_tree.remove_node_reconstruct(n)

    categories_df, edges_df = src_tree.to_dataframes()

    with gzip.open(save_dir.joinpath("categories.csv.gz"), "w") as f:
        categories_df.to_csv(f)

    with gzip.open(save_dir.joinpath("edges.csv.gz"), "w") as f:
        edges_df.to_csv(f)


def process_language(lang: str, save_dir: pathlib.Path):
    started = time.time()
    assets = Assets(lang, wiki_dump=wiki_data_dump.WikiDump(mirror=MirrorType.WIKIMEDIA))

    page_table_updated = assets.page_table_job.updated
    category_links_updated = assets.category_links_job.updated
    category_table_updated = assets.category_table_job.updated

    page_percentile = 70
    max_depth = 100

    if save_dir.joinpath("meta.json").exists():
        try:
            with open(save_dir.joinpath("meta.json"), 'r', encoding="utf-8") as f:
                meta_json = json.load(f)

            assert meta_json["page_table_updated"] == page_table_updated
            assert meta_json["category_links_updated"] == category_links_updated
            assert meta_json["category_table_updated"] == category_table_updated
            assert meta_json["page_percentile"] == page_percentile
            assert meta_json["max_depth"] == max_depth

            return
            #  Skip run
        except KeyError:
            pass
        except AssertionError:
            pass
        except json.JSONDecodeError:
            pass

    save_graph_run(
        CategoryTree(assets),
        save_dir,
        root_id=id_for_category_str_by_lang(lang, "Category:Contents", "en"),
        lang=lang,
        excluded_branches=_preferred_excluded_parents,
        page_percentile=page_percentile,
        max_depth=max_depth,
        mutate_src=True
    )

    with open(save_dir.joinpath("meta.json"), 'w', encoding="utf-8") as f:
        json.dump({
            "page_table_updated": page_table_updated,
            "category_links_updated": category_links_updated,
            "category_table_updated": category_table_updated,
            "page_percentile": page_percentile,
            "max_depth": max_depth,
            "run_duration_seconds": int(time.time() - started),
            "finished": datetime.datetime.now().isoformat()
        }, f)
