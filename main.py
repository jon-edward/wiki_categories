import argparse
import datetime
import json
import logging
import pathlib
from typing import Optional

from category_tree.scripts.update import update


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


parser = argparse.ArgumentParser(description="Updates language files to a destination directory.")

parser.add_argument("dest", help="Destination directory.", type=dir_path, default=None, nargs="?")

parser.add_argument(
    "--languages",
    help="List of languages to update (defaults to languages.txt if not specified).",
    default=[],
    nargs="+"
)

parser.add_argument(
    "--force-update",
    help="Do not check previous update time, and overwrite existing destination directory if existent.",
    action="store_true"
)

parser.add_argument(
    "--suppress-logging",
    help="Do not set logging level to 'logging.INFO'.",
    action="store_true"
)


if __name__ == '__main__':
    args = parser.parse_args()
    var_args = vars(args)

    data_root_path = var_args["dest"]

    if not var_args["suppress_logging"]:
        logging.root.setLevel(logging.INFO)

    if not var_args["languages"]:
        languages_path = pathlib.Path(__file__).parent.joinpath("languages.txt")
        with open(languages_path, 'r') as f:
            languages = [s.strip() for s in f.readlines()]
    else:
        languages = var_args["languages"]

    updated_languages = update(languages, root_path=data_root_path, force_update=var_args["force_update"])

    if data_root_path:
        data_root_path: pathlib.Path

        with open(data_root_path.joinpath("meta.json"), 'w') as f:
            json.dump({"finished_run": datetime.datetime.now().isoformat(), "updated_languages": updated_languages}, f, indent=1)
