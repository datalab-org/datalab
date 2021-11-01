import logging
import sys


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
    stdout_handler = logging.StreamHandler(sys.stdout)
    if CONFIG.DEBUG:
        log_level = logging.DEBUG
    logger.setLevel(log_level)
    stdout_handler.setLevel(log_level)
    stdout_handler.setFormatter("%(asctime)s - %(name)s | %(levelname)8s: %(message)s")
    logger.addHandler(stdout_handler)
    return logger


"""The main logging object to be imported from elsewhere in the package."""
LOGGER = setup_log()
