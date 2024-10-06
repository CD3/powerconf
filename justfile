set positional-arguments
test *args:
        rye run pytest -s "$@"

