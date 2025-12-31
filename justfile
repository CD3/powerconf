set positional-arguments


test *args:
  uv run nox "$@"


make-readme:
  compudoc README.md.cd README.md --comment-line-pattern "<!--{{{{CODE}}-->"

publish:
  rm dist -rf
  uv build
  uv publish

lint:
  uv run ruff check . --fix
