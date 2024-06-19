import copy
import itertools
from typing import Any, Dict, List

import pint
from fspathtree import fspathtree

from . import parsing


class ConfigRenderer:
    def __init__(self, expression_evaluator=None):
        self.expression_evaluator = expression_evaluator
        self.ureg = pint.UnitRegistry()
        self.Quantity = self.ureg.Quantity

    def expand_batch_nodes(self, config: fspathtree):
        """Expand @batch nodes in a configuration tree into multiple configuration trees."""
        configs = []

        return configs

    def _evaluate_all_expressions(self, config: fspathtree):
        paths = list(
            filter(
                lambda p: self._contains_expression(config[p]),
                config.get_all_leaf_node_paths(),
            )
        )
        for path in paths:
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

    def evaluate_all_expressions_repeatedly(self):
        pass

    def _construct_all_quantities(self, config: fspathtree):
        """Replace strings in the tree representing quantities with pint.Quantity objects."""
        for path in config.get_all_leaf_node_paths():
            if type(config[path]) == str:
                try:
                    q = self.Quantity(config[path])
                    config[path] = q
                except:
                    pass

        return config

    def _expand_variables(self, text: Any, template: str = "ctx['{name}']"):
        """
        Expand shell-style variables into python variables

        ${x} -> c['x']
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

    def _expand_all_variables(
        self, config: fspathtree, template: str = "ctx['{name}']"
    ):
        """
        Expand all shell-style variables into python variables in the entire tree.
        """
        for path in config.get_all_leaf_node_paths():
            if type(config[path]) == str:
                config[path] = self._expand_variables(config[path])

        return config

    def _contains_expression(self, text: Any):
        if type(text) is not str:
            return False

        results = parsing.expression.search_string(text)
        return len(results) > 0

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

    def _expand_batch_nodes(self, config: fspathtree):
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
