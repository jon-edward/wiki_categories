from typing import Optional

from requests import Session


__all__ = (
    "CategoryNotFound",
    "id_for_category_str_by_lang"
)


ROOT_SESSION = Session()


class CategoryNotFound(Exception):
    pass


def id_for_category_str_by_lang(lang: str, category: str, source_lang: str):

    def make_request_names(continue_token: Optional[str] = None) -> dict:
        params = {
            "action": "query",
            "format": "json",
            "prop": "langlinks",
            "titles": category,
            "formatversion": "2",
            "lllang": lang,
        }

        if continue_token is not None:
            params["llcontinue"] = continue_token

        return ROOT_SESSION.get(
            f"https://{source_lang}.wikipedia.org/w/api.php", params=params
        ).json()

    if lang != source_lang:
        _response_json = make_request_names()
        try:
            category_name = _response_json["query"]["pages"][0]["langlinks"][0]["title"]
        except KeyError:
            raise CategoryNotFound(category)
    else:
        category_name = category

    def make_request_ids():
        params = {"action": "query", "format": "json", "titles": category_name}
        return ROOT_SESSION.get(
            f"https://{lang}.wikipedia.org/w/api.php", params=params
        ).json()

    return [int(k) for k in make_request_ids()["query"]["pages"].keys()][0]
