# wiki_categories

Tools for collecting and transforming the Wikipedia category tree.

## Usage

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

## Disclaimer

The author of this software is not affiliated, associated, authorized, endorsed by, or in any way 
officially connected with The Wikimedia Foundation or any of its affiliates and is independently 
owned and created.