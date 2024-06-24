from powerconf import readers, rendering


def test_yaml_multi_docs():
    text = """
one: 1
two: 2
---
three : 3
    """

    configs = readers.load_yaml_docs(text)

    assert len(configs) == 2
    assert "one" in configs[0]
    assert "two" in configs[0]
    assert "three" not in configs[0]
    assert "three" in configs[1]
