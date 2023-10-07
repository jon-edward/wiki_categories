from typing import Optional

import requests


def hidden_category_id(language: str, session: requests.Session):
    def make_request_names(continue_token: Optional[str] = None) -> dict:
        params = {
            "action": "query",
            "format": "json",
            "prop": "langlinks",
            "titles": "Category:Hidden categories",
            "formatversion": "2",
            "lllang": language,
        }

        if continue_token is not None:
            params["llcontinue"] = continue_token

        return session.get(
            "https://en.wikipedia.org/w/api.php", params=params
        ).json()

    if language != "en":
        _response_json = make_request_names()
        try:
            category_name = _response_json["query"]["pages"][0]["langlinks"][0]["title"]
        except KeyError:
            raise Exception("Hidden category not found.")
    else:
        category_name = "Category:Hidden categories"

    def make_request_ids():
        params = {"action": "query", "format": "json", "titles": category_name}
        return session.get(
            f"https://{language}.wikipedia.org/w/api.php", params=params
        ).json()

    return [int(k) for k in make_request_ids()["query"]["pages"].keys()][0]
