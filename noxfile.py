"""Nox sessions."""

import nox

python_versions = ["3.12"]
nox.needs_version = ">= 2021.6.6"
nox.options.sessions = ("tests", "lint")


@nox.session(python=python_versions)
def tests(session: nox.Session) -> None:
    """Run the test suite."""
    session.install("uv")
    session.run("uv", "pip", "install", "-e", ".", "--group", "dev")
    session.run("pytest", *session.posargs)


@nox.session
def lint(session: nox.Session) -> None:
    """Run the linter."""
    session.install("uv")
    session.run("uv", "pip", "install", "-e", ".", "--group", "dev")
    session.run("ruff", "check", ".", "--fix")
    session.run("ruff", "check", ".")
