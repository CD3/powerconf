import itertools
import pathlib
import time
from typing import List

from fspathtree import fspathtree

from . import loaders, rendering
from .pyyaml import dump, safe_load
from .parallel_processing import mkmsg,BatchJobController

def config_renderer_server_func(link):
    config_renderer = rendering.ConfigRenderer()
    while True:
        msg = link.recv()
        if msg == "stop":
            break
        if msg['type'] == "expand_batch_nodes":
            res = config_renderer.expand_batch_nodes(msg['payload'])
            link.send(res)
        if msg['type'] == "render":
            res = config_renderer.render(msg['payload'])
            link.send(res)



def powerload(config_file: pathlib.Path, njobs = None) -> List[fspathtree]:
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
        return rendered_configs

    config_renderer_server = BatchJobController(config_renderer_server_func)
    jobs = list(map(lambda c: mkmsg("expand_batch_nodes",c), complete_configs))
    unrendered_config = list(itertools.chain(*config_renderer_server.run_jobs(jobs)))
    jobs = list(map(lambda c: mkmsg("render",c), unrendered_config))
    rendered_configs = config_renderer_server.run_jobs(jobs)
    config_renderer_server.stop()
    config_renderer_server.wait()
    return rendered_configs




