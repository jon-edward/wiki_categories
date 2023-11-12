import logging
import pathlib
import traceback

from wiki_categories.scripts.save_graph_run import process_language, default_languages


if __name__ == '__main__':
    root = pathlib.Path("./data")

    for language in default_languages:
        try:
            process_language(language, root.joinpath(language))
        except:
            logging.error(traceback.format_exc())
