from __future__ import annotations

import asyncio
import shutil
import time
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from ..core.config import UPLOAD_DIR
from ..core.model import DEVICE
from ..core.state import SEM
from ..services.advice import build_advice_from_plan
from ..services.job_store import create_job, get_job, mark_done, update_job, update_result
from ..services.nanobanana import call_nanobanana_api, compose_prompt
from ..services.qwen import analyze_garment_style, build_qwen_plan
from ..utils.files import cleanup_assets
from ..utils.images import sanitize_and_save_image

router = APIRouter()


async def _run_variant(
    person_path,
    garment_path,
    variant: dict[str, object],
) -> dict[str, object]:
    prompt_used = compose_prompt(
        str(variant.get("nanobanana_prompt") or ""),
        str(variant.get("negative_prompt") or ""),
    )
    async with SEM:
        tryon_path, used, err, _ = await asyncio.to_thread(
            call_nanobanana_api,
            person_path,
            garment_path,
            variant.get("nanobanana_prompt"),
            variant.get("negative_prompt"),
            variant.get("id"),
        )
    return {
        "variant_id": variant.get("id", ""),
        "title": variant.get("title", ""),
        "prompt_used": prompt_used,
        "negative_prompt_used": variant.get("negative_prompt", ""),
        "image_url": f"/assets/{tryon_path.name}",
        "error": err,
        "nanobanana_used": used,
    }


async def _run_job(
    job_id: str,
    person_path,
    garment_path,
    variants: list[dict[str, object]],
    request_dir,
    meta_base: dict[str, object],
) -> None:
    nanobanana_used = False
    nanobanana_error = None
    start = time.perf_counter()
    try:
        tasks = [asyncio.create_task(_run_variant(person_path, garment_path, v)) for v in variants]
        for coro in asyncio.as_completed(tasks):
            result = await coro
            variant_id = str(result.get("variant_id", ""))
            nanobanana_used = nanobanana_used or bool(result.get("nanobanana_used"))
            if result.get("error") and nanobanana_error is None:
                nanobanana_error = result.get("error")
            await update_result(
                job_id,
                variant_id,
                {
                    "image_url": result.get("image_url", ""),
                    "error": result.get("error"),
                    "status": "error" if result.get("error") else "done",
                },
            )
        nano_ms = int((time.perf_counter() - start) * 1000)
        meta = {
            **meta_base,
            "nano_ms": nano_ms,
            "nanobanana_used": nanobanana_used,
            "nanobanana_error": nanobanana_error,
        }
        await mark_done(job_id, meta)
    except Exception as exc:
        await update_job(job_id, {"status": "error", "error": str(exc)})
    finally:
        cleanup_assets()
        shutil.rmtree(request_dir, ignore_errors=True)


@router.post("/api/process-advanced-async")
async def process_images_advanced_async(
    person_image: UploadFile = File(...),
    garment_image: UploadFile = File(...),
    k_variants: int = Form(4),
    mode: str = Form("lookbook"),
    user_prompt: str | None = Form(None),
) -> dict[str, object]:
    try:
        k_variants = max(1, int(k_variants))
    except Exception:
        k_variants = 4
    mode = mode if mode in {"lookbook", "pose", "multi"} else "lookbook"

    request_dir = UPLOAD_DIR / uuid4().hex
    request_dir.mkdir(parents=True, exist_ok=True)

    person_bytes, garment_bytes = await asyncio.gather(
        person_image.read(), garment_image.read()
    )
    person_path = sanitize_and_save_image(person_bytes, request_dir)
    garment_path = sanitize_and_save_image(garment_bytes, request_dir)

    qwen_start = time.perf_counter()
    async with SEM:
        garment_style = await asyncio.to_thread(analyze_garment_style, garment_path)
        plan = await asyncio.to_thread(
            build_qwen_plan, person_path, garment_path, k_variants, mode, user_prompt, garment_style
        )
    qwen_ms = int((time.perf_counter() - qwen_start) * 1000)

    # 将风格DNA原始对象注入 plan，前端可单独展示
    plan["style_dna"] = garment_style

    advice_blocks = build_advice_from_plan(plan)
    variants = plan.get("variants", [])
    if not isinstance(variants, list):
        variants = []

    results = [
        {
            "variant_id": variant.get("id", f"v{idx + 1}"),
            "title": variant.get("title", ""),
            "prompt_used": compose_prompt(
                str(variant.get("nanobanana_prompt") or ""),
                str(variant.get("negative_prompt") or ""),
            ),
            "negative_prompt_used": variant.get("negative_prompt", ""),
            "image_url": "",
            "error": None,
            "status": "pending",
        }
        for idx, variant in enumerate(variants)
    ]

    meta = {
        "qwen_ms": qwen_ms,
        "nano_ms": 0,
        "device": DEVICE,
        "nanobanana_used": False,
        "nanobanana_error": None,
        "k_variants": k_variants,
        "mode": mode,
    }

    job_id = await create_job(
        {
            "advice": advice_blocks,
            "plan": plan,
            "results": results,
            "meta": meta,
        }
    )

    asyncio.create_task(
        _run_job(job_id, person_path, garment_path, variants, request_dir, meta)
    )

    return {
        "job_id": job_id,
        "status": "running",
        "advice": advice_blocks,
        "plan": plan,
        "results": results,
        "meta": meta,
    }


@router.get("/api/process-advanced/jobs/{job_id}")
async def get_process_advanced_job(job_id: str) -> dict[str, object]:
    job = await get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "job_id": job.get("job_id", job_id),
        "status": job.get("status", "running"),
        "advice": job.get("advice", ""),
        "plan": job.get("plan", {}),
        "results": job.get("results", []),
        "meta": job.get("meta", {}),
        "error": job.get("error"),
    }
