set positional-arguments


test *args:
        rye run pytest -s "$@"


make-readme:
  compudoc README-template.md README.md
