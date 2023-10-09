"""
Contains logic for extracting external resources from a Wikipedia Data Dump.
"""

from __future__ import annotations

import abc
import ast
import dataclasses
import re
import urllib.parse
import zlib
from typing import Optional, Generator, Any, List, Iterable

from requests import Session

from wiki_categories.core.resources.config import ResourceConfig
from wiki_categories.core.resources.progress_managers import ProgressManager, NoopProgressManager, TqdmProgressManager


__all__ = (
    "get_category_table_resource_data",
    "get_category_links_resource_data",
    "get_page_table_resource_data",
    "ProgressManager",
    "NoopProgressManager",
    "TqdmProgressManager",
    "CategoryTableData",
    "CategoryLinksData",
    "PageTableData",
    "ResourceConfig"
)


def get_category_table_resource_data(
        language: str,
        resource_config: Optional[ResourceConfig]) -> CategoryTableData:
    resource_config = ResourceConfig() if resource_config is None else resource_config
    return CategoryTableData.for_language(language, resource_config)


def get_category_links_resource_data(
        language: str,
        resource_config: Optional[ResourceConfig]) -> CategoryLinksData:
    resource_config = ResourceConfig() if resource_config is None else resource_config
    return CategoryLinksData.for_language(language, resource_config)


def get_page_table_resource_data(
        language: str,
        resource_config: Optional[ResourceConfig]) -> PageTableData:
    resource_config = ResourceConfig() if resource_config is None else resource_config
    return PageTableData.for_language(language, resource_config)


class Resource(abc.ABC):
    """
    An abstract class that defines expected functionality for streaming a resource.
    """

    @abc.abstractmethod
    def stream_lines(self) -> Generator[bytes, None, None]:
        """
        Is intended to be used to generate buffered lines of a resource.
        See GzipResource for implementation.
        """
        ...


class GzipResource(Resource):
    """
    Used to stream a gzip-compressed resource.
    """

    url: str
    session: Session
    progress_manager: ProgressManager

    def __init__(self, url: str, session: Session, progress_manager: ProgressManager):
        self.url = url
        self.session = session
        self.progress_manager = progress_manager

    def stream_lines(self) -> Generator[bytes, None, None]:
        """
        Streams bytes of a resource, split on "\\n".

        :return:  The generator that yields lines of the resource.
        """

        response = self.session.get(self.url, stream=True)

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


class ResourceData:
    """
    Defines logic for processing an external resource, line by line.
    """

    resource: Resource

    def __init__(self, resource: Resource):
        self.resource = resource

    @abc.abstractmethod
    def process_line(self, line: bytes) -> Iterable[Any]:
        """
        Is called on every line of an external resource.
        :param line: Line of resource text.
        :return: Extracted data from line.
        """
        ...

    def process(self) -> List[Any]:
        """
        Processes entire resource, calling "process_line" on each streamed line.
        :return: Extracted data from entire resource.
        """

        accumulated = []

        for line in self.resource.stream_lines():
            accumulated.extend(self.process_line(line))

        return accumulated


@dataclasses.dataclass
class CategoryTableEntry:
    """
    Entries for the category table. From this resource, a category's name,
    number of pages, and number of subcategories can be extracted.
    """

    name: str
    pages: int
    subcategories: int


class CategoryTableData(ResourceData):

    @classmethod
    def for_language(
            cls,
            language: str,
            resource_config: ResourceConfig
    ):
        wiki_dump = resource_config.wiki_dump
        progress_manager = resource_config.progress_manager
        session = resource_config.session

        url = urllib.parse.urljoin(
            wiki_dump.mirror.index_location,
            wiki_dump[f"{language}wiki", "categorytable"].get_file(
                re.compile(r"category\.sql\.gz$")).url)

        return cls(GzipResource(url, session, progress_manager))

    _parse_re = re.compile(rb"\(\d+,('(?:[^']|\\')*'),(\d+),(\d+),\d+\)")

    def process_line(self, line: bytes) -> List[CategoryTableEntry]:
        hits = self._parse_re.findall(line)
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

    def process(self) -> List[CategoryTableEntry]:
        return super(CategoryTableData, self).process()


@dataclasses.dataclass
class CategoryLinksEntry:
    """
    Category links between parent and child categories. Note: only the child id is
    found, parent name maps to parent's id through the collection of the page table.
    """

    child_id: int
    parent_name: str


class CategoryLinksData(ResourceData):

    @classmethod
    def for_language(
            cls,
            language: str,
            resource_config: ResourceConfig
    ):
        wiki_dump = resource_config.wiki_dump
        progress_manager = resource_config.progress_manager
        session = resource_config.session

        url = urllib.parse.urljoin(
            wiki_dump.mirror.index_location,
            wiki_dump[f"{language}wiki", "categorylinkstable"].get_file(
                re.compile(r"categorylinks\.sql\.gz$")).url)

        return cls(GzipResource(url, session, progress_manager))

    _parse_re = re.compile(rb"\((\d+),('(?:[^']|\\')*'),(?:'(?:[^']|\\')*',){4}'subcat'\)")

    def process_line(self, line: bytes) -> List[CategoryLinksEntry]:
        hits = self._parse_re.findall(line)
        parsed = []

        for _id, _name in hits:
            _id = int(_id)
            _name = ast.literal_eval(_name.decode())
            parsed.append(CategoryLinksEntry(_id, _name))

        return parsed

    def process(self) -> List[CategoryLinksEntry]:
        return super(CategoryLinksData, self).process()


@dataclasses.dataclass
class PageTableEntry:
    """
    Page table entries. Maps page ids to category names.
    """

    page_id: int
    name: str


class PageTableData(ResourceData):

    @classmethod
    def for_language(
            cls,
            language: str,
            resource_config: ResourceConfig
    ):
        wiki_dump = resource_config.wiki_dump
        progress_manager = resource_config.progress_manager
        session = resource_config.session

        url = urllib.parse.urljoin(
            wiki_dump.mirror.index_location,
            wiki_dump[f"{language}wiki", "pagetable"].get_file(
                re.compile(r"page\.sql\.gz$")).url)

        return cls(GzipResource(url, session, progress_manager))

    _parse_re = re.compile(rb"\((\d+),14,('(?:[^']|\\')*'),")

    def process_line(self, line: bytes) -> List[PageTableEntry]:
        hits = self._parse_re.findall(line)
        parsed = []

        for _id, _name in hits:
            _id = int(_id)
            _name = ast.literal_eval(_name.decode())
            parsed.append(PageTableEntry(_id, _name))

        return parsed

    def process(self) -> List[PageTableEntry]:
        return super(PageTableData, self).process()
