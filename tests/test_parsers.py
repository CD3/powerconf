import pyparsing
import pytest

from powerconf import parsing


def test_variable():
    result = parsing.variable.parse_string("$x")
    assert result["variable name"] == "x"
    result = parsing.variable.parse_string("$xyz")
    assert result["variable name"] == "xyz"
    result = parsing.variable.parse_string("$grid/x/min")
    assert result["variable name"] == "grid/x/min"
    result = parsing.variable.parse_string("$x_q")
    assert result["variable name"] == "x_q"

    with pytest.raises(pyparsing.exceptions.ParseException):
        parsing.variable.parse_string("x$x")

    with pytest.raises(pyparsing.exceptions.ParseException):
        parsing.variable.parse_string("$ x")

    result = parsing.variable.parse_string("${x}")
    assert result["variable name"] == "x"
    result = parsing.variable.parse_string("${/grid/x/min}")
    assert result["variable name"] == "/grid/x/min"
    result = parsing.variable.parse_string("${/grid/x/min val}")
    assert result["variable name"] == "/grid/x/min val"

    with pytest.raises(pyparsing.exceptions.ParseException):
        parsing.variable.parse_string("$ {x}")


def test_expressions():
    result = parsing.expression.parse_string("$(1 + 1)")
    assert result["expression body"] == "(1 + 1)"

    with pytest.raises(pyparsing.exceptions.ParseException):
        result = parsing.expression.parse_string("$ (1 + 1)")

    result = parsing.expression.parse_string("$( $x + $y)")
    assert result["expression body"] == "( $x + $y)"

    result = parsing.expression.parse_string("$( $x + ( 1 + 2 + $y))")
    assert result["expression body"] == "( $x + ( 1 + 2 + $y))"

    # result = parsing.expression_body.parse_string(result["expression body"])


def test_expressions_with_filters():
    result = parsing.expression.parse_string("$( $x + $y | to('cm') )")
    assert result["expression body"] == "( $x + $y | to('cm') )"

    code_and_filter = result["expression body"][1:-1].split("|")

    assert code_and_filter[0] == " $x + $y "
    assert code_and_filter[1] == " to('cm') "
