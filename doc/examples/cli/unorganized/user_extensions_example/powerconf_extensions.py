from tissue_properties.optical.absorption_coefficient import mainster


def fto(q, unit):
    return q.to(unit).magnitude


def ito(q, unit):
    return int(q.to(unit).magnitude)


_RPE = mainster.RPE()
_Choroid = mainster.Choroid()


def RPE(wavelength):
    # we can't mix units from two different systems, so we have to turn wavelength
    # into a string to pass it in.
    return _RPE(str(wavelength))
