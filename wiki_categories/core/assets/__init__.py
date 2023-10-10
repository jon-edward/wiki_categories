import ast
import re
import urllib.parse
import zlib
from typing import Optional, Generator, NamedTuple

import requests
import wiki_data_dump as wdd

from wiki_categories.core.assets.progress_managers import ProgressManager, TqdmProgressManager, NoopProgressManager


__all__ = (
    "CategoryTableEntry",
    "CategoryLinksEntry",
    "PageTableEntry",
    "Assets",
    "ProgressManager",
    "TqdmProgressManager",
    "NoopProgressManager"
)


class CategoryTableEntry(NamedTuple):
    name: str
    pages: int
    subcategories: int


class CategoryLinksEntry(NamedTuple):
    child_id: int
    parent_name: str


class PageTableEntry(NamedTuple):
    page_id: int
    name: str


class Assets:

    language: str
    wiki_dump: wdd.WikiDump
    session: requests.Session
    progress_manager: ProgressManager

    def __init__(
            self,
            language: str,
            wiki_dump: Optional[wdd.WikiDump] = None,
            session: Optional[requests.Session] = None,
            progress_manager: Optional[ProgressManager] = None
    ):
        self.language = language
        self.wiki_dump = wdd.WikiDump() if wiki_dump is None else wiki_dump
        self.session = requests.Session() if session is None else session
        self.progress_manager = TqdmProgressManager() if progress_manager is None else progress_manager

    def _stream_decompressed_lines(self, url: str) -> Generator[bytes, None, None]:
        """
        Streams bytes of a resource, split on "\\n".

        :return:  The generator that yields lines of the resource.
        """

        response = self.session.get(url, stream=True)

        size: int = int(response.headers["Content-Length"])
        self.progress_manager.start(size)

        decompress_obj = zlib.decompressobj(16 + zlib.MAX_WBITS)
        content = response.iter_content(chunk_size=1024)

        buffer = b""

        for c in content:
            self.progress_manager.update(len(c))

            buffer += decompress_obj.decompress(c)

            try:
                split_at = buffer.index(b"\n")
                yield buffer[:split_at]
                buffer = buffer[split_at+1:]

            except ValueError:
                continue

        for tail_line in buffer.split(b"\n"):
            yield tail_line

        self.progress_manager.close()

    @property
    def category_table_job(self) -> wdd.Job:
        return self.wiki_dump[f"{self.language}wiki", "categorytable"]

    @property
    def category_links_job(self) -> wdd.Job:
        return self.wiki_dump[f"{self.language}wiki", "categorylinkstable"]

    @property
    def page_table_job(self) -> wdd.Job:
        return self.wiki_dump[f"{self.language}wiki", "pagetable"]

    @property
    def category_table_url(self) -> str:
        return urllib.parse.urljoin(
            self.wiki_dump.mirror.index_location,
            self.category_table_job.get_file(
                re.compile(r"category\.sql\.gz$")).url)

    @property
    def category_links_url(self) -> str:
        return urllib.parse.urljoin(
            self.wiki_dump.mirror.index_location,
            self.category_links_job.get_file(
                re.compile(r"categorylinks\.sql\.gz$")).url)

    @property
    def page_table_url(self) -> str:
        return urllib.parse.urljoin(
            self.wiki_dump.mirror.index_location,
            self.page_table_job.get_file(
                re.compile(r"page\.sql\.gz$")).url)

    def category_table_entries(self) -> Generator[CategoryTableEntry, None, None]:
        parse_re = re.compile(rb"\(\d+,('(?:[^']|\\')*'),(\d+),(\d+),\d+\)")

        def _process_line(line: bytes):
            hits = parse_re.findall(line)
            parsed = []

            for _name, _pages, _subcategories in hits:
                try:
                    _name = ast.literal_eval(_name.decode())
                except UnicodeDecodeError:
                    _name = ast.literal_eval(_name.decode(encoding="latin"))

                _pages = int(_pages)
                _subcategories = int(_subcategories)

                parsed.append(CategoryTableEntry(_name, _pages, _subcategories))

            return parsed

        for _line in self._stream_decompressed_lines(self.category_table_url):
            for hit in _process_line(_line):
                yield hit

    def category_links_entries(self) -> Generator[CategoryLinksEntry, None, None]:
        parse_re = re.compile(rb"\((\d+),('(?:[^']|\\')*'),(?:'(?:[^']|\\')*',){4}'subcat'\)")

        def _process_line(line: bytes):
            hits = parse_re.findall(line)
            parsed = []

            for _id, _name in hits:
                _id = int(_id)
                _name = ast.literal_eval(_name.decode())
                parsed.append(CategoryLinksEntry(_id, _name))

            return parsed

        for _line in self._stream_decompressed_lines(self.category_links_url):
            for hit in _process_line(_line):
                yield hit

    def page_table_entries(self) -> Generator[PageTableEntry, None, None]:
        parse_re = re.compile(rb"\((\d+),14,('(?:[^']|\\')*'),")

        def _process_line(line: bytes):
            hits = parse_re.findall(line)
            parsed = []

            for _id, _name in hits:
                _id = int(_id)
                _name = ast.literal_eval(_name.decode())
                parsed.append(PageTableEntry(_id, _name))

            return parsed

        for _line in self._stream_decompressed_lines(self.page_table_url):
            for hit in _process_line(_line):
                yield hit
