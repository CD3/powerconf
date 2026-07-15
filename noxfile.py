"""Nox sessions."""

import nox

python_versions = ["3.10", "3.11", "3.12", "3.13", "3.14"]
nox.needs_version = ">= 2021.6.6"
nox.options.sessions = ("tests",)


@nox.session(python=python_versions)
def tests(session: nox.Session) -> None:
    """Run the test suite."""
    session.install("uv")
    session.run("uv", "pip", "install", "-e", ".[dev]")
    session.run("pytest", *session.posargs)
