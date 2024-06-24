import hashlib
import json

from fspathtree import fspathtree


def get_id(config: fspathtree, strip_keys=None):
    """Return a unique id for the given configuration object."""
    if strip_keys is None:
        strip_keys = []
    # make a copy of the config with only keys not in the strip list
    c = fspathtree()

    def filt(path):
        if str(path) in strip_keys:
            return False
        return True

    # we use a filter on the get_all_leaf_node_paths(...) here for more flexability
    for p in config.get_all_leaf_node_paths(predicate=filt):
        c[p] = str(config[p])

    text = json.dumps(c.tree, sort_keys=True).replace(" ", "")
    return hashlib.md5(text.encode("utf-8")).hexdigest()
