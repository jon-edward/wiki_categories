from typing import Optional

from category_tree.wiki_utils._session import ROOT_SESSION


class HiddenCategoryNotFound(Exception):
    pass


def hidden_category_id(language_code: str) -> int:
    def make_request_names(continue_token: Optional[str] = None) -> dict:
        params = {
            "action": "query",
            "format": "json",
            "prop": "langlinks",
            "titles": "Category:Hidden categories",
            "formatversion": "2",
            "lllang": language_code,
        }

        if continue_token is not None:
            params["llcontinue"] = continue_token

        return ROOT_SESSION.get(
            "https://en.wikipedia.org/w/api.php", params=params
        ).json()

    if language_code != "en":
        _response_json = make_request_names()
        try:
            category_name = _response_json["query"]["pages"][0]["langlinks"][0]["title"]
        except KeyError:
            raise HiddenCategoryNotFound()
    else:
        category_name = "Category:Hidden categories"

    def make_request_ids():
        params = {"action": "query", "format": "json", "titles": category_name}
        return ROOT_SESSION.get(
            f"https://{language_code}.wikipedia.org/w/api.php", params=params
        ).json()

    return [int(k) for k in make_request_ids()["query"]["pages"].keys()][0]
