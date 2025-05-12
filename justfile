set positional-arguments


test *args:
  #! /bin/bash
  export SHELL=/bin/bash
  uv run pytest "$@"


make-readme:
  compudoc README-template.md README.md

publish:
  rm dist -rf
  uv build
  uv publish
