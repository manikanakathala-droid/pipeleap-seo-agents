from __future__ import annotations

import logging


def configure_logger(name: str = "pipeleap_seo_agent", level: str = "INFO") -> logging.Logger:
    """Create a reusable console logger."""

    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    )
    logger.addHandler(handler)
    logger.propagate = False
    return logger
