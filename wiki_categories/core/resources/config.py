from dataclasses import dataclass, field

import requests
import wiki_data_dump as wdd

from wiki_categories.core.resources.progress_managers import ProgressManager, TqdmProgressManager

__all__ = (
    "ResourceConfig",
)


@dataclass
class ResourceConfig:
    wiki_dump: wdd.WikiDump = field(default_factory=wdd.WikiDump)
    session: requests.Session = field(default_factory=requests.Session)
    progress_manager: ProgressManager = field(default_factory=TqdmProgressManager)
