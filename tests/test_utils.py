import pint
from fspathtree import fspathtree

from powerconf import utils

Q_ = pint.UnitRegistry().Quantity


def test_config_id():
    config1 = fspathtree({"one": 1})
    config2 = fspathtree({"one": 1, "two": 2})
    config3 = fspathtree({"one": 1})

    _id1 = utils.get_id(config1)
    _id2 = utils.get_id(config2)
    _id3 = utils.get_id(config3)

    assert _id1 != _id2
    assert _id1 == _id3
    assert _id2 != _id3

    assert utils.get_id(config2, path_predicate=lambda p: p.name != "two") == _id1


def test_config_id_with_quantities():
    config1 = fspathtree({"one": Q_(1, "cm")})
    config2 = fspathtree({"one": Q_(1, "cm"), "two": Q_(2, " cm")})
    config3 = fspathtree({"one": Q_(1, " cm")})

    _id1 = utils.get_id(config1)
    _id2 = utils.get_id(config2)
    _id3 = utils.get_id(config3)

    assert _id1 != _id2
    assert _id1 == _id3
    assert _id2 != _id3

    assert utils.get_id(config2, path_predicate=lambda p: p.name != "two") == _id1


def test_transforming_quantities_to_strings():
    config = fspathtree({"x": Q_(1, "cm"), "N": 1})
    config = utils.apply_transform(
        config, lambda p, n: str(n) if type(n) is Q_ else config[p]
    )

    assert config["x"] == "1 centimeter"
    assert config["N"] == 1


def test_transforming_quantities_to_strings_with_predicate():
    config = fspathtree({"x": Q_(1, "cm"), "N": 1})
    config = utils.apply_transform(
        config, lambda p, n: str(n), predicate=lambda p, n: hasattr(n, "magnitude")
    )

    assert config["x"] == "1 centimeter"
    assert config["N"] == 1


def test_apply_transform_to_list_of_configs():
    configs = []
    configs.append(fspathtree({"x": Q_(1, "cm"), "N": 1}))
    configs.append(fspathtree({"x": Q_(1, "cm"), "N": 1}))

    configs = utils.apply_transform(
        configs, lambda p, n: str(n), predicate=lambda p, n: hasattr(n, "magnitude")
    )

    assert len(configs) == 2
    assert configs[0]["x"] == "1 centimeter"
    assert configs[0]["N"] == 1
    assert configs[1]["x"] == "1 centimeter"
    assert configs[1]["N"] == 1
