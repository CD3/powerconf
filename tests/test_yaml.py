import os
import pathlib

import pytest
import time

from powerconf import yaml


def test_yaml_powerload(tmp_path):
    text = """
grid:
    res: 1 um
    x: 
        res: $(${../res})
        min: 0 cm
        max: 1 cm
        N: $( ($max-$min)/${res} + 1)
    y: 
        res: $(${../res})
        min: 0 cm
        max: 1 cm
        N: $( ($max-$min)/${res} + 1)
laser:
    profile:
        R: $(${D}/2)
        D: 
         '@batch':
           - 10 um
           - 20 um
           - 50 um
---
laser:
    pulse:
        tau: 10 us
        T: 0.25 s
        N:
            '@batch':
                - 1
                - 2
                - 4
                - 8
---
laser:
    pulse:
        tau: 100 us
        T: 0.25 s
        N:
            '@batch':
                - 1
                - 2
                - 4
"""
    orig_path = os.getcwd()
    os.chdir(tmp_path)

    config_file = pathlib.Path("CONFIG.yml")
    config_file.write_text(text)

    configs = yaml.powerload(config_file)

    assert len(configs) == 21

    assert configs[0]["/laser/pulse/tau"].to("s").magnitude == pytest.approx(10e-6)
    assert configs[0]["/laser/pulse/N"] == 1
    assert configs[0]["/laser/profile/R"].to("cm").magnitude == pytest.approx(10e-4 / 2)

    configs = yaml.powerload("CONFIG.yml")

    assert len(configs) == 21

    assert configs[0]["/laser/pulse/tau"].to("s").magnitude == pytest.approx(10e-6)
    assert configs[0]["/laser/pulse/N"] == 1
    assert configs[0]["/laser/profile/R"].to("cm").magnitude == pytest.approx(10e-4 / 2)

    os.chdir(orig_path)


def test_yaml_powerload_with_parallelization(tmp_path):
    text = """
grid:
    res: 1 um
    x: 
        res: $(${../res})
        min: 0 cm
        max: 1 cm
        N: $( ($max-$min)/${res} + 1)
    y: 
        res: $(${../res})
        min: 0 cm
        max: 1 cm
        N: $( ($max-$min)/${res} + 1)
laser:
    profile:
        R: $(${D}/2)
        D: 10 um
slow: $(time.sleep(2))
---
laser:
    pulse:
        tau: 10 us
---
laser:
    pulse:
        tau: 100 us
"""
    extensions= """
import time

    """
    orig_path = os.getcwd()
    os.chdir(tmp_path)

    config_file = pathlib.Path("CONFIG.yml")
    config_file.write_text(text)
    extensions_file = pathlib.Path("powerconf_extensions.py")
    extensions_file.write_text(extensions)

    start = time.perf_counter_ns()
    configs = yaml.powerload(config_file)
    stop = time.perf_counter_ns()
    serial_runtime = stop - start

    start = time.perf_counter_ns()
    configs = yaml.powerload(config_file,njobs=2)
    stop = time.perf_counter_ns()
    parallel_runtime = stop - start


    assert parallel_runtime < 0.75*serial_runtime
