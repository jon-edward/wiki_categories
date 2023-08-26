import datetime
import re
from typing import Callable, Any, Optional, Tuple

import wiki_data_dump as wdd


DownloadProgressCallbackType = Optional[Callable[[int, int], Any]]


class DownloadMetaData:
    updated_date: datetime.date

    def __init__(self, updated_str_time: str):
        self.updated_date = datetime.datetime.fromisoformat(updated_str_time).date()


def job_file_for_asset(language: str, descriptor: str, data_dump: wdd.WikiDump) -> Tuple[wdd.Job, wdd.File]:
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
        to_path: str,
        language_code: str,
        data_dump: wdd.WikiDump,
        download_progress_callback: DownloadProgressCallbackType):

    job, file = job_file_for_asset(language_code, "category",  data_dump)

    data_dump.download(
        file,
        destination=to_path,
        download_progress_hook=download_progress_callback
    ).join()

    return DownloadMetaData(job.updated)


def download_page_table(
        to_path: str,
        language_code: str,
        data_dump: wdd.WikiDump,
        download_progress_callback: DownloadProgressCallbackType):

    job, file = job_file_for_asset(language_code, "pagetable",  data_dump)

    data_dump.download(
        file,
        destination=to_path,
        download_progress_hook=download_progress_callback
    ).join()

    return DownloadMetaData(job.updated)


def download_category_links_table(
        to_path: str,
        language_code: str,
        data_dump: wdd.WikiDump,
        download_progress_callback: DownloadProgressCallbackType):

    job, file = job_file_for_asset(language_code, "categorylinks",  data_dump)

    data_dump.download(
        file,
        destination=to_path,
        download_progress_hook=download_progress_callback
    ).join()

    return DownloadMetaData(job.updated)
