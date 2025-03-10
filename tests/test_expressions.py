import pint
import pytest
from fspathtree import fspathtree

from powerconf import expressions

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

    evaluator.eval("numpy.exp( (c['/grid/x/max'] - c['/grid/x/min']) / Q_(10,'cm') )")
    assert dx.magnitude == 0.05

    evaluator.stop()


def test_expression_exceptions():
    with pytest.raises(expressions.ExpressionError) as e:
        raise expressions.ExpressionError("There was a problem.")

    assert e.value.args[0] == "There was a problem."

    with pytest.raises(expressions.ExpressionError) as e:
        try:
            exec("x = (a")
        except Exception as ee:
            raise expressions.ExpressionError(f"There was a problem: {ee}.")

    assert (
        e.value.args[0]
        == "There was a problem: '(' was never closed (<string>, line 1)."
    )


def test_expression_evaluator_bad_text():
    ctx = fspathtree()
    evaluator = expressions.ExecExpressionEvaluator()
    evaluator.start()
    evaluator.add_global("c", ctx)
    evaluator.add_global("Q_", Q_)

    with pytest.raises(RuntimeError) as e:
        evaluator.eval("import os")

    assert (
        e.value.args[0] == "Expressions are not allowed to contain the text 'import'."
    )


def test_expression_evaluator_with_filter():
    ctx = fspathtree()
    ctx["/grid/x/min"] = Q_(0, "cm")
    ctx["/grid/x/max"] = Q_(10, "cm")
    ctx["/grid/x/N"] = Q_(101, "")

    evaluator = expressions.ExecExpressionEvaluator()
    evaluator.start()
    evaluator.add_global("c", ctx)
    evaluator.add_global("Q_", Q_)
    evaluator.add_global("magnitude", lambda q: q.magnitude)
    evaluator.add_global("divide", lambda a, b: a / b)
    dx = evaluator.eval(
        "(c['/grid/x/max'] - c['/grid/x/min']) / (c['/grid/x/N']-1) | magnitude"
    )
    assert dx == 0.1
    dx = evaluator.eval(
        "(c['/grid/x/max'] - c['/grid/x/min']) / (c['/grid/x/N']-1) | magnitude(_1) | divide(2,_1)"
    )
    assert dx == 20

    evaluator.stop()


def test_expression_evaluator_with_exceptions():
    ctx = fspathtree()
    ctx["/grid/x/min"] = Q_(0, "cm")
    ctx["/grid/x/max"] = Q_(10, "cm")
    ctx["/grid/x/N"] = Q_(101, "")

    evaluator = expressions.ExecExpressionEvaluator()
    evaluator.start()
    evaluator.add_global("c", ctx)
    evaluator.add_global("Q_", Q_)
    evaluator.add_global("magnitude", lambda q: q.magnitude)
    evaluator.add_global("divide", lambda a, b: a / b)
    with pytest.raises(expressions.ExpressionError) as e:
        x = evaluator.eval("(1 + 2/3")
    assert e.value.args[0].startswith(
        "An exception was thrown while evaluating expression '(1 + 2/3'.\n"
    )
    assert "SyntaxError" in e.value.args[0]
    assert "'(' was never closed" in e.value.args[0]

    x = evaluator.eval("(1 + 2)/3")
    assert x == 1

    with pytest.raises(expressions.ExpressionError) as e:
        x = evaluator.eval("(1 + 2)/3 | missing")

    assert e.value.args[0].startswith(
        "An exception was thrown while evaluating expression ' missing(_configurator_xyz_result)' (generated by filter ' missing' in '(1 + 2)/3 | missing').\n"
    )
    assert "NameError" in e.value.args[0]
    assert "name 'missing' is not defined" in e.value.args[0]

    evaluator.stop()
