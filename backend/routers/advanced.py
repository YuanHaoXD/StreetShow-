from __future__ import annotations

import asyncio
import shutil
import time
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, File, Form, UploadFile

from ..core.config import UPLOAD_DIR
from ..core.model import DEVICE
from ..core.state import SEM
from ..services.nanobanana import call_nanobanana_api, compose_prompt
from ..services.advice import build_advice_from_plan
from ..services.qwen import analyze_garment_style, build_qwen_plan
from ..utils.files import cleanup_assets
from ..utils.images import sanitize_and_save_image

router = APIRouter()


@router.post("/api/process-advanced")
async def process_images_advanced(
    background_tasks: BackgroundTasks,
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
        # 先提取衣服风格DNA，再生成风格匹配的方案
        garment_style = await asyncio.to_thread(analyze_garment_style, garment_path)
        plan = await asyncio.to_thread(
            build_qwen_plan, person_path, garment_path, k_variants, mode, user_prompt, garment_style
        )
    plan_ms = int((time.perf_counter() - qwen_start) * 1000)

    # 将风格DNA原始对象注入 plan，前端可单独展示
    plan["style_dna"] = garment_style

    advice_blocks = build_advice_from_plan(plan)
    qwen_ms = plan_ms

    variants = plan.get("variants", [])

    async def run_variant(variant: dict[str, object]) -> dict[str, object]:
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

    nano_start = time.perf_counter()
    results_raw = await asyncio.gather(*(run_variant(v) for v in variants))
    nano_ms = int((time.perf_counter() - nano_start) * 1000)

    nanobanana_used = any(r.get("nanobanana_used") for r in results_raw)
    nanobanana_error = None
    for r in results_raw:
        if r.get("error"):
            nanobanana_error = r["error"]
            break

    results = [
        {
            "variant_id": r["variant_id"],
            "title": r["title"],
            "prompt_used": r["prompt_used"],
            "negative_prompt_used": r["negative_prompt_used"],
            "image_url": r["image_url"],
            "error": r["error"],
        }
        for r in results_raw
    ]

    background_tasks.add_task(cleanup_assets)
    background_tasks.add_task(shutil.rmtree, request_dir, ignore_errors=True)

    return {
        "advice": advice_blocks,
        "plan": plan,
        "results": results,
        "meta": {
            "qwen_ms": qwen_ms,
            "nano_ms": nano_ms,
            "device": DEVICE,
            "nanobanana_used": nanobanana_used,
            "nanobanana_error": nanobanana_error,
            "k_variants": k_variants,
            "mode": mode,
        },
    }
