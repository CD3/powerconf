from pathlib import Path
from typing import Annotated, List

import rich
import typer
import yaml
from fspathtree import fspathtree

from . import rendering

app = typer.Typer()
console = rich.console.Console()


def load_config(config_file: Path):
    """load config from a file."""
    configs = []
    if not config_file.exists():
        raise typer.Exit(f"File '{config_file}' not found.")
    config_text = config_file.read_text()
    config_docs = config_text.split("---")
    for doc in config_docs:
        config = fspathtree(yaml.safe_load(doc))
        configs.append(config)

    return configs


@app.command()
def render(config_file: Path, output: Path = None):
    if output is None:
        output = config_file.parent / (config_file.name + ".rendered")
    configs = load_config(config_file)
    config_renderer = rendering.ConfigRenderer()
    rendered_configs = []
    for config in configs:
        config = config_renderer.expand_and_render(config)
        rendered_configs += config
    if len(rendered_configs) == 1:
        output.write_text(yaml.dump(rendered_configs[0].tree))


@app.command()
def help():
    print(
        """
The `powerconf` command is a CLI for the powerconf python module. It allows you to read
a configuration file, evaluate all expression, expand all batch nodes, etc, and write
the "rendered" configurations to a file(s).
"""
    )
