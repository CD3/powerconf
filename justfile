set positional-arguments


test *args:
  #! /bin/bash
  export SHELL=/bin/bash
  uv run pytest "$@"


make-readme:
  compudoc README.md.cd README.md --comment-line-pattern "<!--{{{{CODE}}-->"

publish:
  rm dist -rf
  uv build
  uv publish
