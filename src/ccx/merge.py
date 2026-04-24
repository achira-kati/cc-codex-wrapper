import copy
from typing import Any


def deep_merge(left: Any, right: Any) -> Any:
    """Merge `right` onto `left`. Dicts union, lists concat, scalars — right wins.

    On type mismatch between `left` and `right`, `right` wins.

    The returned value is independent of both inputs: mutating the result
    never affects `left` or `right`.
    """
    if isinstance(left, dict) and isinstance(right, dict):
        out: dict[Any, Any] = {}
        for key, value in left.items():
            if key in right:
                out[key] = deep_merge(value, right[key])
            else:
                out[key] = copy.deepcopy(value)
        for key, value in right.items():
            if key not in left:
                out[key] = copy.deepcopy(value)
        return out
    if isinstance(left, list) and isinstance(right, list):
        return copy.deepcopy(left) + copy.deepcopy(right)
    return copy.deepcopy(right)
