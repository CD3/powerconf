import pickle
import subprocess
import sys

from fspathtree import fspathtree


class ExpressionEvaluator:
    """A class for evaluting expressions in a separate environement."""

    def __init__(self):
        pass

    def start(self):
        pass

    def eval(self, text: str):
        pass

    def stop(self):
        pass


class ExecExpressionEvaluator(ExpressionEvaluator):
    """A class for evaluating expressions using the builtin exec(). BE CAREFUL!"""

    def __init__(self):
        self.globals = {}
        self.locals = {}
        self.token = "_configurator_xyz"

        import math

        import numpy

        self.add_global("numpy", numpy)
        self.add_global("math", math)

    def add_global(self, name, obj):
        self.globals[name] = obj

    def eval(self, text: str):
        for forbidden_text in ["import", "open"]:
            if forbidden_text in text.replace(" ", ""):
                raise RuntimeError(
                    f"Expressions are not allowed to contain the text '{forbidden_text}'."
                )
        exec(f"{self.token}_result = " + text, self.globals, self.locals)
        return self.locals[self.token + "_result"]
