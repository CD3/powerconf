set positional-arguments


test *args:
        rye test "$@"


make-readme:
  compudoc README-template.md README.md
