set positional-arguments
test *args:
        poetry run pytest -s "$@"

pub:
  rm dist -r
  poetry publish --build
