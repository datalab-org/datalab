import logging
from functools import wraps
from typing import Callable


class AnsiColorHandler(logging.StreamHandler):
    """Colourful and truncated log handler, exfiltrated from/inspired
    by various answers at
    https://stackoverflow.com/questions/7484454/removing-handlers-from-pythons-logging-loggers

    """

    LOGLEVEL_COLORS = {
        logging.DEBUG: "38;20m",
        logging.INFO: "46;30m",
        logging.WARNING: "43;30m",
        logging.ERROR: "41;30m",
        logging.CRITICAL: "101;30m",
    }

    max_width = 320

    def __init__(self) -> None:
        super().__init__()
        self.formatter = logging.Formatter("%(asctime)s - %(name)s | %(levelname)-8s: %(message)s")

    def format(self, record: logging.LogRecord) -> str:
        message: str = super().format(record)
        if len(message) > self.max_width:
            message = message[: self.max_width] + "[...]"
        color = self.LOGLEVEL_COLORS[record.levelno]
        message = f"\x1b[{color}{message}\x1b[0m"
        return message


def setup_log():
    """Creates a logger for pydatalab with a simple
    stdout output.

    Verbosity is set in the config file via
    the DEBUG option.

    """
    from pydatalab.config import CONFIG

    logger = logging.getLogger("pydatalab")
    logger.handlers = []
    logger.propagate = False
    handler = AnsiColorHandler()
    logger.addHandler(handler)

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

        LOGGER.debug(
            "Calling %s with request: %s, JSON payload with keys %s",
            fn.__name__,
            request,
            request.get_json().keys() if request.get_json() else "null",
        )
        try:
            result = fn(*args, **kwargs)
            LOGGER.debug(
                "%s returned %s",
                fn.__name__,
                result,
            )
            return result
        except Exception as exc:
            LOGGER.error("%s errored with %s", fn.__name__, exc)
            raise exc

    return wrapped_logged_route
