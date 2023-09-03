import datetime
import logging
import os
import pathlib
import shutil

from category_tree.data_dir import DataDir

languages = (
    # 'en',
    # 'ceb',
    # 'de',
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


def update(data_dir: DataDir):

    data_dir.save_raw_category_tree()
    data_dir.save_trimmed_category_tree()
    data_dir.save_compressed_category_tree()
    data_dir.save_meta_file()

    os.unlink(data_dir.raw_category_tree_path)


def update_all(root_path: pathlib.Path = None, *, remove_existing: bool = True, start: int = 0, end: int = None):

    for lang in languages[start:end]:

        starting_time = datetime.datetime.now()

        logging.info(f"Starting {lang}wiki at {starting_time.time()}")

        try:
            data_dir = DataDir(lang, root_path=root_path)

            logging.log(logging.INFO, f"Saving {lang}wiki to {data_dir.lang_dir_root.absolute()}")

            if remove_existing:
                shutil.rmtree(data_dir.lang_dir_root, ignore_errors=True)

            update(data_dir)
        except Exception as e:
            logging.exception(e, exc_info=e, stack_info=True)

        logging.info(f"Finished in {datetime.datetime.now() - starting_time}")
