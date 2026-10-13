"""Safe serialization and normalization helpers; standard library only."""
from datetime import date, datetime
import json
import math


def to_jsonable(value, depth=0):
    if depth > 7:
        return str(value)[:300]
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(k)[:100]: to_jsonable(v, depth + 1) for k, v in list(value.items())[:100]}
    if isinstance(value, (list, tuple, set)):
        return [to_jsonable(v, depth + 1) for v in list(value)[:100]]
    # pandas/numpy scalars commonly expose item()
    try:
        item = value.item()
        if item is not value:
            return to_jsonable(item, depth + 1)
    except Exception:
        pass
    return str(value)[:300]


def as_dict(value):
    return value if isinstance(value, dict) else {}


def first_present(mapping, *keys, default=None):
    mapping = as_dict(mapping)
    for key in keys:
        value = mapping.get(key)
        if value is not None and value != "":
            return value
    return default


def dumps(value):
    return json.dumps(to_jsonable(value), ensure_ascii=False, separators=(",", ":"), allow_nan=False)
