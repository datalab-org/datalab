"""Middleware for cleaning incoming data.’"""

from functools import wraps

from bson import ObjectId
from flask import request


def clean_objectids_middleware(f):
    """Middleware to automatically clean ObjectIds in JSON queries."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.is_json:
            original_get_json = request.get_json

            def cleaned_get_json(*args, **kwargs):
                data = original_get_json(*args, **kwargs)
                if data:
                    return _clean_objectids_recursive(data)
                return data

            request.get_json = cleaned_get_json

        return f(*args, **kwargs)

    return decorated_function


def _clean_objectids_recursive(data):
    """Recursively cleans up malformed ObjectIds in the data."""
    if isinstance(data, dict):
        if "$oid" in data and len(data) == 1:
            return ObjectId(data["$oid"])
        else:
            return {k: _clean_objectids_recursive(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_clean_objectids_recursive(item) for item in data]
    else:
        return data
