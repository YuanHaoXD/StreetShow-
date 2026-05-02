from __future__ import annotations

import asyncio
import base64
import http.client
import json
import shutil
import time
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, File, Form, UploadFile

from ..core.config import ASSET_DIR, DMXAPI_KEY, DMXAPI_TIMEOUT, UPLOAD_DIR
from ..core.logging import logger
from ..core.model import DEVICE
from ..core.state import SEM
from ..services.nanobanana import _extract_inline_image, _mime_to_ext, make_mock_image
from ..services.qwen import analyze_garment_style
from ..utils.files import cleanup_assets
from ..utils.images import sanitize_and_save_image

router = APIRouter()

_IMAGE_HOST = "www.dmxapi.cn"
_IMAGE_PATH = "/v1beta/models/gemini-2.5-flash-image:generateContent"


def _build_multi_prompt(garment_count: int, user_prompt: str | None) -> str:
    if garment_count == 1:
        base = "将这件衣服穿到模特身上，保持模特脸部、发型、配件和背景完全不变，真实摄影质感。"
    elif garment_count == 2:
        base = (
            "将第一件衣服换到模特上半身（保持领子/袖子细节），"
            "将第二件衣服换到模特下半身（保持裤型/裙型细节）。"
            "保持模特脸部、发型、肤色、配件和背景完全不变，真实摄影质感。"
        )
    else:
        base = (
            "按顺序将多件衣服分层穿到模特身上（第一件上半身，第二件下半身，其余作叠穿搭配）。"
            "保持模特脸部、发型、肤色和背景完全不变，真实摄影质感，展示完整穿搭效果。"
        )
    if user_prompt:
        return f"{base} 额外要求：{user_prompt.strip()}"
    return base


def _call_multi_api(
    person_path: Path,
    garment_paths: list[Path],
    prompt_text: str,
) -> tuple[Path, bool, str | None, int]:
    """调用 Gemini 图像生成，多件衣物同时送入"""
    start = time.perf_counter()
    if not DMXAPI_KEY:
        out = make_mock_image()
        elapsed = int((time.perf_counter() - start) * 1000)
        return out, False, "dmxapi_key_missing", elapsed

    negative = "人脸变形，服装图案错误，材质失真，背景变化，配件消失"
    full_prompt = f"{prompt_text}。不要：{negative}"
    logger.info("Multi-Fit prompt: %s", full_prompt)

    # 构建 parts：先加所有衣物图片，最后加人物图片
    parts: list[dict] = [{"text": full_prompt}]
    for g_path in garment_paths:
        parts.append({
            "inline_data": {
                "mime_type": "image/jpeg",
                "data": base64.b64encode(g_path.read_bytes()).decode("utf-8"),
            }
        })
    parts.append({
        "inline_data": {
            "mime_type": "image/jpeg",
            "data": base64.b64encode(person_path.read_bytes()).decode("utf-8"),
        }
    })

    conn = None
    try:
        payload = json.dumps({
            "contents": [{"role": "user", "parts": parts}],
            "generationConfig": {
                "responseModalities": ["TEXT", "IMAGE"],
                "imageConfig": {"aspectRatio": "2:3"},
            },
        })
        headers = {
            "x-goog-api-key": DMXAPI_KEY,
            "Content-Type": "application/json",
        }
        conn = http.client.HTTPSConnection(_IMAGE_HOST, timeout=DMXAPI_TIMEOUT)
        conn.request("POST", _IMAGE_PATH, payload, headers)
        res = conn.getresponse()
        raw = res.read()
        if res.status >= 400:
            raise RuntimeError(f"DMXAPI 图像生成错误: {res.status} {res.reason}")
        resp = json.loads(raw.decode("utf-8", errors="replace"))
        mime, data = _extract_inline_image(resp)
        out_path = ASSET_DIR / f"multi_{uuid4().hex}{_mime_to_ext(mime)}"
        out_path.write_bytes(base64.b64decode(data))
        elapsed = int((time.perf_counter() - start) * 1000)
        return out_path, True, None, elapsed
    except Exception as exc:
        logger.warning("Multi-Fit API error: %s", exc)
        out = make_mock_image()
        elapsed = int((time.perf_counter() - start) * 1000)
        return out, False, str(exc), elapsed
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


@router.post("/api/process-multi")
async def process_multi_garments(
    background_tasks: BackgroundTasks,
    person_image: UploadFile = File(...),
    garment_images: list[UploadFile] = File(...),
    user_prompt: str | None = Form(None),
) -> dict[str, object]:
    # 限制衣物数量 1-3 件
    garment_images = garment_images[:3]

    request_dir = UPLOAD_DIR / uuid4().hex
    request_dir.mkdir(parents=True, exist_ok=True)

    person_bytes = await person_image.read()
    garment_bytes_list = await asyncio.gather(*(g.read() for g in garment_images))

    person_path = sanitize_and_save_image(person_bytes, request_dir)
    garment_paths = [
        sanitize_and_save_image(gb, request_dir) for gb in garment_bytes_list
    ]

    # 并行分析所有衣物风格DNA
    async with SEM:
        style_dna_list = await asyncio.gather(
            *(asyncio.to_thread(analyze_garment_style, gp) for gp in garment_paths)
        )

    prompt_text = _build_multi_prompt(len(garment_paths), user_prompt)

    start = time.perf_counter()
    async with SEM:
        result_path, used, err, nano_ms = await asyncio.to_thread(
            _call_multi_api, person_path, garment_paths, prompt_text
        )
    total_ms = int((time.perf_counter() - start) * 1000)

    background_tasks.add_task(cleanup_assets)
    background_tasks.add_task(shutil.rmtree, request_dir, ignore_errors=True)

    return {
        "image_url": f"/assets/{result_path.name}",
        "prompt_used": prompt_text,
        "garment_count": len(garment_paths),
        "style_dna_list": list(style_dna_list),
        "error": err,
        "meta": {
            "nano_ms": nano_ms,
            "total_ms": total_ms,
            "device": DEVICE,
            "nanobanana_used": used,
            "nanobanana_error": err,
        },
    }
