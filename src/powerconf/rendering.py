import copy
import itertools
from os.path import normpath
from pathlib import Path
from typing import Any, Callable, List

import pystache
from fspathtree import fspathtree

from . import expressions, graphs, parsing, units

__local_Quantity = units.Q_


def expand_partial_configs(configs: List[fspathtree], include_base=False):
    """
    Give a list of configuration trees, treat the frist tree
    as a "base" configuration and all other trees as partial configurations
    that should be merged with the base config to create instances.

    @param include_base : if true, the base config will be included in the returned set.
    """
    assert len(configs) > 0

    if len(configs) == 1:
        return configs

    full_configs = []
    if include_base:
        full_configs.append(copy.deepcopy(configs[0]))
    for c in configs[1:]:
        full_configs.append(copy.deepcopy(configs[0]))
        full_configs[-1].update(c)

    return full_configs


def try_construct_quantity(
    obj: Any,
    is_quantity: Callable[[Any], bool] = None,
    quantity_class: Any = __local_Quantity,
):
    """
    Try to construct a pint.UnitRegistry().Quantity
    object from a given object, if the given looks like it would be
    a quantity.

    By default, an object is considered a quantity if it:
        - is a string,
        - begins with a numerical value,
        - does not throw an exception when passed to pint.UnitRegistry().Quantity(...) constructor

    @param is_quantity: a function returning true if the object should be considered a quantity. This allows the caller to provide
                        their logic to identify quantities.
    @param quantity_class : the class that should be used to construct quantities. pint cannot handle quantities from different
                            registries, so this allows the caller to provide the class they are uing.
    """

    if is_quantity is None:

        def f(obj: Any) -> bool:
            if type(obj) is not str:
                return False
            try:
                float(obj.strip().split(" ")[0])
            except Exception:
                return False
            try:
                quantity_class(obj.strip())
            except Exception:
                return False

            return True

        is_quantity = f

    if is_quantity(obj):
        return quantity_class(obj)
    else:
        return obj


def expand_variables(text: Any, template: str = "ctx['{name}']"):
    """
    Expand shell-style variables into python variables

    @param template: optional template string used for variable expantion. The variables
                     name will be inserted into the template using {VARNAME}. Default value
                     is "ctx['{name}']", which means we will have:

                    $x -> c['x']
                    ${x} -> c['x']
                    $/grid/x -> c['/grid/x']
                    ${/grid/x} -> c['/grid/x']

    """
    i = 0
    new_text = ""
    for tokens, start, end in parsing.variable.scan_string(text):
        new_text += text[i:start]
        i = end
        new_text += template.format(name=tokens["variable name"])
    new_text += text[i:]
    return new_text


def contains_expression(text: Any):
    """
    Returns true if a string contains expression.
    Supports passing not strings as arguments, in which
    case False is returned.
    """

    if type(text) is not str:
        return False

    results = parsing.expression.search_string(text)
    return len(results) > 0


def contains_variable(text: Any):
    """
    Returns true if a string contains a variable refernce.
    Supports passing not strings as arguments, in which
    case False is returned.
    """
    if type(text) is not str:
        return False

    results = parsing.variable.search_string(text)
    return len(results) > 0


def load_includes(config: fspathtree, loader):
    """
    Find all '@include' branches in the tree and load the branch from
    a file.

    @param config: the configuration tree to expand. If the tree does not include any '@include' leafs, it will not be changes.
    @param loader: a function that accepts a pathlib.Path argument and loads the contents of the file into an fspathtree that is returned.
    """
    for leaf in config.get_all_leaf_node_paths(
        predicate=lambda p, n: p.name == "@include"
    ):
        subtree = loader(Path(config[leaf]))
        subtree = load_includes(subtree, loader)
        config[leaf.parent] = subtree.tree

    return config


class ConfigRenderer:
    Quantity = units.Q_

    def __init__(self, expression_evaluator=None):
        if expression_evaluator is None:
            expression_evaluator = expressions.ExecExpressionEvaluator()

        self.expression_evaluator = expression_evaluator

    def expand_and_render(self, config):
        """Expand batch configurations and render each instance."""
        configs = self.expand_batch_nodes(config)
        for i in range(len(configs)):
            configs[i] = self.render(configs[i])

        return configs

    def expand_batch_nodes(self, config: fspathtree):
        """Expand @batch nodes in a configuration tree into multiple configuration trees."""
        configs = []

        batch_leaves = self._get_batch_leaves(config)

        for vals in itertools.product(
            *[config[leaf + "/@batch"] for leaf in batch_leaves.keys()]
        ):
            instance = copy.deepcopy(config)
            for i, leaf in enumerate(batch_leaves.keys()):
                instance[leaf] = vals[i]
            configs.append(instance)

        return configs

    def render(self, config: fspathtree, make_copy=True):
        """Render a configuration tree, constructing all quantities, expanding all variables, and evaluating all expressions."""
        # create a graph of the dependencies
        G = graphs.DependencyGraph()
        # add all leaf node paths as nodes of the graph
        G.add_nodes_from(config.get_all_leaf_node_paths())
        # draw edges between nodes representing dependencies.
        # edges point from a node to its dependency.
        # if a node has incomming edges, other nodes depend on it
        # if a node has outgoing edges, it depends on others.
        for node in list(G.nodes):
            variables = [
                fspathtree.PathType(r["variable name"])
                for r in parsing.variable.search_string(config[node])
            ]
            for v in variables:
                dep = fspathtree.PathType(
                    normpath(v if v.is_absolute() else node.parent / v)
                )
                G.add_edge(node, dep)
        # detect circular dependencies
        cycles = sorted(graphs.nx.simple_cycles(G))
        if len(cycles) > 0:
            msg = "Circular dependencies detected."
            for cycle in cycles:
                msg += "(" + " -> ".join(map(str, cycle)) + ")"
            raise RuntimeError(msg)

        # make a copy to work with

        if make_copy:
            rendered_config = copy.deepcopy(config)
        else:
            rendered_config = config

        rendered_config = self._construct_all_quantities(rendered_config)
        rendered_config = self._expand_all_variables(rendered_config)
        rendered_config = self._evaluate_all_expressions(rendered_config, G)

        return rendered_config

    def _evaluate_all_expressions(
        self, config: fspathtree, graph: graphs.DependencyGraph
    ):
        """Evaluate the expressions in a configuration tree, using a graph of the tree dependencies to determine the render order."""
        # We need to determine the order to evaluate the nodes of the config tree.
        # We have a graph that describes the dependencies. Each node is the graph is a leaf node
        # in the tree, and the edges represent dependencies between nodes.
        # Consider an example,
        #
        #          A        X
        #        /   \    /   \
        #       B    C   Y     Z
        #           / \ /
        #          D   E
        #
        # Assume all edges are directed DOWN.
        # B, D, E and Z then have no dependencies. All of their edges are "in" edges,
        # they have no "out" edges.
        #
        # With networkx we can easily get a list of all nodes with no dependencies, first
        # get the number of in and out edges for each node.
        out_degrees = dict(graph.out_degree)
        in_degrees = dict(graph.in_degree)
        # any nodes that have zero out edges (out_degrees = 0) have no dependencies, and we can go ahead and render these.
        config = self._evaluate_expressions(
            config,
            paths=map(
                lambda item: item[0],
                filter(lambda item: item[1] == 0, out_degrees.items()),
            ),
        )
        # Now we need to render nodes that have dependencies, but we need to determine the order that this can be
        # done first. In the above example, we can't evaluate A until B and C are evaluated. We can't evaluate C until D and E
        # are evaluated.
        #
        # With networkx, we can easily get a list of all ancestors of a node. For node E, this would be [C,Y,A,X]
        # Note: with the direction of our edges, an ancestor _depends_ on the node. So C is an ancestor of E, even
        # though it seems more natural to consider E the ancestor of C. If we wanted E to be the ancestor of C,
        # we would need to direct our edges to point from dependencies to dependents.

        # Find all root dependencies. those nodes that don't depend on any others, but are depended on by others
        # thse are all nodes with out_degrees == 0 and in_degrees > 0
        root_dependencies = list(
            filter(
                lambda k: in_degrees[k] > 0,
                filter(lambda k: out_degrees[k] == 0, out_degrees.keys()),
            )
        )

        # For each root node, get a list of all ancestors, and then find every path that connects the ancestor to the root.
        # in this example above, node E would have 4 ancestors, [C,Y,A,X]. And the list of paths connecting E to its ancestors
        # would be E -> C, E -> Y, E -> C -> A, and E -> Y -> X.
        # However, we can't simply take one of these paths and start evaluating nodes. If we tried to evaluate E -> C -> A for example,
        # we would get an error if B had not already been determined.
        #
        # What we really need to be able to do is find A and X, then work backward from there...
        #
        # Find all leaf node dependencies. These are nodes that only have dependencies, no dependents (out_degree > 0, in_nodes = 0)
        leaf_dependencies = list(
            filter(
                lambda k: in_degrees[k] == 0,
                filter(lambda k: out_degrees[k] > 0, out_degrees.keys()),
            )
        )
        # now get a set of paths that connect each leaf node to its children
        for leaf in leaf_dependencies:
            all_paths = []
            for d in graphs.nx.descendants(graph, leaf):
                all_paths += graphs.nx.all_simple_paths(graph, leaf, d)

            # node batches are sets of nodes that can all be rendered
            # at the same time.
            node_batches = [
                set(filter(lambda n: n is not None, nodes))
                for nodes in itertools.zip_longest(*all_paths)
            ]
            node_batches.reverse()
            for batch in node_batches[1:]:
                config = self._evaluate_expressions(config, paths=batch)

        return config

        for root in root_dependencies:
            all_chains = []
            for a in graphs.nx.ancestors(graph, root):
                all_chains += graphs.nx.all_simple_paths(graph, a, root)

        # get all paths in the graph that end on roots
        all_chains = []
        for root in root_dependencies:
            for a in graphs.nx.ancestors(graph, root):
                all_chains += graphs.nx.all_simple_paths(graph, a, root)
        # prune paths that are included in ohters,
        # i.e. we only want to keep paths from each root to it's
        # oldest ancestors.
        longest_chains = []
        for p1 in all_chains:
            save = True
            for p2 in all_chains:
                if p1 == p2:
                    continue
                if p2[-len(p1) :] == p1:
                    save = False
                    break
            if save:
                longest_chains.append(p1)

        # determine the order to evaluate dependencies.

        for chain in longest_chains:
            chain.reverse()  # paths start with oldest ancestor and end with root node.
            config = self._evaluate_expressions(config, paths=chain[1:])

        return config

    def _evaluate_expressions(self, config: fspathtree, paths: List[Any]):
        """Evaluate expression in the config at the paths listed. Uses as a utility function on _evaluate_all_expressions(...)"""
        for path in paths:
            if not contains_expression(config[path]):
                continue

            self.expression_evaluator.globals["ctx"] = config[path.parent]
            expressions = parsing.expression.search_string(config[path])
            if (
                len(expressions) == 1
                and "$" + expressions[0]["expression body"] == config[path]
            ):
                # the value of the element is a single expression with no surrounding text
                # we want to replace the expression with the evaluation
                e = expressions[0]
                value = self.expression_evaluator.eval(e["expression body"][1:-1])
                config[path] = value
            else:
                # we have more than one expression or the expression is surrounded by text
                # we want to evaluate each expression and replace it with a str of its value
                old_text = config[path]
                new_text = ""
                i = 0
                for tokens, start, end in parsing.expression.scan_string(old_text):
                    new_text += old_text[i:start]
                    i = end
                    new_text += str(
                        self.expression_evaluator.eval(tokens["expression body"][1:-1])
                    )
                new_text += old_text[i:]
                config[path] = new_text
        return config

    def _construct_all_quantities(self, config: fspathtree):
        """Replace strings in the tree representing quantities with pint.Quantity objects."""
        for path in config.get_all_leaf_node_paths():
            config[path] = try_construct_quantity(
                config[path], quantity_class=self.Quantity
            )
        return config

    def _expand_all_variables(
        self, config: fspathtree, template: str = "ctx['{name}']"
    ):
        """
        Expand all shell-style variables into python variables in the entire tree.
        """
        for path in config.get_all_leaf_node_paths():
            if type(config[path]) is str:
                config[path] = expand_variables(config[path])

        return config

    def _get_batch_leaves(self, config: fspathtree):
        """
        Return a list of keys in a fpathtree (nested dict/list) that are marked
        as batch.
        """
        batch_leaves = dict()
        for leaf in config.get_all_leaf_node_paths():
            if leaf.parent.parts[-1] == "@batch":
                batch_leaves[str(leaf.parent.parent)] = (
                    batch_leaves.get(str(leaf.parent.parent), 0) + 1
                )
        return batch_leaves


def render_mustache_template(template_text: str, ctx: fspathtree):
    """
    Render a Mustache template text string using the values in a context. The context can
    be a configuration tree that has been previously loaded and rendered with powerconf.
    """
    # check for keys in the template that are not in the config dict
    # and throw an exception if any are missing
    parse_tree = pystache.parse(template_text)
    missing_keys = list(
        filter(
            lambda item: item not in ctx,
            set(
                map(
                    lambda item: item.key,
                    filter(lambda item: type(item) is not str, parse_tree._parse_tree),
                )
            ),
        )
    )
    if len(missing_keys) > 0:
        msg = (
            "Required configuration parameters were missing. These parameters are present in the template, but were not given in the context: "
            + ", ".join(missing_keys)
        )
        raise RuntimeError(msg)

    # we have to pass a flat dict to pystache, so we generate
    # it inline here. also, Mustache uses a leading slash on a key to
    # identify the end of a section, so we can use absolute path, just
    # relative paths with respect to the root.
    rendered_text = pystache.render(
        template_text, {str(p)[1:]: ctx[p] for p in ctx.get_all_leaf_node_paths()}
    )

    return rendered_text


def render_mustache_template_file(
    template_file: Path, ctx: fspathtree, output_file: Path
):
    template_text = template_file.read_text()
    rendered_text = render_mustache_template(template_text, ctx)
    output_file.write_text(rendered_text)
