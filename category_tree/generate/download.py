import datetime
import re
import urllib.parse
from typing import Tuple, Iterable
import zlib

import requests
import wiki_data_dump as wdd


class DownloadData:
    updated_date: datetime.date
    lines: Iterable[bytes]

    def __init__(self, updated_str_time: str, lines: Iterable[bytes]):
        self.updated_date = datetime.datetime.fromisoformat(updated_str_time).date()
        self.lines = lines


def stream_lines(url: str, session: requests.Session) -> Iterable[bytes]:
    buffer = b""

    response = session.get(url, stream=True)
    decompress_obj = zlib.decompressobj(16 + zlib.MAX_WBITS)
    content = response.iter_content(chunk_size=1024)

    for c in content:
        buffer += decompress_obj.decompress(c)

        try:
            split_at = buffer.index(b"\n")
            yield buffer[:split_at]
            buffer = buffer[split_at + 1 :]

        except ValueError:
            continue

    yield buffer


def job_file_for_asset(
    language: str, descriptor: str, data_dump: wdd.WikiDump
) -> Tuple[wdd.Job, wdd.File]:
    assert descriptor in ("pagetable", "category", "categorylinks")

    if descriptor == "pagetable":
        job = data_dump[f"{language}wiki", "pagetable"]
        return job, job.get_file(re.compile(r"page\.sql\.gz$"))
    if descriptor == "category":
        job = data_dump[f"{language}wiki", "categorytable"]
        return job, job.get_file(re.compile(r"category\.sql\.gz$"))
    if descriptor == "categorylinks":
        job = data_dump[f"{language}wiki", "categorylinkstable"]
        return job, job.get_file(re.compile(r"categorylinks\.sql\.gz$"))

    raise Exception("Unreachable")


def download_category_info(
    language_code: str,
    data_dump: wdd.WikiDump,
):
    job, file = job_file_for_asset(language_code, "category", data_dump)
    url = urllib.parse.urljoin(data_dump.mirror.index_location, file.url)
    return DownloadData(job.updated, stream_lines(url, data_dump.session))


def download_page_table(language_code: str, data_dump: wdd.WikiDump):
    job, file = job_file_for_asset(language_code, "pagetable", data_dump)
    url = urllib.parse.urljoin(data_dump.mirror.index_location, file.url)
    return DownloadData(job.updated, stream_lines(url, data_dump.session))


def download_category_links_table(language_code: str, data_dump: wdd.WikiDump):
    job, file = job_file_for_asset(language_code, "categorylinks", data_dump)
    url = urllib.parse.urljoin(data_dump.mirror.index_location, file.url)
    return DownloadData(job.updated, stream_lines(url, data_dump.session))
