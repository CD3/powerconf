set positional-arguments
test *args:
        poetry run pytest -s "$@"

pub:
  rm dist -rf
  poetry publish --build
