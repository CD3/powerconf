import inspect
import itertools
import pathlib
import textwrap
from types import FunctionType
from typing import List

from fspathtree import fspathtree

from . import loaders, rendering, utils
from .parallel_processing import BatchJobController, mkmsg


def _get_function_name(src):
    """
    Given the source code for a function, extract the function's name.
    """
    # a dumb first cut
    name = src.strip()
    if not name.startswith("def "):
        raise RuntimeError(
            f"Cannot determine the name of function from definition\n{src}"
        )
    name = name[3:].strip()
    if "(" not in name:
        raise RuntimeError(
            f"Cannot determine the name of function from definition\n{src}"
        )

    return name[: name.find("(")]


def config_renderer_server_func(link):
    config_renderer = rendering.ConfigRenderer()
    while True:
        msg = link.recv()
        if msg == "stop":
            break
        if msg["type"] == "expand_batch_nodes":
            res = config_renderer.expand_batch_nodes(msg["payload"])
            link.send(res)
        if msg["type"] == "render":
            res = config_renderer.render(msg["payload"])
            link.send(res)
        if msg["type"] == "transform":
            config = msg["payload"]["config"]
            transform_src = msg["payload"]["transform"]
            transform_name = _get_function_name(transform_src)
            exec(transform_src)
            exec(f"""utils.apply_transform(config, {transform_name})""")
            link.send(config)


def powerload(
    config_file: pathlib.Path, /, njobs=None, transform=None
) -> List[fspathtree]:
    """
    Load a set of configurations from a YAML files.

    If the file contains multiple documents, the first document is assumed to be
    a base configuration with all following documents being partial configs that are applied
    on top of the base configuration. This makes it easy define multiple configuration
    that only differ by a few settings in a single file.

    If configuration tree includes '@batch' nodes, these will be expanded into multiple configurations.

    For each configuration that is generated after considering all YAML documents and expanding all
    batch parameters, expressions are evaluated. This may include variable references to other configuration
    parameter.

    This is your one-stop-shop for loading powerconfigs from YAML files.
    """
    # the user may want to pass in the filename as a string (ignoring our type hint)
    # so let's just make sure we have a pathlib.Path
    config_file = pathlib.Path(config_file)

    config_docs = loaders.yaml_all_docs(config_file)
    complete_configs = rendering.expand_partial_configs(config_docs)
    complete_configs = [
        rendering.load_includes(c, loaders.yaml) for c in complete_configs
    ]

    # default to legacy serial behavior
    if njobs is None or njobs < 1:
        njobs = 1

    if njobs == 1:
        config_renderer = rendering.ConfigRenderer()
        unrendered_configs = list(
            itertools.chain(
                *list(map(config_renderer.expand_batch_nodes, complete_configs))
            )
        )
        rendered_configs = list(map(config_renderer.render, unrendered_configs))
        if transform is not None:
            utils.apply_transform(rendered_configs, transform)
        return rendered_configs

    if transform is not None:
        if not isinstance(transform, FunctionType):
            raise RuntimeError("Transforms can only be function types")
        # can't send a function through the pipe, so we need are sending the source code instead
        # and then we'll exec it on the other end. What could go wrong...
        transform_src = textwrap.dedent("".join(inspect.getsourcelines(transform)[0]))
        if not transform_src.startswith("def"):
            raise RuntimeError(
                "Transforms can only be free functions when using parallel processing"
            )

    config_renderer_server = BatchJobController(config_renderer_server_func)
    jobs = list(map(lambda c: mkmsg("expand_batch_nodes", c), complete_configs))
    unrendered_config = list(itertools.chain(*config_renderer_server.run_jobs(jobs)))
    jobs = list(map(lambda c: mkmsg("render", c), unrendered_config))
    rendered_configs = config_renderer_server.run_jobs(jobs)
    if transform:
        jobs = list(
            map(
                lambda c: mkmsg("transform", {"transform": transform_src, "config": c}),
                rendered_configs,
            )
        )
        rendered_configs = config_renderer_server.run_jobs(jobs)
    config_renderer_server.stop()
    config_renderer_server.wait()
    return rendered_configs
