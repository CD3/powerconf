import contextlib
import hashlib
import json
import os
import pathlib
import typing

from fspathtree import fspathtree


def get_id(
    config: fspathtree,
    path_predicate: typing.Callable[[fspathtree], bool] = None,
):
    """
    Return a unique id for the given configuration object.

    @param path_predicate: a function that will be passed the path to each node
    in the tree and should return true if the path sould be included in the
    tree when creating the id. This is useful for removing config parameters
    that are expected to change, but don't chnge the actual configuration.
    """
    if path_predicate is None:

        def path_predicate(p):
            return True

    # make a copy of the config with only keys not in the strip list
    c = fspathtree()
    for p in config.get_all_leaf_node_paths(predicate=path_predicate):
        c[p] = str(config[p])

    text = json.dumps(c.tree, sort_keys=True).replace(" ", "")
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def apply_transform(
    config: fspathtree | typing.List[fspathtree],
    transform: typing.Callable[[fspathtree.PathType, typing.Any], typing.Any],
    predicate: typing.Callable[[fspathtree.PathType, typing.Any], typing.Any] = None,
):
    """
    Apply a transformation to configuration tree.

    Tree is modified in place.
    Transform is _ONLY_ applied to leaf nodes.


    @param transform: a function that accepts a path and node value, and returns the new value of the node.
    @param predicate: a function that accepst a path and node value, and returns True if the node should
                      have the transform apply. by default, all nodes have transform applied.
    """

    if type(config) is list:
        for i in range(len(config)):
            config[i] = apply_transform(config[i], transform, predicate)
    else:
        for p in config.get_all_leaf_node_paths(predicate=predicate):
            config[p] = transform(p, config[p])

    return config


@contextlib.contextmanager
def working_directory(path):
    path = pathlib.Path(path)
    path.mkdir(exist_ok=True, parents=True)
    last_dir = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(last_dir)
