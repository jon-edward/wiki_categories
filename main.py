import datetime
import json
import logging
import pathlib
import traceback

from wiki_categories.scripts.save_graph_run import process_language, default_languages


if __name__ == '__main__':
    started = datetime.datetime.now()

    root = pathlib.Path("./data")

    root.mkdir(exist_ok=True)

    languages_processed = []
    incomplete_languages = []

    for language in default_languages:
        try:
            finished = process_language(language, root.joinpath(language))

            if finished:
                languages_processed.append(language)
        except:
            incomplete_languages.append(language)
            logging.error(traceback.format_exc())

    with open(root.joinpath("_meta.json"), 'w', encoding="utf-8") as f:
        json.dump({
            "started": started.isoformat(),
            "finished": datetime.datetime.now().isoformat(),
            "languages_processed": languages_processed,
            "incomplete_languages": incomplete_languages
        }, f)
