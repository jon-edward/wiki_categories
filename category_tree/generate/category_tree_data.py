import dataclasses
import datetime
from typing import Dict, List, Tuple, TypedDict


class MetaDict(TypedDict):
    updated: datetime.date


@dataclasses.dataclass
class CategoryTreeData:
    language: str

    meta: Dict[str, MetaDict]

    id_to_name: Dict[int, str]
    id_to_page_count: Dict[int, int]
    edges: List[Tuple[int, int]]

    def to_dict(self):
        return {
            "language": self.language,
            "meta": {k: {"updated": v["updated"].isoformat()} for k, v in self.meta.items()},
            "id_to_name": self.id_to_name,
            "id_to_page_count": self.id_to_page_count,
            "edges": self.edges
        }

    @classmethod
    def from_dict(cls, d: Dict):
        language = d["language"]

        meta: Dict[str, MetaDict] = {
            k: {"updated": datetime.date.fromisoformat(v["updated"])} for k, v in d["meta"].items()}

        id_to_name = {int(k): v for k, v in d["id_to_name"].items()}
        id_to_page_count = {int(k): v for k, v in d["id_to_page_count"].items()}
        edges = d["edges"]

        return cls(
            language=language,
            meta=meta,
            id_to_name=id_to_name,
            id_to_page_count=id_to_page_count,
            edges=edges
        )
