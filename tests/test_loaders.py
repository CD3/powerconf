import pathlib

import fspathtree

from powerconf import loaders

from . import unit_test_utils


def test_yaml_loader(tmp_path):
    text = """one: 1"""
    config = loaders.yaml(text)
    assert type(config) is fspathtree.fspathtree
    assert "one" in config
    assert config["one"] == 1

    with unit_test_utils.working_directory(tmp_path):
        text = """
        one: 1
        two: 2
        """
        pathlib.Path("CONFIG.yml").write_text(text)
        config = loaders.yaml(pathlib.Path("CONFIG.yml"))
        assert type(config) is fspathtree.fspathtree
        assert "one" in config
        assert "two" in config
        assert config["one"] == 1
        assert config["two"] == 2


def test_yaml_multi_doc_loader(tmp_path):
    text = """
one: 1
two: 2
---
three : 3
    """

    configs = loaders.yaml_all_docs(text)

    assert len(configs) == 2
    assert "one" in configs[0]
    assert "two" in configs[0]
    assert "three" not in configs[0]
    assert "three" in configs[1]
