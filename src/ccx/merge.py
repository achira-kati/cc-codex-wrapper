from typing import Any


def deep_merge(left: Any, right: Any) -> Any:
    """Merge `right` onto `left`. Dicts union, lists concat, scalars — right wins.

    On type mismatch between `left` and `right`, `right` wins.
    """
    if isinstance(left, dict) and isinstance(right, dict):
        out = dict(left)
        for key, rvalue in right.items():
            if key in out:
                out[key] = deep_merge(out[key], rvalue)
            else:
                out[key] = rvalue
        return out
    if isinstance(left, list) and isinstance(right, list):
        return list(left) + list(right)
    return right
