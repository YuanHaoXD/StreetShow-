from __future__ import annotations

import asyncio
import time
from typing import Any
from uuid import uuid4

from ..core.config import JOB_TTL_SECONDS

_JOBS: dict[str, dict[str, Any]] = {}
_LOCK = asyncio.Lock()


def _now() -> float:
    return time.time()


async def _cleanup_jobs() -> None:
    cutoff = _now() - JOB_TTL_SECONDS
    async with _LOCK:
        stale_keys = [key for key, job in _JOBS.items() if job.get("updated_at", 0) < cutoff]
        for key in stale_keys:
            _JOBS.pop(key, None)


async def create_job(payload: dict[str, Any]) -> str:
    await _cleanup_jobs()
    job_id = uuid4().hex
    data = {
        **payload,
        "job_id": job_id,
        "status": "running",
        "created_at": _now(),
        "updated_at": _now(),
    }
    async with _LOCK:
        _JOBS[job_id] = data
    return job_id


async def get_job(job_id: str) -> dict[str, Any] | None:
    await _cleanup_jobs()
    async with _LOCK:
        job = _JOBS.get(job_id)
        return dict(job) if job else None


async def update_job(job_id: str, updates: dict[str, Any]) -> None:
    async with _LOCK:
        job = _JOBS.get(job_id)
        if not job:
            return
        job.update(updates)
        job["updated_at"] = _now()


async def update_result(
    job_id: str, variant_id: str, updates: dict[str, Any]
) -> None:
    async with _LOCK:
        job = _JOBS.get(job_id)
        if not job:
            return
        results = job.get("results", [])
        if not isinstance(results, list):
            return
        for item in results:
            if item.get("variant_id") == variant_id:
                item.update(updates)
                job["updated_at"] = _now()
                return


async def mark_done(job_id: str, meta_updates: dict[str, Any]) -> None:
    await update_job(job_id, {"status": "completed", "meta": meta_updates})
