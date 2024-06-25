import pint
import pyparsing
import pytest
import yaml
from fspathtree import fspathtree

from powerconf import rendering

ureg = pint.UnitRegistry()
Q_ = ureg.Quantity


def test_quantity_construction():
    x = rendering.try_construct_quantity(" 4.5 cm")
    assert x.magnitude == pytest.approx(4.5)

    x = rendering.try_construct_quantity(4)
    assert x == 4

    x = rendering.try_construct_quantity(4.5)
    assert x == pytest.approx(4.5)

    x = rendering.try_construct_quantity("quant")
    assert x == "quant"

    x = rendering.try_construct_quantity("quad")
    assert x == "quad"
    x = rendering.try_construct_quantity("quad", is_quantity=lambda s: True)
    assert x.magnitude == pytest.approx(1)

    with pytest.raises(Exception) as e:
        x = rendering.try_construct_quantity("lskjdf", is_quantity=lambda s: True)

    x = rendering.try_construct_quantity(" 4.5 cm")
    assert type(x) != Q_
    x = rendering.try_construct_quantity(" 4.5 cm", quantity_class=Q_)
    assert type(x) == Q_
