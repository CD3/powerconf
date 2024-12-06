import copy
import importlib
import multiprocessing
import os
import pathlib
import subprocess
import sys
from pathlib import Path
from typing import Annotated, List

import rich
import typer
from fspathtree import fspathtree

import powerconf

from . import loaders, rendering, utils, yaml

app = typer.Typer()

console = rich.console.Console()
error_console = rich.console.Console(stderr=True)

__version__ = importlib.metadata.version("powerconf")
state = {"verbose": 0}


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


@app.callback()
def main():
    """
    The `powerconf` command is a CLI for the powerconf python module. It allows you to read
    a configuration file, evaluate all expression, expand all batch nodes, etc, and write
    the "rendered" configurations to a file(s).
    """


@app.command()
def version():
    """
    Print the version number.
    """
    console.print(f"version: {__version__}")


@app.command()
def render(config_file: Path, template_file: Path, output: Path):
    """
    Read a powerconf-enabled configuration file and write a rendered configuration file.

    The rendered file(s) will be generated by rendering the template with each
    configuration instance as a context.
    """
    configs = yaml.powerload(config_file)

    if len(configs) == 1:
        # configuration expands into a single instance
        if output == template_file:
            raise RuntimeError(
                "Output file and template file are the same. This would overwrite the template file."
            )
        rendering.render_mustache_template_file(template_file, configs[0], output)
    else:
        output.mkdir(exist_ok=True, parents=True)
        for config in configs:
            _id = utils.get_id(config)
            output_file_suffix = template_file.suffix
            output_file_basename = template_file.with_suffix("")
            if template_file.suffix in [".template", ".tpl"]:
                output_file_suffix = output_file_basename.suffix
                output_file_basename = output_file_basename.with_suffix("")
            output_filename = output_file_basename.name + "-" + _id + output_file_suffix
            rendering.render_mustache_template_file(
                template_file, config, output / output_filename
            )


@app.command()
def print_instances(config_file: Path):
    """
    Print instances of configuration trees generated from the config.
    """
    configs = yaml.powerload(config_file)
    configs = utils.apply_transform(
        configs, lambda p, n: str(n), lambda p, n: hasattr(n, "magnitude")
    )
    console.print("\n---\n".join(map(lambda c: yaml.dump(c.tree), configs)))


def run_config(config, tool):
    with console.capture() as capture:

        tool_config = config[f"/powerconf-run/{tool}"]

        template_config_file = tool_config.get("template_config_file", None)
        rendered_config_file = tool_config.get("rendered_config_file", None)

        if template_config_file is not None:
            template_config_file = Path(template_config_file).absolute()
        if rendered_config_file is not None:
            rendered_config_file = Path(rendered_config_file)

        working_directory = Path(tool_config.get("working_directory", ".")).absolute()
        with utils.working_directory(working_directory):
            if template_config_file is not None:
                if not rendered_config_file.parent.exists():
                    rendered_config_file.parent.mkdir(exist_ok=True, parents=True)
                rendering.render_mustache_template_file(
                    template_config_file, config, rendered_config_file
                )

            for command in tool_config["command"]:
                wd = working_directory
                cmd = command
                if hasattr(command, "tree"):
                    cmd = command["command"]
                    wd = Path(command.get("working_directory", ".")).absolute()
                with utils.working_directory(wd):
                    console.print(f"Running Command: {cmd}")
                    console.print(f"Working Directory: {wd}")
                    result = subprocess.run(
                        cmd,
                        shell=True,
                        stderr=subprocess.STDOUT,
                        stdout=subprocess.PIPE,
                    )
                    console.print(f"Command '{cmd}' Finished")
                    console.print(f"Return Code: {result.returncode}")
                    console.print(f"Output")
                    console.print(f"vvvvvvvvvvvvvvvvvvvvvvvv")
                    console.print(result.stdout.decode())
                    console.print(f"^^^^^^^^^^^^^^^^^^^^^^^^")
                    console.print()
    return capture.get()


@app.command()
def run(
    tool: Annotated[str, typer.Argument(help="The tool (i.e. model) to run.")],
    config_file: Annotated[
        pathlib.Path,
        typer.Argument(
            help="Confuration file. Includes model configuration and configuration for `powerconf run`."
        ),
    ],
):

    configs = yaml.powerload(config_file)
    # check that all configs have a section for the given tool.
    for i, config in enumerate(configs):
        if f"/powerconf-run/{tool}" not in config:
            error_console.print(
                f"No 'powerconf-run/{tool}' key in config instance {i} of {config_file}. If you run `powerconf print-instance {config_file}`, each instance should have a `powerconf-run/{tool}` branch."
            )
            raise typer.Exit(code=1)
        if (
            f"/powerconf-run/{tool}/rendered_config_file" in config
            and f"/powerconf-run/{tool}/template_config_file" not in config
        ):
            error_console.print(
                f"Invalid configuration. `powerconf-run/{tool}/rendered_config_file` was found but `powerconf-run/{tool}/template_config_file` was not. If one is given, both must be given."
            )
            raise typer.Exit(code=2)

        if (
            f"/powerconf-run/{tool}/template_config_file" in config
            and f"/powerconf-run/{tool}/rendered_config_file" not in config
        ):
            error_console.print(
                f"Invalid configuration. `powerconf-run/{tool}/template_config_file` was found but `powerconf-run/{tool}/rendered_config_file` was not. If one is given, both must be given."
            )
            raise typer.Exit(code=2)

    console.print("Running job for each config in parallel.")
    console.print("Output from commands will be printed as they finish.")
    with multiprocessing.Pool() as pool:
        for output in pool.starmap(run_config, [(config, tool) for config in configs]):
            print(output)
            print()
