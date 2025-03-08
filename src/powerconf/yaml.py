import pathlib
from typing import List

from fspathtree import fspathtree

from . import loaders, rendering
from .pyyaml import dump, safe_load



def powerload(config_file: pathlib.Path) -> List[fspathtree]:
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
    config_renderer = rendering.ConfigRenderer()

    config_docs = loaders.yaml_all_docs(config_file)
    complete_configs = rendering.expand_partial_configs(config_docs)
    complete_configs = [
        rendering.load_includes(c, loaders.yaml) for c in complete_configs
    ]
    unrendered_configs = []
    for c in complete_configs:
        unrendered_configs += config_renderer.expand_batch_nodes(c)
    rendered_configs = []
    for c in unrendered_configs:
        rendered_configs.append(config_renderer.render(c))

    return rendered_configs
