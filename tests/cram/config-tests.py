def test_works():
    assert type(configs) is list
    assert len(configs) == 1

    assert "/simulation/N" in configs[0]
    assert configs[0]["/simulation/N"] == 20000
