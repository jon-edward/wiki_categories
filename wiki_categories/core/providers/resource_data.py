"""
Contains logic for processing resources. Namely, category, category-link, and page tables.
"""

import abc
import ast
import dataclasses
import re
import urllib.parse
from typing import Any, List

import requests
import wiki_data_dump as wdd

from .resources import Resource, ProgressManager, GzipResource


class ResourceData:
    resource: Resource

    def __init__(self, resource: Resource):
        self.resource = resource

    @abc.abstractmethod
    def process_line(self, line: bytes):
        ...

    def process(self) -> List[Any]:
        accumulated = []

        for line in self.resource.stream_lines():
            accumulated.extend(self.process_line(line))

        return accumulated


@dataclasses.dataclass
class Category:
    name: str
    pages: int
    subcategories: int


class CategoryData(ResourceData):

    @classmethod
    def from_language_dump(
            cls,
            language: str,
            wiki_dump: wdd.WikiDump,
            session: requests.Session,
            progress_manager: ProgressManager
    ):
        url = urllib.parse.urljoin(
            wiki_dump.mirror.index_location,
            wiki_dump[f"{language}wiki", "categorytable"].get_file(
                re.compile(r"category\.sql\.gz$")).url)

        return cls(GzipResource(url, session, progress_manager))

    _parse_re = re.compile(rb"\(\d+,('(?:[^']|\\')*'),(\d+),(\d+),\d+\)")

    def process_line(self, line: bytes) -> List[Category]:
        hits = self._parse_re.findall(line)
        parsed = []

        for _name, _pages, _subcategories in hits:
            try:
                _name = ast.literal_eval(_name.decode())
            except UnicodeDecodeError:
                _name = ast.literal_eval(_name.decode(encoding="latin"))

            _pages = int(_pages)
            _subcategories = int(_subcategories)

            parsed.append(Category(_name, _pages, _subcategories))

        return parsed

    def process(self) -> List[Category]:
        return super(CategoryData, self).process()


@dataclasses.dataclass
class CategoryLink:
    child_id: int
    parent_name: str


class CategoryLinkData(ResourceData):

    @classmethod
    def from_language_dump(
            cls,
            language: str,
            wiki_dump: wdd.WikiDump,
            session: requests.Session,
            progress_manager: ProgressManager
    ):
        url = urllib.parse.urljoin(
            wiki_dump.mirror.index_location,
            wiki_dump[f"{language}wiki", "categorylinkstable"].get_file(
                re.compile(r"categorylinks\.sql\.gz$")).url)

        return cls(GzipResource(url, session, progress_manager))

    _parse_re = re.compile(rb"\((\d+),('(?:[^']|\\')*'),(?:'(?:[^']|\\')*',){4}'subcat'\)")
    
    def process_line(self, line: bytes) -> List[CategoryLink]:
        hits = self._parse_re.findall(line)
        parsed = []

        for _id, _name in hits:
            _id = int(_id)
            _name = ast.literal_eval(_name.decode())
            parsed.append(CategoryLink(_id, _name))

        return parsed
    
    def process(self) -> List[CategoryLink]:
        return super(CategoryLinkData, self).process()


@dataclasses.dataclass
class PageTable:
    page_id: int
    name: str


class PageTableData(ResourceData):

    @classmethod
    def from_language_dump(
            cls,
            language: str,
            wiki_dump: wdd.WikiDump,
            session: requests.Session,
            progress_manager: ProgressManager
    ):
        url = urllib.parse.urljoin(
            wiki_dump.mirror.index_location,
            wiki_dump[f"{language}wiki", "pagetable"].get_file(
                re.compile(r"page\.sql\.gz$")).url)

        return cls(GzipResource(url, session, progress_manager))

    _parse_re = re.compile(rb"\((\d+),14,('(?:[^']|\\')*'),")

    def process_line(self, line: bytes) -> List[PageTable]:
        hits = self._parse_re.findall(line)
        parsed = []

        for _id, _name in hits:
            _id = int(_id)
            _name = ast.literal_eval(_name.decode())
            parsed.append(PageTable(_id, _name))

        return parsed

    def process(self) -> List[PageTable]:
        return super(PageTableData, self).process()
