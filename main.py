import argparse
import logging
import pathlib
from typing import Optional

from category_tree.scripts.update import update_all


def dir_path(string) -> Optional[pathlib.Path]:
    if string is None:
        return None

    path = pathlib.Path().joinpath(string)

    if path.is_dir():
        return path

    if not path.exists():
        path.mkdir()
        return path

    raise NotADirectoryError


def optional_int(value):
    return None if value is None else int(value)


parser = argparse.ArgumentParser(description="Updates all language files to a specific directory.")
parser.add_argument("dest", help="Destination directory.", type=dir_path, default=None, nargs="?")
parser.add_argument("--start", help="Specify language index to start after.", type=int, default=0)
parser.add_argument("--end", help="Specify language index to end on.", type=optional_int, default=None)


if __name__ == '__main__':
    args = parser.parse_args()
    var_args = vars(args)

    data_root_path = var_args["dest"]
    start = var_args["start"]
    end = var_args["end"]

    logging.root.setLevel(logging.INFO)
    update_all(data_root_path, start=start, end=end)
