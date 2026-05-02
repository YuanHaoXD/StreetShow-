from __future__ import annotations

import asyncio

from .config import MAX_CONCURRENT

SEM = asyncio.Semaphore(MAX_CONCURRENT)
