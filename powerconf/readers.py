import pathlib

import yaml
from fspathtree import fspathtree


def load_yaml_docs(text_or_file: pathlib.Path | str):
    """Load all documents in YAML file."""
    if type(text_or_file) == str:
        text = text_or_file
    else:
        text = text_or_file.read_text()

    configs = []
    for doc in text.split("---"):
        configs.append(fspathtree(yaml.safe_load(doc)))

    return configs
