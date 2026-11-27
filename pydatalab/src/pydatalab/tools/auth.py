"""Shared authentication helpers for tool launches and provider routes."""

from urllib.parse import urlsplit

from flask import request
from pydantic import AnyHttpUrl, TypeAdapter

from pydatalab.config import CONFIG, is_loopback_host

HTTP_URL_ADAPTER = TypeAdapter(AnyHttpUrl)


def validated_external_tool_url(
    value: str,
    *,
    allow_insecure_http: bool,
    require_empty_query_and_fragment: bool = False,
) -> str:
    """Return a validated browser-facing URL for an external tool handoff."""
    validated_url = str(HTTP_URL_ADAPTER.validate_python(value))
    parsed_url = urlsplit(validated_url)
    if parsed_url.username is not None or parsed_url.password is not None:
        raise ValueError("External tool URLs cannot contain credentials")
    if require_empty_query_and_fragment and (parsed_url.query or parsed_url.fragment):
        raise ValueError("External tool callback URLs cannot contain a query or fragment")
    if parsed_url.scheme == "https":
        return validated_url
    if parsed_url.scheme == "http" and (
        is_loopback_host(parsed_url.hostname) or allow_insecure_http
    ):
        return validated_url
    raise ValueError("External tool URLs must use HTTPS except on loopback hosts")


def _normalized_origin(value: str) -> tuple[str, str, int] | None:
    """Normalize an HTTP origin for strict comparisons."""
    try:
        parsed = urlsplit(value)
        if (
            parsed.scheme.lower() not in {"http", "https"}
            or parsed.hostname is None
            or parsed.username is not None
            or parsed.password is not None
        ):
            return None
        port = parsed.port
    except ValueError:
        return None

    scheme = parsed.scheme.lower()
    if port is None:
        port = 443 if scheme == "https" else 80
    return scheme, parsed.hostname.rstrip(".").lower(), port


def _is_loopback_origin(origin: tuple[str, str, int] | None) -> bool:
    return origin is not None and is_loopback_host(origin[1])


def request_origin_is_allowed() -> bool:
    """Return whether the request origin is trusted by this datalab deployment."""
    supplied_origin = request.headers.get("Origin")
    if supplied_origin is None:
        return False

    origin = _normalized_origin(supplied_origin)
    request_origin = _normalized_origin(request.host_url)
    allowed_origins = {request_origin}
    if CONFIG.APP_URL:
        allowed_origins.add(_normalized_origin(str(CONFIG.APP_URL)))

    if origin is not None and origin in allowed_origins:
        return True

    # The development frontend and API commonly use separate localhost ports.
    return _is_loopback_origin(origin) and _is_loopback_origin(request_origin)
