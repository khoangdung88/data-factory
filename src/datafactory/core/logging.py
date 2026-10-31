"""Logging setup. Use ``get_logger(__name__)``; never ``print``."""

import logging


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    # basicConfig is a no-op when the root logger already has handlers (e.g. pytest);
    # setting the package level explicitly keeps pipeline INFO logs visible in the UI.
    logging.getLogger("datafactory").setLevel(level)
