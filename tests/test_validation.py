import os
import pathlib

from powerconf import validation, yaml


def test_simple_validation(tmp_path):

    orig_path = os.getcwd()
    os.chdir(tmp_path)

    config_text = """
grid:
    x:
        min: 0
        max: 2
    y:
        max: 0
        min: 2
    """
    validation_text = """
def max_greater_than_min(config):
    assert config['/grid/x/max'] > config['/grid/x/min'], '/grid/x/max must be greater than /grid/x/min'
    assert config['/grid/y/max'] > config['/grid/y/min'], '/grid/y/max must be greater than /grid/y/min'
    """

    config_file = tmp_path / "CONFIG.yml"
    config_file.write_text(config_text)
    validation_file = tmp_path / "powerconf_validate.py"
    validation_file.write_text(validation_text)

    configs = yaml.powerload(config_file)

    results = validation.validate_config(configs[0], validation_file)

    assert len(results) == 1
    assert "max_greater_than_min" in results
    assert results["max_greater_than_min"]["result"] == "fail"
    assert "/grid/y/max must be greater than /grid/y/min" in str(
        results["max_greater_than_min"]["exception"]
    )

    os.chdir(orig_path)
