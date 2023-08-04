# Based on Archipelago's NetUtils
# see https://github.com/ArchipelagoMW/Archipelago for copyright and license


from json import JSONEncoder
from typing import Any


__all__ = ["encode"]


def _scan_for_typed(obj: Any) -> Any:
    if isinstance(obj, tuple) and hasattr(obj, "_fields"):  # NamedTuple is not actually a parent class
        data = obj._asdict()
        data["class"] = obj.__class__.__name__
        return data
    if isinstance(obj, (tuple, list, set, frozenset)):
        return tuple(_scan_for_typed(o) for o in obj)
    if isinstance(obj, dict):
        return {key: _scan_for_typed(value) for key, value in obj.items()}
    return obj


_encode = JSONEncoder(
    ensure_ascii=False,
    check_circular=False,
    separators=(',', ':'),
).encode


def encode(obj: Any) -> str:
    return _encode(_scan_for_typed(obj))
