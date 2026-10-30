"""Explicit, bounded JSON-tree presentation transforms (not secret detection)."""

import math
from collections.abc import Collection
from typing import cast


def unwrap_data(value: object, *, data_key: str = "data") -> object:
    if type(value) is dict and set(value) == {data_key}:
        return value[data_key]
    return value


def strip_fields(value: object, *, names: Collection[str], max_depth: int = 64, max_items: int = 10000) -> object:
    if type(max_depth) is not int or max_depth < 0 or type(max_items) is not int or max_items < 1:
        raise ValueError("Invalid traversal bounds")
    if any(type(name) is not str for name in names):
        raise ValueError("Excluded names must be strings")
    excluded = set(names)
    ancestors: set[int] = set()
    count = 0

    def walk(item: object, depth: int) -> object:
        nonlocal count
        count += 1
        if count > max_items or depth > max_depth:
            raise ValueError("JSON traversal limit exceeded")
        if item is None or type(item) in (str, bool, int):
            return item
        if type(item) is float and math.isfinite(item):
            return item
        if type(item) not in (dict, list):
            raise ValueError("Expected a finite JSON tree")
        if id(item) in ancestors:
            raise ValueError("Cyclic JSON tree")
        ancestors.add(id(item))
        try:
            if type(item) is list:
                return [walk(child, depth + 1) for child in item]
            result = {}
            for key, child in cast(dict[object, object], item).items():
                if type(key) is not str:
                    raise ValueError("JSON keys must be strings")
                # Validate excluded values too, so the input contract remains deterministic.
                converted = walk(child, depth + 1)
                if key not in excluded:
                    result[key] = converted
            return result
        finally:
            ancestors.remove(id(item))

    return walk(value, 0)
