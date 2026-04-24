from ccx.merge import deep_merge


def test_disjoint_dicts_union():
    assert deep_merge({"a": 1}, {"b": 2}) == {"a": 1, "b": 2}


def test_right_wins_on_scalar_conflict():
    assert deep_merge({"x": "left"}, {"x": "right"}) == {"x": "right"}


def test_nested_dicts_merge_recursively():
    left = {"server": {"command": "npx", "args": ["-y"]}}
    right = {"server": {"env": {"TOKEN": "x"}}}
    assert deep_merge(left, right) == {
        "server": {"command": "npx", "args": ["-y"], "env": {"TOKEN": "x"}}
    }


def test_lists_concatenate():
    assert deep_merge([1, 2], [3, 4]) == [1, 2, 3, 4]


def test_lists_inside_dicts_concatenate():
    left = {"hooks": [{"matcher": "Bash"}]}
    right = {"hooks": [{"matcher": "Edit"}]}
    assert deep_merge(left, right) == {
        "hooks": [{"matcher": "Bash"}, {"matcher": "Edit"}]
    }


def test_type_mismatch_right_wins():
    assert deep_merge({"x": [1]}, {"x": "string"}) == {"x": "string"}


def test_none_on_either_side_right_wins():
    assert deep_merge({"x": 1}, {"x": None}) == {"x": None}
    assert deep_merge({"x": None}, {"x": 1}) == {"x": 1}


def test_empty_inputs():
    assert deep_merge({}, {"a": 1}) == {"a": 1}
    assert deep_merge({"a": 1}, {}) == {"a": 1}
    assert deep_merge({}, {}) == {}
