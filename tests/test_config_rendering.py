import pathlib

import pint
import pytest
import yaml
from fspathtree import fspathtree

from powerconf import expressions, loaders, rendering, units, utils

from . import unit_test_utils

ureg = pint.UnitRegistry()
Q_ = ureg.Quantity


def test_batch_expansion_single_node():
    config = fspathtree({"time": {"max": {"@batch": [1, 2, 3]}}})
    config_renderer = rendering.ConfigRenderer(expressions.ExecExpressionEvaluator())

    tmp = config_renderer._get_batch_leaves(config)
    assert len(tmp) == 1
    assert "/time/max" in tmp
    assert tmp["/time/max"] == 3

    configs = config_renderer.expand_batch_nodes(config)
    assert len(configs) == 3
    assert configs[0]["/time/max"] == 1
    assert configs[1]["/time/max"] == 2
    assert configs[2]["/time/max"] == 3


def test_batch_expansion_two_nodes():
    config = fspathtree(
        {
            "time": {"max": {"@batch": [1, 2, 3]}},
            "grid": {"x": {"max": {"@batch": [4, 5]}}},
        }
    )
    config_renderer = rendering.ConfigRenderer(expressions.ExecExpressionEvaluator())

    tmp = config_renderer._get_batch_leaves(config)
    assert len(tmp) == 2
    assert "/time/max" in tmp
    assert "/grid/x/max" in tmp
    assert tmp["/time/max"] == 3
    assert tmp["/grid/x/max"] == 2

    configs = config_renderer.expand_batch_nodes(config)
    assert len(configs) == 6
    assert configs[0]["/time/max"] == 1
    assert configs[1]["/time/max"] == 1
    assert configs[2]["/time/max"] == 2
    assert configs[3]["/time/max"] == 2
    assert configs[4]["/time/max"] == 3
    assert configs[5]["/time/max"] == 3
    assert configs[0]["/grid/x/max"] == 4
    assert configs[1]["/grid/x/max"] == 5
    assert configs[2]["/grid/x/max"] == 4
    assert configs[3]["/grid/x/max"] == 5
    assert configs[4]["/grid/x/max"] == 4
    assert configs[5]["/grid/x/max"] == 5


def test_expand_to_list():
    config = fspathtree({"N": 10, "xmin": -1, "xmax": 1, "points": "$([1,2,3])"})
    config_renderer = rendering.ConfigRenderer()
    config = config_renderer.render(config)

    assert config["N"] == 10
    assert type(config["points"].tree) is list
    assert config["points"][0] == 1
    assert config["points"][1] == 2
    assert config["points"][2] == 3

    # list comprehension
    config = fspathtree(
        {
            "N": 10,
            "xmin": -1,
            "xmax": 1,
            "dx": "$((${xmax}-${xmin})/(${N}-1) )",
            "points": "$([ i*${dx} + ${xmin} for i in range(${N})])",
        }
    )
    config_renderer = rendering.ConfigRenderer()
    config = config_renderer.render(config)

    assert config["N"] == 10
    assert type(config["points"].tree) is list
    assert len(config["points"].tree) == 10
    assert config["points"][0] == -1
    assert config["points"][1] == pytest.approx(-1 + 2 / 9)
    assert config["points"][2] == pytest.approx(-1 + 4 / 9)
    assert config["points"][8] == pytest.approx(1 - 2 / 9)
    assert config["points"][9] == 1

    # list comprehension with quantities
    config = fspathtree(
        {
            "N": 10,
            "xmin": "-1 cm",
            "xmax": "1 cm",
            "dx": "$((${xmax}-${xmin})/(${N}-1) )",
            "points": "$([ i*${dx} + ${xmin} for i in range(${N})])",
        }
    )
    config_renderer = rendering.ConfigRenderer()
    config = config_renderer.render(config)

    assert config["N"] == 10
    assert type(config["points"].tree) is list
    assert len(config["points"].tree) == 10
    assert config["points"][0].to("m").magnitude == pytest.approx(-0.01)
    assert config["points"][1].to("m").magnitude == pytest.approx(-0.01 + 0.02 / 9)
    assert config["points"][2].to("m").magnitude == pytest.approx(-0.01 + 0.04 / 9)
    assert config["points"][8].to("m").magnitude == pytest.approx(0.01 - 0.02 / 9)
    assert config["points"][9].to("m").magnitude == pytest.approx(0.01)

    # list comprehension with quantities
    config = fspathtree(
        {
            "N": 10,
            "t0": "200 us",
            "tau": "50 us",
            "pulses": "$([ {'arrival_time': i*${t0}, 'duration' : ${tau}} for i in range(${N})])",
        }
    )
    config_renderer = rendering.ConfigRenderer()
    config = config_renderer.render(config)

    assert config["N"] == 10
    assert type(config["pulses"].tree) is list
    assert len(config["pulses"].tree) == 10
    assert config["pulses/0/arrival_time"] == 0
    assert config["pulses/1/arrival_time"].magnitude == 200
    assert config["pulses/2/arrival_time"].magnitude == 400


def test_expression_detector():
    assert not rendering.contains_expression(1)
    assert not rendering.contains_expression("x")
    assert not rendering.contains_expression("${x}")
    assert rendering.contains_expression("$(1 + 1)")
    assert rendering.contains_expression("_$(1 + 1)-var")
    assert rendering.contains_expression("_$(1 + 1)-to-$(2+2)")


def test_evaluate_expression():
    config = fspathtree(
        {
            "time": {"max": "$(1 + 2)"},
            "prefix": "_$(1 + 2)",
            "prefix2": "_$(1 + 2)-$(2+3)_",
            "sin_of_1": "$(math.sin(1))",
            "grid": {
                "x": {
                    "min": Q_(0, "cm"),
                    "length": Q_(1, "cm"),
                    "n": "$(2*ctx['../n'])",
                    "max": "$(ctx['min']+ctx['length'])",
                },
                "n": 10,
            },
        }
    )
    evaluator = expressions.ExecExpressionEvaluator()
    import math

    evaluator.add_global("math", math)
    config_renderer = rendering.ConfigRenderer(evaluator)

    config = config_renderer.render(config)

    assert config["/time/max"] == 3
    assert config["/prefix"] == "_3"
    assert config["/prefix2"] == "_3-5_"
    assert config["/sin_of_1"] == pytest.approx(math.sin(1))
    assert config["/grid/x/min"].magnitude == pytest.approx(0)
    assert config["/grid/x/max"].magnitude == pytest.approx(1)


def test_expand_variables():
    assert rendering.expand_variables("${x}", "ctx['{name}']") == "ctx['x']"
    assert (
        rendering.expand_variables("${x} + $y", "ctx['{name}']")
        == "ctx['x'] + ctx['y']"
    )


def test_construct_quantities():
    config = fspathtree(
        {"time": {"max": "2 s"}, "laser": {"power": "1 W/cm^2"}, "tag": "CW", "N": 10}
    )
    config_renderer = rendering.ConfigRenderer()
    config = config_renderer._construct_all_quantities(config)

    assert config["/time/max"].magnitude == pytest.approx(2)
    assert config["/laser/power"].to("mW/cm^2").magnitude == pytest.approx(1000)
    assert config["/tag"] == "CW"
    assert config["/N"] == 10


def test_only_construct_quantities_from_strings_that_look_like_a_quantity():
    """
    Pint is willing to treat way more text as a quantity than we want to allow.

    For example, '$(${cm})' will be interpretted as a quantity. So will 'quant'.

    So we only want to try to interpret something as a quantity if it starts wit a numerical value.
    """

    assert rendering.try_construct_quantity("4 m").magnitude == 4

    assert units.Q_("cm") is not None
    assert units.Q_("cm").magnitude == 1
    assert units.Q_("$(${cm})") is not None
    assert units.Q_("$(${cm})").magnitude == 1
    assert rendering.try_construct_quantity("cm") == "cm"
    assert rendering.try_construct_quantity("$(${cm})") == "$(${cm})"


def test_yaml_config_example_1():
    config_text = """
grid:
    res: 1 um
    x:
      min: 0 cm
      max: 1.5 cm
      N: $( ($max - $min) / ${../res} + 1 )
    y:
      min: 0 cm
      max: 0.5 cm
      N: $( ($max - $min) / ${../res} + 1 )
"""

    config = fspathtree(yaml.safe_load(config_text))

    config_renderer = rendering.ConfigRenderer()

    config = config_renderer.render(config)
    assert config["grid/x/max"].magnitude == pytest.approx(1.5)
    assert config["grid/x/N"] == 15001


def test_yaml_config_example_2():
    """Adding unit support to legacy configs..."""

    config_text = """
x_q: 13 mm
x: $($x_q.to("cm").magnitude)
"""

    config = fspathtree(yaml.safe_load(config_text))

    evaluator = expressions.ExecExpressionEvaluator()
    config_renderer = rendering.ConfigRenderer(evaluator)
    config = config_renderer.render(config)

    assert config["x_q"].magnitude == pytest.approx(13)
    assert config["x"] == pytest.approx(1.3)


def test_yaml_config_example_3():
    """Adding unit support to legacy configs..."""

    config_text = """
x_q: 13 mm
x: $($x_q.to("cm").magnitude)
"""

    config = fspathtree(yaml.safe_load(config_text))

    evaluator = expressions.ExecExpressionEvaluator()
    config_renderer = rendering.ConfigRenderer(evaluator)

    config = config_renderer.render(config)

    assert config["x_q"].magnitude == pytest.approx(13)
    assert config["x"] == pytest.approx(1.3)


def test_inplace_vs_copy_render():
    config_text = """
x_q: 13 mm
x: $($x_q.to("cm").magnitude)
"""

    config = fspathtree(yaml.safe_load(config_text))

    config_renderer = rendering.ConfigRenderer()

    rconfig = config_renderer.render(config)

    assert rconfig["x_q"].magnitude == pytest.approx(13)
    assert rconfig["x"] == pytest.approx(1.3)
    assert config["x_q"] == "13 mm"
    assert config["x"] == '$($x_q.to("cm").magnitude)'

    rconfig = config_renderer.render(config, make_copy=False)

    assert rconfig["x_q"].magnitude == pytest.approx(13)
    assert rconfig["x"] == pytest.approx(1.3)
    assert config["x_q"].magnitude == pytest.approx(13)
    assert config["x"] == pytest.approx(1.3)


def test_circular_dependency_detection():
    """Adding unit support to legacy configs..."""

    config_text = """
a : $($g)
b : $($a)
c : $($b)
d : $($c)
e : $($d)
f : $($e)
g : $($f)
"""

    config = fspathtree(yaml.safe_load(config_text))
    evaluator = expressions.ExecExpressionEvaluator()
    config_renderer = rendering.ConfigRenderer(evaluator)

    with pytest.raises(RuntimeError) as e:
        config = config_renderer.render(config)
    assert "Circular dependencies detected" in str(e)


def test_long_dependency_chaings():
    """Adding unit support to legacy configs..."""

    config_text = """
a : 'here'
b : $($a)
c : $($b)
d : $($c)
e : $($d)
f : $($e)
g : $($f)
"""

    config = fspathtree(yaml.safe_load(config_text))
    evaluator = expressions.ExecExpressionEvaluator()
    config_renderer = rendering.ConfigRenderer(evaluator)

    config = config_renderer.render(config)

    assert config["/g"] == "here"


def test_batch_expansion_and_rendering():
    config_text = """
a : 
    '@batch':
        - 1
        - 2
        - 3
b : $($a)
c : $($b)
d : $($c)
e : $($d)
f : $($e)
g : $($f)
"""

    config = fspathtree(yaml.safe_load(config_text))
    config_renderer = rendering.ConfigRenderer()
    configs = config_renderer.expand_and_render(config)

    assert len(configs) == 3
    assert configs[0]["/g"] == 1


def test_rendering_partial_configs():
    text = """
one: 1
two: 2
---
three : 3
    """

    configs = loaders.yaml_all_docs(text)
    configs = rendering.expand_partial_configs(configs)

    assert len(configs) == 1

    assert "one" in configs[0]
    assert "two" in configs[0]
    assert "three" in configs[0]

    configs = loaders.yaml_all_docs(text)
    configs = rendering.expand_partial_configs(configs, include_base=True)

    assert len(configs) == 2

    assert "one" in configs[0]
    assert "two" in configs[0]
    assert "three" not in configs[0]
    assert "one" in configs[1]
    assert "two" in configs[1]
    assert "three" in configs[1]


def test_rendering_partial_configs_with_nested_trees():
    text = """
sim:
    grid:
        res : 1 um
        x:
            min: 0 cm
            max: 1 cm
        y:
            min: 0 cm
            max: 1 cm
---
sim:
    grid:
        x:
            N: $( ($max-$min)/($/sim/grid/res) + 1)
        y:
            N: $( ($max-$min)/($/sim/grid/res) + 1)
    """

    configs = loaders.yaml_all_docs(text)
    configs = rendering.expand_partial_configs(configs)

    assert len(configs) == 1

    assert "/sim/grid/x/N" in configs[0]
    assert "/sim/grid/x/min" in configs[0]
    assert "/sim/grid/x/max" in configs[0]
    assert "/sim/grid/y/N" in configs[0]
    assert "/sim/grid/y/min" in configs[0]
    assert "/sim/grid/y/max" in configs[0]


def test_rendering_complex_dependencies():
    config = fspathtree(
        {
            "laser": {
                "irradiance": "1 W/cm^2",
                "one_over_e2_diameter": "1 cm",
                "one_over_e_diameter": "$(${one_over_e2_diameter}/math.sqrt(2))",
                "one_over_e_area": "$(math.pi*${one_over_e_diameter}**2/4)",
                "power": "$(${irradiance} * ${one_over_e_area})",
            }
        }
    )
    config_renderer = rendering.ConfigRenderer()
    config = config_renderer.render(config)

    assert config["/laser/one_over_e_diameter"].magnitude == pytest.approx(1 / 2**0.5)
    assert config["/laser/power"].magnitude == pytest.approx(1 * 3.14159 / 8)


def test_include_branches_yaml(tmp_path):
    with unit_test_utils.working_directory(tmp_path):
        text1 = """
    simulation:
        grid:
            x:
                '@include' : grid.yml
            y:
                '@include' : grid.yml
    """

        text2 = """
    min: 0 cm
    max: 1 cm
    N: 101
        """

        pathlib.Path("grid.yml").write_text(text2)

        config = loaders.yaml(text1)
        config = rendering.load_includes(config, loaders.yaml)

        assert "simulation/grid/x/min" in config
        assert "simulation/grid/x/max" in config
        assert "simulation/grid/x/N" in config
        assert "simulation/grid/y/min" in config
        assert "simulation/grid/y/max" in config
        assert "simulation/grid/y/N" in config

        assert config["simulation/grid/x/min"] == "0 cm"
        assert config["simulation/grid/x/max"] == "1 cm"
        assert config["simulation/grid/x/N"] == 101
        assert config["simulation/grid/y/min"] == "0 cm"
        assert config["simulation/grid/y/max"] == "1 cm"
        assert config["simulation/grid/y/N"] == 101


def test_multi_level_include_branches_yaml(tmp_path):
    with unit_test_utils.working_directory(tmp_path):
        text1 = """
    simulation:
        grid:
            '@include' : grid.yml
    """

        text2 = """
    x: 
        '@include' : x-grid.yml
    y: 
        '@include' : x-grid.yml
    """
        text3 = """
    min: 0 cm
    max: 1 cm
    N: 101
        """
        text4 = """
    min: 1 cm
    max: 2 cm
    N: 201
        """

        pathlib.Path("grid.yml").write_text(text2)
        pathlib.Path("x-grid.yml").write_text(text3)
        pathlib.Path("y-grid.yml").write_text(text4)

        config = loaders.yaml(text1)
        config = rendering.load_includes(config, loaders.yaml)

        assert "simulation/grid/x/min" in config
        assert "simulation/grid/x/max" in config
        assert "simulation/grid/x/N" in config
        assert "simulation/grid/y/min" in config
        assert "simulation/grid/y/max" in config
        assert "simulation/grid/y/N" in config

        assert config["simulation/grid/x/min"] == "0 cm"
        assert config["simulation/grid/x/max"] == "1 cm"
        assert config["simulation/grid/x/N"] == 101
        assert config["simulation/grid/y/min"] == "0 cm"
        assert config["simulation/grid/y/max"] == "1 cm"
        assert config["simulation/grid/y/N"] == 101


def test_yaml_config_var_name_errors():
    config_text = """
layers:
    - name: layer 1
      thickness: 10 um
grid:
    x:
      max: $( ${../layers/0/thickness}) # element name does not walk up the tree far enough
"""

    config = fspathtree(yaml.safe_load(config_text))

    config_renderer = rendering.ConfigRenderer()

    with pytest.raises(KeyError) as e:
        config = config_renderer.render(config)

    assert (
        e.value.args[0]
        == "Error while parsing path '/grid/layers/0/thickness'. Could not find path element 'layers'."
    )

    config_text = """
layers:
    - name: layer 1
      thickness: 10 um
grid:
    x:
      max: $( ${/layer/0/thickness})
"""

    config = fspathtree(yaml.safe_load(config_text))

    config_renderer = rendering.ConfigRenderer()

    with pytest.raises(KeyError) as e:
        config = config_renderer.render(config)

    assert (
        e.value.args[0]
        == "Error while parsing path '/layer/0/thickness'. Could not find path element 'layer'."
    )


def test_creating_filenames():
    """
    Demonstrate how we can powerconf to generate filenames (for output for example) based on config parameters.
    """

    config_text = """
layers:
    - name: layer 1
      thickness: 10 um
      absorption: 2 1 / cm
grid:
    x:
      max: $( ${/layers/0/thickness})
laser:
    radius: 100 um
    irradiance: 2 W /cm^2

simulation: 
    output: Tvst-$(${/layers/0/absorption}.to("1/cm").magnitude|fmt(_1,".0f"))_inv_cm-$(${/laser/radius}.to("um").magnitude|fmt(_1,".0f"))_um.txt
    id: $( id(ctx))
"""

    config = fspathtree(yaml.safe_load(config_text))

    config_renderer = rendering.ConfigRenderer()

    def del_space(text):
        return text.replace(" ", "_")

    def to(q, u):
        return q.to(u).magnitude

    def fmt(v, spec=""):
        return ("{:" + spec + "}").format(v)

    assert fmt(10) == "10"
    config_renderer.expression_evaluator.add_global("del_space", del_space)
    config_renderer.expression_evaluator.add_global("fmt", fmt)
    config_renderer.expression_evaluator.add_global("to", to)
    config_renderer.expression_evaluator.add_global("id", utils.get_id)

    config = config_renderer.render(config)

    assert config["/simulation/output"] == "Tvst-2_inv_cm-100_um.txt"
    assert config["/simulation/id"] == "1c8c60bee71afc4f3143ef6edf3ca971"
