from __future__ import annotations

import logging

from .config import LOG_LEVEL


def setup_logging() -> logging.Logger:
    logging.basicConfig(
        level=LOG_LEVEL,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    return logging.getLogger("streetshow")


logger = logging.getLogger("streetshow")
