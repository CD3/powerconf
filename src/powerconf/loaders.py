"""A collection of functions for loading config trees from a file or string."""

import pathlib

import fspathtree
import yaml as _yaml


def yaml(text_or_file: str | pathlib.Path):
    """
    Load a configuration tree from a string or file.
    """
    if type(text_or_file) is str:
        text = text_or_file
    else:
        text = text_or_file.read_text()

    config = fspathtree.fspathtree(_yaml.safe_load(text))

    return config


def yaml_all_docs(text_or_file: pathlib.Path | str):
    """Load all documents in YAML file."""
    if type(text_or_file) is str:
        text = text_or_file
    else:
        text = text_or_file.read_text()

    configs = []
    for doc in text.split("---"):
        configs.append(fspathtree.fspathtree(_yaml.safe_load(doc)))

    return configs
