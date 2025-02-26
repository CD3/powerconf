set positional-arguments


test *args:
        uv run pytest "$@"


make-readme:
  compudoc README-template.md README.md
