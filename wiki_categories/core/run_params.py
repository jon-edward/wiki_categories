from dataclasses import dataclass


@dataclass
class RunParams:
    pages_percentile: int
    max_depth: int
    keep_hidden: bool
