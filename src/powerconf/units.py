import pint

# enable support for loading temperature quantities from a string.
# i.e. '37 degC'
ureg = pint.UnitRegistry(autoconvert_offset_to_baseunit=True)
Q_ = ureg.Quantity
