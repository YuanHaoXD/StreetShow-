from __future__ import annotations

import base64
import http.client
import json
import time
from pathlib import Path
from uuid import uuid4

from PIL import Image, ImageDraw

from ..core.config import (
    ASSET_DIR,
    DMXAPI_IMAGE_MODEL,
    DMXAPI_KEY,
    DMXAPI_TIMEOUT,
)
from ..core.logging import logger

_IMAGE_PATH = f"/v1beta/models/{DMXAPI_IMAGE_MODEL}:generateContent"
_IMAGE_HOST = "www.dmxapi.cn"


def _mime_to_ext(mime: str) -> str:
    return {
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/webp": ".webp",
    }.get(mime, ".bin")


def _extract_inline_image(resp: dict[str, object]) -> tuple[str, str]:
    candidates = resp.get("candidates", []) or []
    for cand in candidates:
        if not isinstance(cand, dict):
            continue
        content = cand.get("content", {}) or {}
        if not isinstance(content, dict):
            continue
        parts = content.get("parts", []) or []
        for part in parts:
            if not isinstance(part, dict):
                continue
            inline = part.get("inlineData") or part.get("inline_data")
            if isinstance(inline, dict) and inline.get("data"):
                mime = inline.get("mimeType") or inline.get("mime_type") or "image/png"
                return mime, inline["data"]
    raise RuntimeError("Nanobanana 响应中未找到图片数据。")


def make_mock_image() -> Path:
    out_path = ASSET_DIR / f"mock_tryon_{uuid4().hex}.png"
    img = Image.new("RGB", (768, 1024), color=(10, 10, 20))
    draw = ImageDraw.Draw(img)
    draw.rectangle((40, 40, 728, 984), outline=(0, 255, 180), width=4)
    draw.text((80, 80), "DMXAPI MOCK", fill=(0, 255, 180))
    img.save(out_path)
    return out_path


def compose_prompt(prompt_text: str | None, negative_prompt: str | None) -> str:
    base = prompt_text.strip() if prompt_text else "将衣服换上模特"
    if negative_prompt:
        return f"{base}。不要：{negative_prompt.strip()}"
    return base


def call_nanobanana_api(
    person_img_path: Path,
    garment_img_path: Path,
    prompt_text: str | None = None,
    negative_prompt: str | None = None,
    variant_id: str | None = None,
) -> tuple[Path, bool, str | None, int]:
    """调用 DMXAPI Gemini 图像生成，返回：(路径, 是否成功, 错误信息, 耗时ms)"""
    start = time.perf_counter()
    if not DMXAPI_KEY:
        out = make_mock_image()
        elapsed = int((time.perf_counter() - start) * 1000)
        return out, False, "dmxapi_key_missing", elapsed

    prompt_used = compose_prompt(
        prompt_text or "将第二张图中的衣服穿到模特身上，只替换对应的服装部位，保持模特脸部/发型/背景/其余服装完全不变，真实摄影质感",
        negative_prompt,
    )
    tag = f"[{variant_id}] " if variant_id else ""
    logger.info("Nanobanana prompt %s%s", tag, prompt_used)

    conn = None
    try:
        payload = json.dumps(
            {
                "contents": [
                    {
                        "role": "user",
                        "parts": [
                            {"text": prompt_used},
                            {
                                "inline_data": {
                                    "mime_type": "image/jpeg",
                                    "data": base64.b64encode(
                                        garment_img_path.read_bytes()
                                    ).decode("utf-8"),
                                }
                            },
                            {
                                "inline_data": {
                                    "mime_type": "image/jpeg",
                                    "data": base64.b64encode(
                                        person_img_path.read_bytes()
                                    ).decode("utf-8"),
                                }
                            },
                        ],
                    }
                ],
                "generationConfig": {
                    "responseModalities": ["TEXT", "IMAGE"],
                    "imageConfig": {"aspectRatio": "2:3"},  # 竖版人像 832×1248
                },
            }
        )
        headers = {
            "x-goog-api-key": DMXAPI_KEY,   # DMXAPI Gemini 接口认证头
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
        out_path = ASSET_DIR / f"tryon_{uuid4().hex}{_mime_to_ext(mime)}"
        out_path.write_bytes(base64.b64decode(data))
        elapsed = int((time.perf_counter() - start) * 1000)
        return out_path, True, None, elapsed
    except Exception as exc:
        logger.warning("Nanobanana error %s%s", tag, exc)
        out = make_mock_image()
        elapsed = int((time.perf_counter() - start) * 1000)
        return out, False, str(exc), elapsed
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass
