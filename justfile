set positional-arguments := true

test *args:
    uv run nox "$@"

pytest *args:
    uv run pytest "$@"

make-readme:
    uv run compudoc README.md.cd README.md --comment-line-pattern "<!--{{{{CODE}}-->"

publish:
    rm dist -rf
    uv build
    uv publish

lint:
    uv run ruff check . --fix
