# wiki_categories

Tools for collecting and transforming the Wikipedia category tree.

## Usage as CLI

Firstly, install requirements.

```commandline
py -m pip install -r requirements.txt
```

The following utility allows you to serialize the Wikipedia category tree for the language `en`, and 
save it to the local directory `data`.

```commandline
py main.py data --languages en
```

Note: The English Wikipedia (`en`) is very large, the required assets will take a long time to download.

Through the available CLI arguments, you can adjust the parameters of the category tree trimming and serialization.
For example, lowering `--pages-percentile` allows you to be more permissive with lower page-count categories, and 
extending `--max-depth` can offer deeper category trees.

```commandline
py main.py --languages en --pages-percentile 20 --max-depth 200
```

Note: The above means "trim all categories with page-count that falls under the 20th percentile of all categories, 
and trim any categories that fall outside a distance of 200 from the root node."

## Usage as libary

To demonstrate simple use cases of the library, the second example in "Usage as CLI" can also be written in the 
form of a Python script:

```python
from pathlib import Path

from category_tree import DataDir


data_dir = DataDir("en", root_path=Path().joinpath("data"))
data_dir.save_trimmed_category_tree(pages_percentile=20, max_depth=200)

#  Note: This automatically generates the full category tree in addition to the trimmed category tree,
#  because the trimmed category tree is dependent upon the existence of the full category tree.
```

If saving the category tree isn't needed, then you can manipulate the category tree in memory.

```python
from category_tree import fetch_category_tree_data
from category_tree import CategoryTree

c_tree = CategoryTree(fetch_category_tree_data("en"))

c_tree.add_root()
c_tree.trim_hidden()
c_tree.trim_by_page_count_percentile(20)
c_tree.trim_by_id_without_name()
c_tree.trim_by_max_depth(200)

#  The above modifies the category tree in-place.
```

## Disclaimer

The author of this software is not affiliated, associated, authorized, endorsed by, or in any way 
officially connected with The Wikimedia Foundation or any of its affiliates and is independently 
owned and created.