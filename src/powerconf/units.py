import pint

# enable support for loading temperature quantities from a string.
# i.e. '37 degC'
ureg = pint.UnitRegistry(autoconvert_offset_to_baseunit=True)
Q_ = ureg.Quantity


def make_quantity(qstr):
    """
    Make a quantity from a string.

    For _most_ quantity strings we can just do Q_(qstr). However,
    it does not work for offset units.
    """
    v, u = qstr.split(maxsplit=1)
    v = float(v)
    u = u.strip()
    # handle inverse units that are given as the
    # value divided by a unit. i.e. "10 / s"
    # is "10 1/s"
    if len(u) > 0 and u[0] == "/":
        u = "1" + u
    return Q_(v, u)
