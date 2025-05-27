def validate_max_greater_than_min(config):
    assert (
        config["/simulation/grid/x/max"] > config["/simulation/grid/x/min"]
    ), "x/min must be less than x/max"
    assert (
        config["/simulation/grid/y/max"] > config["/simulation/grid/y/min"]
    ), "y/min must be less than y/max"
