import pint
import pyparsing
import pytest
from fspathtree import fspathtree

from powerconfig import expressions

ureg = pint.UnitRegistry()
Q_ = ureg.Quantity


def test_expression_evaluator():
    ctx = fspathtree()
    ctx["/grid/x/min"] = Q_(0, "cm")
    ctx["/grid/x/max"] = Q_(10, "cm")
    ctx["/grid/x/N"] = Q_(101, "")

    evaluator = expressions.ExecExpressionEvaluator()
    evaluator.start()
    evaluator.add_global("c", ctx)
    evaluator.add_global("Q_", Q_)
    dx = evaluator.eval("(c['/grid/x/max'] - c['/grid/x/min']) / (c['/grid/x/N']-1)")
    assert dx.magnitude == 0.1

    ctx["/grid/x/N"] = Q_(201, "")
    dx = evaluator.eval("(c['/grid/x/max'] - c['/grid/x/min']) / (c['/grid/x/N']-1)")
    assert dx.magnitude == 0.05

    f = evaluator.eval(
        "numpy.exp( (c['/grid/x/max'] - c['/grid/x/min']) / Q_(10,'cm') )"
    )
    assert dx.magnitude == 0.05

    evaluator.stop()


def test_expression_evaluator_bad_text():
    ctx = fspathtree()
    evaluator = expressions.ExecExpressionEvaluator()
    evaluator.start()
    evaluator.add_global("c", ctx)
    evaluator.add_global("Q_", Q_)

    with pytest.raises(RuntimeError) as e:
        evaluator.eval("import os")
