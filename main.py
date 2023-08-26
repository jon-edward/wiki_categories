import argparse
import logging
import os
import pathlib

from category_tree.scripts.update import update_all


def dir_path(string):
    if string is None:
        return None

    path = pathlib.Path().joinpath(string)

    if path.is_dir():
        return path

    if not path.exists():
        path.mkdir()
        return path

    raise NotADirectoryError


parser = argparse.ArgumentParser(description="Updates all language files to a specific directory.")
parser.add_argument("dest", help="Destination directory.", type=dir_path, default=None, nargs="?")


if __name__ == '__main__':
    args = parser.parse_args()
    data_root_path = vars(args)["dest"]
    logging.root.setLevel(logging.INFO)
    update_all(data_root_path)
