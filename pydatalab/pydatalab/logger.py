import logging
import pprint
from functools import wraps
from typing import Callable


def setup_log():
    """Creates a logger for pydatalab with a simple
    stdout output.

    Verbosity is set in the config file via
    the DEBUG option.

    """
    from pydatalab.config import CONFIG

    logging.basicConfig()
    logger = logging.getLogger("pydatalab")
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
            "Calling %s with request: %s, JSON payload: %s",
            fn.__name__,
            request,
            pprint.pprint(request.get_json(), depth=1, width=80, compact=True),
        )

        result = fn(*args, **kwargs)
        LOGGER.debug(
            "%s returned %s", fn.__name__, pprint.pprint(result, depth=1, width=80, compact=True)
        )
        return result

    return wrapped_logged_route
