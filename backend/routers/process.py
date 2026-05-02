from __future__ import annotations

import asyncio
import shutil
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, File, UploadFile

from ..core.config import RETURN_DATA_URL, UPLOAD_DIR
from ..core.model import DEVICE
from ..core.state import SEM
from ..services.nanobanana import call_nanobanana_api
from ..services.qwen import run_qwen_advice
from ..utils.files import cleanup_assets
from ..utils.images import encode_image_data_url, sanitize_and_save_image

router = APIRouter()


@router.post("/api/process")
async def process_images(
    background_tasks: BackgroundTasks,
    person_image: UploadFile = File(...),
    garment_image: UploadFile = File(...),
) -> dict[str, object]:
    request_dir = UPLOAD_DIR / uuid4().hex
    request_dir.mkdir(parents=True, exist_ok=True)

    person_bytes, garment_bytes = await asyncio.gather(
        person_image.read(), garment_image.read()
    )
    person_path = sanitize_and_save_image(person_bytes, request_dir)
    garment_path = sanitize_and_save_image(garment_bytes, request_dir)

    async def run_qwen() -> tuple[str, int]:
        async with SEM:
            return await asyncio.to_thread(run_qwen_advice, person_path, garment_path)

    _BASIC_PROMPT = (
        "将第二张图片中的衣服自然地穿到第一张图片的模特身上。"
        "换衣规则：若是上装（T恤/卫衣/衬衫/外套/西装/夹克等）只替换上半身服装，"
        "若是下装（裤子/短裤/半裙/长裙等）只替换下半身服装，"
        "若是连衣裙/连体裤则全身替换。"
        "严格保持不变：①模特脸部五官、发型、肤色、体型；"
        "②背景场景、地面、光线方向；"
        "③鞋子、包包、帽子等其余配饰；"
        "④衣服原有的颜色、图案、Logo、材质纹理完全保留。"
        "真实摄影质感，禁止人脸变形、衣服边缘违和感、材质塑料化。"
    )

    async def run_nano() -> tuple[object, bool, str | None, int]:
        async with SEM:
            return await asyncio.to_thread(
                call_nanobanana_api, person_path, garment_path, _BASIC_PROMPT, None
            )

    (advice_text, qwen_ms), (tryon_path, used, nano_err, nano_ms) = await asyncio.gather(
        run_qwen(), run_nano()
    )

    background_tasks.add_task(cleanup_assets)
    background_tasks.add_task(shutil.rmtree, request_dir, ignore_errors=True)

    response: dict[str, object] = {
        "advice": advice_text,
        "tryon_image_url": f"/assets/{tryon_path.name}",
        "meta": {
            "qwen_ms": qwen_ms,
            "nano_ms": nano_ms,
            "device": DEVICE,
            "nanobanana_used": used,
            "nanobanana_error": nano_err,
        },
    }
    if RETURN_DATA_URL:
        response["tryon_image_data_url"] = encode_image_data_url(tryon_path)
    return response
