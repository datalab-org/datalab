import logging
import logging.handlers
import pathlib
import time
from collections.abc import Callable
from contextvars import ContextVar
from functools import lru_cache, wraps

# Abbreviate the two long level names so that all levels fit in 5 characters
logging.addLevelName(logging.WARNING, "WARN")
logging.addLevelName(logging.CRITICAL, "CRIT")

LOG_FORMAT_STRING = (
    "%(asctime)s %(levelname)-5s %(request_id)s │ %(message)s (PID: %(process)d - %(source)s)"
)

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
"""Holds the ID of the request (or background task) currently being handled
in this context, used to correlate log lines; set per-request in `create_app`."""


@lru_cache(maxsize=None)
def _module_from_path(pathname: str) -> str:
    """Resolve a source file path to a dotted module name by walking up
    the package tree, e.g., '.../src/pydatalab/main.py' -> 'pydatalab.main'."""
    path = pathlib.Path(pathname)
    parts = [path.stem]
    parent = path.parent
    while (parent / "__init__.py").exists():
        parts.append(parent.name)
        parent = parent.parent
    return ".".join(reversed(parts))


class LogContextFilter(logging.Filter):
    """Stamps each record with the current request/task ID (blank outside of
    any request, padded to the width of the generated 8-character IDs) and
    a concise 'module:function:lineno' source location."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = (request_id_var.get() or "").ljust(8)
        record.source = f"{_module_from_path(record.pathname)}:{record.funcName}:{record.lineno}"
        return True


class AnsiColorFormatter(logging.Formatter):
    """Truncating formatter that renders the timestamp, request ID and
    PID/source suffix in grey and the level name in a severity-dependent
    colour, leaving the message itself unstyled."""

    GREY = "\x1b[90m"
    RESET = "\x1b[0m"

    LOGLEVEL_COLORS = {
        logging.DEBUG: "36m",
        logging.INFO: "32m",
        logging.WARNING: "33m",
        logging.ERROR: "1;91m",
        logging.CRITICAL: "1;31m",
    }

    max_width = 2000

    def __init__(self, fmt: str = LOG_FORMAT_STRING):
        super().__init__(fmt)
        self._level_formatters = {}
        for level, color in self.LOGLEVEL_COLORS.items():
            # As each level gets its own formatter, the level name can be
            # coloured and padded statically, keeping any background
            # colour off the padding spaces
            level_name = logging.getLevelName(level)
            padding = " " * max(0, 5 - len(level_name))
            colored_fmt = (
                fmt.replace("%(asctime)s", f"{self.GREY}%(asctime)s{self.RESET}")
                .replace("%(levelname)-5s", f"\x1b[{color}{level_name}{self.RESET}{padding}")
                .replace("%(request_id)s", f"{self.GREY}%(request_id)s{self.RESET}")
                .replace("│", f"\x1b[{color}│{self.RESET}")
                .replace("(PID:", f"{self.GREY}(PID:")
            )
            if "(PID:" in fmt:
                colored_fmt += self.RESET
            self._level_formatters[level] = logging.Formatter(colored_fmt)

    def format(self, record: logging.LogRecord) -> str:
        formatter = self._level_formatters.get(record.levelno)
        message = formatter.format(record) if formatter else super().format(record)
        if len(message) > self.max_width:
            message = message[: self.max_width] + "[...]"
        return message


def setup_log(log_name: str = "pydatalab", log_level: int | None = None) -> logging.Logger:
    """Creates a logger a simple coloured stdout output.

    Verbosity can be set to debug in the config file via
    the DEBUG option, or passed the the function.

    Starts by suppressing the root logger (retaining only
    errors and warnings), then creates a new logger for datalab
    specifically.
    Also quietens the werkzeug logger to warnings and above, as
    access logs are written by the app itself in `create_app`.

    Parameters:
        log_name: The name of the logger.
        log_level: The logging level to use.

    Returns:
        The logger object.

    """
    from pydatalab.config import CONFIG

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.CRITICAL)
    root_logger.handlers = []

    context_filter = LogContextFilter()

    logger = logging.getLogger(log_name)
    logger.handlers = []
    logger.propagate = False
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(AnsiColorFormatter())
    stream_handler.addFilter(context_filter)
    logger.addHandler(stream_handler)

    # Quieten the werkzeug dev server: access lines are logged by the app
    # itself (see `create_app`), so only warnings and above are kept,
    # rendered through the same handlers as the main logger
    werkzeug_logger = logging.getLogger("werkzeug")
    werkzeug_logger.setLevel(logging.WARNING)
    werkzeug_logger.handlers = []
    werkzeug_logger.addHandler(stream_handler)

    if CONFIG.LOG_FILE is not None:
        # A single handler instance shared between both loggers, so that
        # only one object is ever responsible for rotating the file
        rotating_file_handler = logging.handlers.RotatingFileHandler(
            CONFIG.LOG_FILE, maxBytes=1000000, backupCount=100
        )
        rotating_file_handler.setFormatter(logging.Formatter(LOG_FORMAT_STRING))
        rotating_file_handler.addFilter(context_filter)
        logger.addHandler(rotating_file_handler)
        werkzeug_logger.addHandler(rotating_file_handler)

    if log_level is None:
        log_level = logging.INFO

        if CONFIG.DEBUG:
            log_level = logging.DEBUG

    logger.setLevel(log_level)
    return logger


"""The main logging object to be imported from elsewhere in the package."""
LOGGER = setup_log()


def logged_route(fn: Callable):
    """A decorator that enables logging of inputs (arguments
    and request body) and outputs (server response) when debug
    mode is enabled.

    Args:
        fn: The function to wrap.

    """

    @wraps(fn)
    def wrapped_logged_route(*args, **kwargs):
        from flask import request

        start = time.monotonic_ns()
        try:
            LOGGER.debug(
                "Calling %s with request: %s, JSON payload with keys %s",
                fn.__name__,
                request,
                request.get_json().keys() if request.get_json() else "null",
            )
        except Exception:
            LOGGER.debug(
                "Calling %s with request: %s, Unable to decode JSON payload",
                fn.__name__,
                request,
            )
        try:
            result = fn(*args, **kwargs)

            LOGGER.debug(
                "%s returned in %.3f seconds",
                fn.__name__,
                (time.monotonic_ns() - start) / 1e9,
            )
            return result
        except Exception as exc:
            LOGGER.exception(
                "%s errored in %.3f seconds with %s: %s",
                fn.__name__,
                (time.monotonic_ns() - start) / 1e9,
                exc.__class__.__name__,
                exc,
            )
            raise exc

    return wrapped_logged_route
