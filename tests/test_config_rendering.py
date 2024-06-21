import pint
import pyparsing
import pytest
import yaml
from fspathtree import fspathtree

from powerconf import expressions, parsing, rendering

ureg = pint.UnitRegistry()
Q_ = ureg.Quantity


def test_batch_expansion_single_node():
    config = fspathtree({"time": {"max": {"@batch": [1, 2, 3]}}})
    config_renderer = rendering.ConfigRenderer(expressions.ExecExpressionEvaluator())

    tmp = config_renderer._get_batch_leaves(config)
    assert len(tmp) == 1
    assert "/time/max" in tmp
    assert tmp["/time/max"] == 3

    configs = config_renderer._expand_batch_nodes(config)
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

    configs = config_renderer._expand_batch_nodes(config)
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


def test_expression_detector():

    config_renderer = rendering.ConfigRenderer(expressions.ExecExpressionEvaluator())

    assert config_renderer._contains_expression(1) == False
    assert config_renderer._contains_expression("x") == False
    assert config_renderer._contains_expression("${x}") == False
    assert config_renderer._contains_expression("$(1 + 1)") == True
    assert config_renderer._contains_expression("_$(1 + 1)-var") == True
    assert config_renderer._contains_expression("_$(1 + 1)-to-$(2+2)") == True


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
    config_renderer = rendering.ConfigRenderer()
    assert config_renderer._expand_variables("${x}", "ctx['{name}']") == "ctx['x']"
    assert (
        config_renderer._expand_variables("${x} + $y", "ctx['{name}']")
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
