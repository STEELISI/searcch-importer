
import logging

def configure_logging(level=logging.WARN):
    logger = logging.getLogger("searcch.importer")
    ch = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s [%(process)d] %(levelname)-8s %(pathname)s"
        ":%(funcName)s:%(lineno)d %(message)s")
    ch.setFormatter(formatter)
    ch.setLevel(level)
    logger.addHandler(ch)
    logger.setLevel(level)
    logger.debug("logging configured")
