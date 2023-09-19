from typing import List, Optional

from category_tree.wiki_utils._session import ROOT_SESSION


_main_topics = (
    "Academic disciplines",
    "Business",
    "Communication",
    "Concepts",
    "Culture",
    "Economy",
    "Education",
    "Energy",
    "Engineering",
    "Entertainment",
    "Entities",
    "Ethics",
    "Food and drink",
    "Geography",
    "Government",
    "Health",
    "History",
    "Human behavior",
    "Humanities",
    "Information",
    "Internet",
    "Knowledge",
    "Language",
    "Law",
    "Life",
    "Mass media",
    "Mathematics",
    "Military",
    "Nature",
    "People",
    "Philosophy",
    "Politics",
    "Religion",
    "Science",
    "Society",
    "Sports",
    "Technology",
    "Time",
    "Universe"
)


def main_topic_classifications(language_code: str) -> List[int]:

    def make_request_names(continue_token: Optional[str] = None) -> dict:
        params = {
            "action": "query",
            "format": "json",
            "prop": "langlinks",
            "titles": "|".join(f"Category:{topic}" for topic in _main_topics),
            "formatversion": "2",
            "lllang": language_code
        }

        if continue_token is not None:
            params["llcontinue"] = continue_token

        return ROOT_SESSION.get("https://en.wikipedia.org/w/api.php", params=params).json()

    if language_code != "en":
        _response_json = make_request_names()

        category_names = []

        def process_response_names(response_json: dict):
            content = response_json["query"]["pages"]
            for page in content:
                if "langlinks" not in page:
                    continue
                category_names.append(page["langlinks"][0]["title"])

        process_response_names(_response_json)

        while _response_json.get("continue", {}).get("llcontinue", False):
            _continue_token = _response_json["continue"]["llcontinue"]
            _response_json = make_request_names(_continue_token)
            process_response_names(_response_json)

    else:
        category_names = [f"Category:{topic}" for topic in _main_topics]

    def make_request_ids():
        params = {
            "action": "query",
            "format": "json",
            "titles": "|".join(category_names)
        }
        return ROOT_SESSION.get(f"https://{language_code}.wikipedia.org/w/api.php", params=params).json()

    return [int(k) for k in make_request_ids()["query"]["pages"].keys()]