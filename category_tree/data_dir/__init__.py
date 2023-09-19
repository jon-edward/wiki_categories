import datetime
import gzip
import hashlib
import json
import os.path
import pathlib
from typing import Optional

from category_tree.category_tree import CategoryTree
from category_tree.deserialize import deserialize
from category_tree.generate.fetch_category_tree_data import fetch_category_tree_data
from category_tree.serialize import serialize

DEFAULT_DATA_DIR = pathlib.Path(__file__).parent.parent.parent.joinpath("_data").absolute()


class DataDirPathProvider:

    @staticmethod
    def raw_category_tree_name(language: str):
        return f"{language}_category_tree.full.json"

    @staticmethod
    def trimmed_category_tree_name(language: str):
        return f"{language}_trimmed_category_tree.json"

    @staticmethod
    def compressed_category_tree_name(language: str):
        return f"{language}_category_tree.full.json.gz"

    @staticmethod
    def meta_file_name():
        return "meta.json"


class DataDir:
    """
    Specifies default behavior for interacting with the data repository.
    """

    language: str
    root_path: pathlib.Path
    path_provider: DataDirPathProvider

    def __init__(
            self,
            language: str,
            *,
            root_path: pathlib.Path = None,
            path_provider: DataDirPathProvider = None):

        self.language = language

        if root_path is None:
            self.root_path = DEFAULT_DATA_DIR
        else:
            self.root_path = root_path

        if path_provider is None:
            self.path_provider = DataDirPathProvider()
        else:
            self.path_provider = path_provider

    def _ensure_dirs_exists(self):
        required_paths = (
            x.parent for x in (
                self.raw_category_tree_path,
                self.trimmed_category_tree_path,
                self.compressed_category_tree_path,
                self.meta_file_path
            )
        )

        for path in required_paths:
            if not os.path.exists(path):
                os.mkdir(path)

    @property
    def lang_dir_root(self):
        return self.root_path.joinpath(self.language)

    @property
    def raw_category_tree_path(self):
        raw_category_tree_name = self.path_provider.raw_category_tree_name(self.language)
        return self.lang_dir_root.joinpath(raw_category_tree_name)

    @property
    def trimmed_category_tree_path(self):
        trimmed_category_tree_name = self.path_provider.trimmed_category_tree_name(self.language)
        return self.lang_dir_root.joinpath(trimmed_category_tree_name)

    @property
    def compressed_category_tree_path(self):
        compressed_category_tree_name = self.path_provider.compressed_category_tree_name(self.language)
        return self.lang_dir_root.joinpath(compressed_category_tree_name)

    @property
    def meta_file_path(self):
        return self.lang_dir_root.joinpath(self.path_provider.meta_file_name())

    def save_raw_category_tree(self):
        self._ensure_dirs_exists()

        category_tree_data = fetch_category_tree_data(self.language)
        serialize(category_tree_data, self.raw_category_tree_path)

    def save_trimmed_category_tree(self, pages_percentile: int, max_depth: Optional[int], keep_hidden: bool):
        self._ensure_dirs_exists()

        raw_tree_data = deserialize(self.raw_category_tree_path)
        cat_tree = CategoryTree(raw_tree_data)

        cat_tree.add_root()

        if not keep_hidden:
            cat_tree.trim_hidden()

        cat_tree.trim_by_page_count_percentile(pages_percentile)
        cat_tree.trim_by_id_without_name()
        cat_tree.trim_by_max_depth(max_depth)

        with open(self.trimmed_category_tree_path, 'wb') as f:
            content = json.dumps(cat_tree.to_dict(), ensure_ascii=False, indent=1)
            f.write(content.encode("utf-8"))

    def save_compressed_category_tree(self):
        self._ensure_dirs_exists()

        with gzip.open(self.compressed_category_tree_path, 'w') as f_out, \
                open(self.raw_category_tree_path, 'rb') as f_in:
            f_out.write(f_in.read())

    def save_meta_file(self):
        self._ensure_dirs_exists()

        meta_dict = deserialize(self.raw_category_tree_path).to_dict()["meta"]

        with gzip.open(self.compressed_category_tree_path, 'r') as f:
            data = f.read()
            sha256hash = hashlib.sha256(data).hexdigest()
            meta_dict["uncompressed_sha256"] = sha256hash

        meta_dict["updated"] = datetime.date.today().isoformat()

        with open(self.meta_file_path, 'w') as f_out:
            json.dump(meta_dict, f_out, indent=1)
