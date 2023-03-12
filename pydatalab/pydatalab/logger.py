import logging
from functools import wraps
from typing import Callable, Optional


class AnsiColorHandler(logging.StreamHandler):
    """Colourful and truncated log handler, exfiltrated from/inspired
    by various answers at
    https://stackoverflow.com/questions/7484454/removing-handlers-from-pythons-logging-loggers

    """

    LOGLEVEL_COLORS = {
        logging.DEBUG: "36m",
        logging.INFO: "32m",
        logging.WARNING: "33m",
        logging.ERROR: "1;91m",
        logging.CRITICAL: "101;30m",
    }

    max_width = 2000

    def __init__(self) -> None:
        super().__init__()
        self.formatter = logging.Formatter("%(asctime)s - %(name)s | %(levelname)-8s: %(message)s")

    def format(self, record: logging.LogRecord) -> str:
        from flask_login import current_user

        prefix = "🔓"
        if current_user and current_user.is_authenticated:
            prefix = "🔒"
        message: str = super().format(record)
        if len(message) > self.max_width:
            message = message[: self.max_width] + "[...]"
        color = self.LOGLEVEL_COLORS[record.levelno]
        message = f"\x1b[{color} {prefix} {message}\x1b[0m"
        return message


def setup_log(log_name: str = "pydatalab", log_level: Optional[int] = None) -> logging.Logger:
    """Creates a logger a simple coloured stdout output.

    Verbosity can be set to debug in the config file via
    the DEBUG option, or passed the the function.

    Parameters:
        log_name: The name of the logger.
        log_level: The logging level to use.

    Returns:
        The logger object.

    """
    from pydatalab.config import CONFIG

    logger = logging.getLogger(log_name)
    logger.handlers = []
    logger.propagate = False
    handler = AnsiColorHandler()
    logger.addHandler(handler)
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

        try:
            LOGGER.debug(
                "Calling %s with request: %s, JSON payload with keys %s",
                fn.__name__,
                request,
                request.get_json().keys() if request.get_json() else "null",
            )
        except Exception:
            pass
        try:
            result = fn(*args, **kwargs)
            LOGGER.debug(
                "%s returned %s",
                fn.__name__,
                result,
            )
            return result
        except Exception as exc:
            import traceback

            LOGGER.error(
                "%s errored with %s %s %s",
                fn.__name__,
                exc.__class__.__name__,
                exc,
                traceback.print_tb(exc.__traceback__),
            )
            raise exc

    return wrapped_logged_route
