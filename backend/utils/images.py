from __future__ import annotations

import base64
import io
import mimetypes
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException
from PIL import Image, ImageOps

from ..core.config import MAX_IMAGE_EDGE, MAX_UPLOAD_MB


def sanitize_and_save_image(file_bytes: bytes, out_dir: Path) -> Path:
    """校验并保存图片，统一为 JPEG，限制最大边长"""
    max_bytes = MAX_UPLOAD_MB * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise HTTPException(status_code=413, detail="Upload too large")

    try:
        with Image.open(io.BytesIO(file_bytes)) as img:
            img = ImageOps.exif_transpose(img)
            img = img.convert("RGB")
            img.thumbnail((MAX_IMAGE_EDGE, MAX_IMAGE_EDGE))
            filename = f"{uuid4().hex}.jpg"
            out_path = out_dir / filename
            img.save(out_path, format="JPEG", quality=92)
            return out_path
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid image") from exc


def encode_image_data_url(image_path: Path) -> str:
    """生成 data URL"""
    mime_type, _ = mimetypes.guess_type(str(image_path))
    if not mime_type:
        mime_type = "image/jpeg"
    data = image_path.read_bytes()
    encoded = base64.b64encode(data).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"
