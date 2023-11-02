import contextlib
import io
import json
import re
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, TypeVar, cast

PARSE_DATE_FIELDS_MAX_DEPTH = 3
PARSE_DATE_FIELDS_KEY_SUFFIX = 'At'

ListOrDict = TypeVar('ListOrDict', List, Dict)
T = TypeVar('T')


def ignore_docs(method: T) -> T:
    """Mark that a method's documentation should not be rendered. Functionally, this decorator is a noop."""
    return method


@ignore_docs
def filter_out_none_values_recursively(dictionary: Dict) -> Dict:
    """Return copy of the dictionary, recursively omitting all keys for which values are None."""
    return cast(dict, _filter_out_none_values_recursively_internal(dictionary))


@ignore_docs
def _filter_out_none_values_recursively_internal(
    dictionary: Dict,
    remove_empty_dicts: Optional[bool] = None,
) -> Optional[Dict]:
    """Recursively filters out None values from a dictionary.

    Unfortunately, it's necessary to have an internal function for the correct result typing,
    without having to create complicated overloads
    """
    result = {}
    for k, v in dictionary.items():
        if isinstance(v, dict):
            v = _filter_out_none_values_recursively_internal(v, remove_empty_dicts is True or remove_empty_dicts is None)
        if v is not None:
            result[k] = v
    if not result and remove_empty_dicts:
        return None
    return result


@ignore_docs
def is_content_type_json(content_type: str) -> bool:
    """Check if the given content type is JSON."""
    return bool(re.search(r'^application/json', content_type, flags=re.IGNORECASE))


@ignore_docs
def is_content_type_xml(content_type: str) -> bool:
    """Check if the given content type is XML."""
    return bool(re.search(r'^application/.*xml$', content_type, flags=re.IGNORECASE))


@ignore_docs
def is_content_type_text(content_type: str) -> bool:
    """Check if the given content type is text."""
    return bool(re.search(r'^text/', content_type, flags=re.IGNORECASE))


@ignore_docs
def is_file_or_bytes(value: Any) -> bool:
    """Check if the input value is a file-like object or bytes.

    The check for IOBase is not ideal, it would be better to use duck typing,
    but then the check would be super complex, judging from how the 'requests' library does it.
    This way should be good enough for the vast majority of use cases, if it causes issues, we can improve it later.
    """
    return isinstance(value, (bytes, bytearray, io.IOBase))


@ignore_docs
def json_dumps(obj: Any) -> str:
    """Dump JSON to a string with the correct settings and serializer."""
    return json.dumps(obj, ensure_ascii=False, indent=2, default=str)


@ignore_docs
def maybe_extract_enum_member_value(maybe_enum_member: Any) -> Any:
    """Extract the value of an enumeration member if it is an Enum, otherwise return the original value."""
    if isinstance(maybe_enum_member, Enum):
        return maybe_enum_member.value
    return maybe_enum_member


@ignore_docs
def parse_date_fields(data: ListOrDict, max_depth: int = PARSE_DATE_FIELDS_MAX_DEPTH) -> ListOrDict:
    """Recursively parse date fields in a list or dictionary up to the specified depth."""
    if max_depth < 0:
        return data

    if isinstance(data, list):
        return [parse_date_fields(item, max_depth - 1) for item in data]

    if isinstance(data, dict):
        def parse(key: str, value: object) -> object:
            parsed_value = value
            if key.endswith(PARSE_DATE_FIELDS_KEY_SUFFIX) and isinstance(value, str):
                with contextlib.suppress(ValueError):
                    parsed_value = datetime.strptime(value, '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=timezone.utc)
            elif isinstance(value, dict):
                parsed_value = parse_date_fields(value, max_depth - 1)
            elif isinstance(value, list):
                parsed_value = parse_date_fields(value, max_depth)  # type: ignore # mypy doesn't work with decorators and recursive calls well
            return parsed_value

        return {key: parse(key, value) for (key, value) in data.items()}

    return data
