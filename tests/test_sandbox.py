def test_eval_with_no_interpolation():
    # ctx = {"grid": {"x": {"min": 0, "max": 10, "N": 101}},
    #                {"y": {"min": 0, "max": 10, "N": "(y/max - y/min)/res", "res": 0.1}}
    #       }
    ctx = {}

    # assert sandbox_eval("($/grid/x/max - $/grid/x/min)/($/grid/x/N - 1)", ctx) == "0.01"
    # assert sandbox_eval("($max - $min)/($N - 1)", ctx["/grid/x"]) == "0.01"

    # assert (
    #     sandbox_eval("(c[/grid/x/max]- c[/grid/x/min])/(c[/grid/x/N] - 1)", ctx)
    #     == "0.01"
    # )
    # assert sandbox_eval("(c[max] - c[min])/(c[N] - 1)", ctx["/grid/x"]) == "0.01"
