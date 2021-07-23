import logging


def setup_log():
    # from pydatalab.config import CONFIG

    logging.basicConfig()
    logger = logging.getLogger("pydatalab")
    log_level = logging.INFO
    # if CONFIG.debug:
    # replace this once config is merged
    if True:
        log_level = logging.DEBUG
    logger.setLevel(log_level)
    return logger


LOGGER = setup_log()
