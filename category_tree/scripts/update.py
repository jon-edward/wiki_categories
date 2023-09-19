import datetime
import json
import logging
import os
import pathlib
from typing import Iterable, List

import wiki_data_dump
import wiki_data_dump.mirrors

from category_tree.data_dir import DataDir
from category_tree.generate.download import job_file_for_asset


def _update_data_dir(data_dir: DataDir, force_update: bool) -> bool:

    class ForceUpdateException(Exception):
        pass

    try:
        if force_update:
            raise ForceUpdateException

        with open(data_dir.meta_file_path, 'r') as f:
            previous_meta = json.load(f)

            last_pagetable_updated = previous_meta["pagetable"]["updated"]
            last_categorylinks_updated = previous_meta["categorylinks"]["updated"]
            last_category_updated = previous_meta["category"]["updated"]

            data_dump = wiki_data_dump.WikiDump(wiki_data_dump.mirrors.MirrorType.YOUR)

            current_pagetable_updated = job_file_for_asset(data_dir.language, "pagetable", data_dump)[0].updated
            current_categorylinks_updated = job_file_for_asset(data_dir.language, "categorylinks", data_dump)[0].updated
            current_category_updated = job_file_for_asset(data_dir.language, "category", data_dump)[0].updated

            current_pagetable_updated = str(datetime.datetime.fromisoformat(current_pagetable_updated).date())
            current_categorylinks_updated = str(datetime.datetime.fromisoformat(current_categorylinks_updated).date())
            current_category_updated = str(datetime.datetime.fromisoformat(current_category_updated).date())

            not_outdated_check = all(
                (
                    last_pagetable_updated == current_pagetable_updated,
                    last_categorylinks_updated == current_categorylinks_updated,
                    last_category_updated == current_category_updated
                )
            )

            if not_outdated_check:
                logging.info(f"Remote assets are at the same update date as local assets, skipping.")
                return False

    except OSError:
        logging.error(f"Error loading {data_dir.meta_file_path}, skipping check and overwriting data assets.")
    except KeyError as e:
        logging.error(f"Meta file does not have key {e}, skipping check and overwriting data assets.")
    except ForceUpdateException:
        logging.info(f"Forcing update and overwriting language {data_dir.language}.")

    data_dir.save_raw_category_tree()
    data_dir.save_trimmed_category_tree()
    data_dir.save_compressed_category_tree()
    data_dir.save_meta_file()

    os.unlink(data_dir.raw_category_tree_path)

    return True


def update(languages: Iterable[str], root_path: pathlib.Path = None, force_update: bool = False) -> List[str]:

    if isinstance(languages, str):
        languages = languages,

    updated_languages = []

    for lang in languages:

        starting_time = datetime.datetime.now()

        logging.info(f"-- Starting {lang}wiki at {starting_time.time()} --")

        try:
            data_dir = DataDir(lang, root_path=root_path)

            logging.log(logging.INFO, f"Will save {lang}wiki to {data_dir.lang_dir_root.absolute()}")

            did_update = _update_data_dir(data_dir, force_update)

            if did_update:
                updated_languages.append(lang)

        except Exception as e:
            logging.exception(e, exc_info=e, stack_info=True)

        logging.info(f"Finished in {datetime.datetime.now() - starting_time}")

    return updated_languages
