from category_tree.scripts.update import languages


if __name__ == '__main__':
    descriptive = "\n".join(f" - [{lang}](https://{lang}.wikipedia.org)" for lang in sorted(languages))
    print(descriptive)
