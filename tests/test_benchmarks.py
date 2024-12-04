import pytest

from powerconf import loaders, rendering


@pytest.mark.benchmark
def test_benchmark_chained_dependencies(benchmark):
    text = """
  a : 1
  b : $(${a}+1)
  c : $(${b}+1)
  d : $(${c}+1)
  e : $(${d}+1)
  f : $(${e}+1)
  g : $(${f}+1)
  h : $(${g}+1)
  i : $(${h}+1)
  j : $(${i}+1)
  k : $(${j}+1)
  """

    config = loaders.yaml(text)
    config_renderer = rendering.ConfigRenderer()
    config_renderer.render(config)
    assert config["b"] == "$(${a}+1)"

    benchmark(config_renderer.render, config)

    config = config_renderer.render(config)

    assert config["a"] == 1
    assert config["b"] == 2
    assert config["k"] == 11


@pytest.mark.benchmark
def test_benchmark_chained_dependencies_reverse(benchmark):
    text = """
  a : $(${b}+1)
  b : $(${c}+1)
  c : $(${d}+1)
  d : $(${e}+1)
  e : $(${f}+1)
  f : $(${g}+1)
  g : $(${h}+1)
  h : $(${i}+1)
  i : $(${j}+1)
  j : $(${k}+1)
  k : 1
  """

    config = loaders.yaml(text)
    config_renderer = rendering.ConfigRenderer()
    config_renderer.render(config)
    assert config["b"] == "$(${c}+1)"

    benchmark(config_renderer.render, config)

    config = config_renderer.render(config)

    assert config["a"] == 11
    assert config["b"] == 10
    assert config["k"] == 1
