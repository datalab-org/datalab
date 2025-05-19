import logging
import logging.handlers
import time
from collections.abc import Callable
from functools import wraps

LOG_FORMAT_STRING = "%(asctime)s | %(levelname)-8s: %(message)s (PID: %(process)d - %(name)s: %(pathname)s:%(funcName)s:%(lineno)d)"
ACCESS_LOG_FORMAT_STRING = (
    "%(asctime)s | %(levelname)-8s: %(message)s (PID: %(process)d - %(name)s)"
)


class AnsiColorHandler(logging.StreamHandler):
    """Colourful and truncated log handler, exfiltrated from/inspired
    by various answers at
    https://stackoverflow.com/questions/7484454/removing-handlers-from-pythons-logging-loggers

    """

    LOGLEVEL_COLORS = {
        logging.DEBUG: "36m",
        logging.INFO: "32m",
        logging.WARNING: "103;30m",
        logging.ERROR: "1;91m",
        logging.CRITICAL: "101;30m",
    }

    max_width = 2000

    def format(self, record: logging.LogRecord) -> str:
        message: str = super().format(record)
        if len(message) > self.max_width:
            message = message[: self.max_width] + "[...]"
        color = self.LOGLEVEL_COLORS[record.levelno]
        return f"\x1b[{color} {message}\x1b[0m"


def setup_log(log_name: str = "pydatalab", log_level: int | None = None) -> logging.Logger:
    """Creates a logger a simple coloured stdout output.

    Verbosity can be set to debug in the config file via
    the DEBUG option, or passed the the function.

    Starts by suppressing the root logger (retaining only
    errors and warnings), then creates a new logger for datalab
    specifically.
    Also adjusts the werkzeug logger to use a more concise format
    for pure access logs.

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

    logger = logging.getLogger(log_name)
    logger.handlers = []
    logger.propagate = False
    stream_handler = AnsiColorHandler()
    stream_handler.setFormatter(logging.Formatter(LOG_FORMAT_STRING))
    logger.addHandler(stream_handler)

    werkzeug_logger = logging.getLogger("werkzeug")
    werkzeug_logger.setLevel(logging.INFO)
    werkzeug_logger.handlers = []
    access_stream_handler = AnsiColorHandler()
    access_stream_handler.setFormatter(logging.Formatter(ACCESS_LOG_FORMAT_STRING))
    werkzeug_logger.addHandler(access_stream_handler)

    if CONFIG.LOG_FILE is not None:
        rotating_file_handler = logging.handlers.RotatingFileHandler(
            CONFIG.LOG_FILE, maxBytes=1000000, backupCount=100
        )
        rotating_file_handler.setFormatter(logging.Formatter(LOG_FORMAT_STRING))
        logger.addHandler(rotating_file_handler)

        access_file_handler = logging.handlers.RotatingFileHandler(
            CONFIG.LOG_FILE, maxBytes=1000000, backupCount=100
        )
        access_file_handler.setFormatter(logging.Formatter(ACCESS_LOG_FORMAT_STRING))
        werkzeug_logger.addHandler(access_file_handler)

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
                "%s returned in %s seconds with %s",
                fn.__name__,
                (time.monotonic_ns() - start) / 1e9,
                result,
            )
            return result
        except Exception as exc:
            import traceback

            LOGGER.error(
                "%s errored in %s seconds with %s %s %s",
                fn.__name__,
                (time.monotonic_ns() - start) / 1e9,
                exc.__class__.__name__,
                exc,
                traceback.print_tb(exc.__traceback__),
            )
            raise exc

    return wrapped_logged_route
