import ast
from pathlib import Path

from fspathtree import fspathtree


def validate_config(
    config: fspathtree, validate_file: Path = Path("powerconf_validate.py")
):

    validate_source = validate_file.read_text()
    validate_ast = ast.parse(validate_source)
    validate_function_names = [
        node.name
        for node in ast.walk(validate_ast)
        if isinstance(node, ast.FunctionDef)
    ]
    validate_code = compile(validate_ast, "<string>", "exec")
    exec(validate_code)

    results = {}
    for fname in validate_function_names:
        code = fname + "(config)"
        try:
            exec(code)
            results[fname] = {"result": "pass"}
        except Exception as e:
            result = {"result": "fail", "exception": e}
            results[fname] = result

    return results
