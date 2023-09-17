import datetime
import json
import logging
import os
import pathlib

import wiki_data_dump
import wiki_data_dump.mirrors

from category_tree.data_dir import DataDir
from category_tree.generate.download import job_file_for_asset

languages = (
    'en',
    'ceb',
    'de',
    'sv',
    'fr',
    'nl',
    'ru',
    'es',
    'it',
    'arz',
    'pl',
    'ja',
    'zh',
    'vi',
    # 'war',
    'uk',
    'ar',
    'pt',
    'fa',
    'ca',
    'sr',
    # 'id',
    'ko',
    'no',
    'ce',
    'fi',
    'tr',
    'hu',
    'cs',
    'tt',
    'sh',
    'ro',
    # 'zh-min-nan',
    'eu',
    'ms',
    'eo',
)


def update(data_dir: DataDir) -> bool:

    try:
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

    except OSError as e:
        logging.error(f"Error loading {data_dir.meta_file_path}, skipping check and overwriting data assets.")
    except KeyError as e:
        logging.error(f"Meta file does not have key {e}, skipping check and overwriting data assets.")

    data_dir.save_raw_category_tree()
    data_dir.save_trimmed_category_tree()
    data_dir.save_compressed_category_tree()
    data_dir.save_meta_file()

    os.unlink(data_dir.raw_category_tree_path)

    return True


def update_all(root_path: pathlib.Path = None, *, start: int = 0, end: int = None):

    updated_languages = []

    for lang in languages[start:end]:

        starting_time = datetime.datetime.now()

        logging.info(f"Starting {lang}wiki at {starting_time.time()}")

        try:
            data_dir = DataDir(lang, root_path=root_path)

            logging.log(logging.INFO, f"Saving {lang}wiki to {data_dir.lang_dir_root.absolute()}")

            did_update = update(data_dir)

            if did_update:
                updated_languages.append(lang)

        except Exception as e:
            logging.exception(e, exc_info=e, stack_info=True)

        logging.info(f"Finished in {datetime.datetime.now() - starting_time}")

    return updated_languages
