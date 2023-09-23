import datetime
import gzip
import hashlib
import json
import os.path
import pathlib
from typing import Optional

import wiki_data_dump.mirrors

from category_tree.category_tree import CategoryTree
from category_tree.deserialize import deserialize
from category_tree.generate.fetch_category_tree_data import fetch_category_tree_data
from category_tree.serialize import serialize

DEFAULT_DATA_DIR = (
    pathlib.Path(__file__).parent.parent.parent.joinpath("_data").absolute()
)


class DataDirPathProvider:
    @staticmethod
    def raw_category_tree_name(language: str):
        return f"{language}_category_tree.full.json"

    @staticmethod
    def trimmed_category_tree_name(language: str):
        return f"{language}_category_tree.trimmed.json"

    @staticmethod
    def compressed_category_tree_name(language: str):
        return f"{language}_category_tree.full.json.gz"

    @staticmethod
    def compressed_trimmed_category_tree_name(language: str):
        return f"{language}_category_tree.trimmed.json.gz"

    @staticmethod
    def meta_file_name():
        return "meta.json"


def _attempt_unlink(path: pathlib.Path):
    try:
        os.unlink(path)
    except FileNotFoundError:
        pass


class DataDir:
    """
    Specifies default behavior for interacting with the data directory.
    """

    language: str
    root_path: pathlib.Path
    path_provider: DataDirPathProvider

    def __init__(
        self,
        language: str,
        *,
        root_path: Optional[pathlib.Path] = None,
        path_provider: Optional[DataDirPathProvider] = None,
    ):
        self.language = language

        if root_path is None:
            self.root_path = DEFAULT_DATA_DIR
        else:
            self.root_path = root_path

        if path_provider is None:
            self.path_provider = DataDirPathProvider()
        else:
            self.path_provider = path_provider

    @property
    def _required_paths(self):
        return (
            self.raw_category_tree_path,
            self.trimmed_category_tree_path,
            self.meta_file_path,
            self.compressed_trimmed_category_tree_path,
            self.compressed_category_tree_path
        )

    def _ensure_dirs_exists(self):
        required_dirs = (
            x.parent
            for x in self._required_paths
        )

        for path in required_dirs:
            if not os.path.exists(path):
                os.mkdir(path)

    @property
    def lang_dir_root(self):
        return self.root_path.joinpath(self.language)

    @property
    def raw_category_tree_path(self):
        raw_category_tree_name = self.path_provider.raw_category_tree_name(
            self.language
        )
        return self.lang_dir_root.joinpath(raw_category_tree_name)

    @property
    def trimmed_category_tree_path(self):
        trimmed_category_tree_name = self.path_provider.trimmed_category_tree_name(
            self.language
        )
        return self.lang_dir_root.joinpath(trimmed_category_tree_name)

    @property
    def compressed_category_tree_path(self):
        compressed_category_tree_name = (
            self.path_provider.compressed_category_tree_name(self.language)
        )
        return self.lang_dir_root.joinpath(compressed_category_tree_name)

    @property
    def compressed_trimmed_category_tree_path(self):
        compressed_trimmed_category_tree_name = (
            self.path_provider.compressed_trimmed_category_tree_name(self.language)
        )
        return self.lang_dir_root.joinpath(compressed_trimmed_category_tree_name)

    @property
    def meta_file_path(self):
        return self.lang_dir_root.joinpath(self.path_provider.meta_file_name())

    def save_raw_category_tree(self, data_dump: wiki_data_dump.WikiDump = None):
        self._ensure_dirs_exists()
        category_tree_data = fetch_category_tree_data(self.language, data_dump=data_dump)
        serialize(category_tree_data, self.raw_category_tree_path)

    def save_trimmed_category_tree(
            self,
            pages_percentile: int,
            max_depth: Optional[int],
            keep_hidden: bool = False,
            data_dump: wiki_data_dump.WikiDump = None):

        self._ensure_dirs_exists()

        if not self.raw_category_tree_path.exists():
            self.save_raw_category_tree(data_dump=data_dump)

        raw_tree_data = deserialize(self.raw_category_tree_path)
        cat_tree = CategoryTree(raw_tree_data)

        cat_tree.add_root()

        if not keep_hidden:
            cat_tree.trim_hidden()

        cat_tree.trim_by_page_count_percentile(pages_percentile)
        cat_tree.trim_by_id_without_name()
        cat_tree.trim_by_max_depth(max_depth)

        with open(self.trimmed_category_tree_path, "wb") as f:
            content = json.dumps(cat_tree.to_dict(), ensure_ascii=False, indent=1)
            f.write(content.encode("utf-8"))

    def save_compressed_category_tree(self):
        self._ensure_dirs_exists()

        if not self.raw_category_tree_path.exists():
            self.save_raw_category_tree()

        with gzip.open(self.compressed_category_tree_path, "w") as f_out, open(
            self.raw_category_tree_path, "rb"
        ) as f_in:
            f_out.write(f_in.read())

    def save_compressed_trimmed_category_tree(self):
        self._ensure_dirs_exists()

        if not self.trimmed_category_tree_path:
            raise Exception(
                "Must first generate trimmed category tree with "
                "'save_trimmed_category_tree'."
            )

        with gzip.open(self.compressed_trimmed_category_tree_path, "w") as f_out, open(
            self.trimmed_category_tree_path, "rb"
        ) as f_in:
            f_out.write(f_in.read())

    def save_meta_file(self, extra_meta: dict = None):
        self._ensure_dirs_exists()

        meta_dict = deserialize(self.raw_category_tree_path).to_dict()["meta"]

        meta_dict["full_category_tree"] = {}
        meta_dict["trimmed_category_tree"] = {}

        with open(self.raw_category_tree_path, "rb") as f:
            sha256hash = hashlib.sha256(f.read()).hexdigest()
            uncompressed_size_in_bytes = f.tell()
            full_meta = meta_dict["full_category_tree"]
            full_meta["sha256"] = sha256hash
            full_meta["uncompressed_size"] = uncompressed_size_in_bytes

        with open(self.trimmed_category_tree_path, "rb") as f:
            sha256hash = hashlib.sha256(f.read()).hexdigest()
            uncompressed_size_in_bytes = f.tell()
            trimmed_meta = meta_dict["trimmed_category_tree"]
            trimmed_meta["sha256"] = sha256hash
            trimmed_meta["uncompressed_size"] = uncompressed_size_in_bytes

        meta_dict["updated"] = datetime.datetime.now().isoformat()

        if extra_meta:
            meta_dict.update(extra_meta)

        with open(self.meta_file_path, "w") as f_out:
            json.dump(meta_dict, f_out, indent=1)

    def clear_files(self):
        for path in self._required_paths:
            _attempt_unlink(path)
