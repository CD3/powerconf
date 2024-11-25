import pathlib
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

        self.add_global("math", math)

        try:
            import numpy

            self.add_global("numpy", numpy)
        except:
            pass

        extension_file = pathlib.Path("powerconf_extensions.py")
        if extension_file.exists():
            try:
                import importlib

                spec = importlib.util.spec_from_file_location(
                    "powerconf_extensions", extension_file
                )
                powerconf_extensions = importlib.util.module_from_spec(spec)
                sys.modules["powerconf_extensions"] = powerconf_extensions
                spec.loader.exec_module(powerconf_extensions)
                for obj in filter(
                    lambda x: not x.startswith("__"), dir(powerconf_extensions)
                ):
                    self.add_global(obj, powerconf_extensions.__dict__[obj])

                self.add_global("powerconf_extensions", powerconf_extensions)
            except Exception as e:
                raise RuntimeError(
                    f"There was a problem loading the extensions file ({extension_file}). ERROR: {e}"
                )

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
