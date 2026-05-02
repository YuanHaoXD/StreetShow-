from __future__ import annotations

import os
from pathlib import Path

# ── DMXAPI（视觉分析 + 图像生成共用一个 Key）────────────────
DMXAPI_KEY: str = os.getenv("DMXAPI_KEY", "")
DMXAPI_BASE_URL: str = "https://www.dmxapi.cn"
DMXAPI_VL_MODEL: str = os.getenv("DMXAPI_VL_MODEL", "qwen3.5-flash")
DMXAPI_IMAGE_MODEL: str = "gemini-2.5-flash-image"
DMXAPI_TIMEOUT: float = float(os.getenv("DMXAPI_TIMEOUT", "90"))

# ── 应用配置 ─────────────────────────────────────────────────
MAX_UPLOAD_MB: int = int(os.getenv("MAX_UPLOAD_MB", "10"))
MAX_IMAGE_EDGE: int = int(os.getenv("MAX_IMAGE_EDGE", "2048"))
MAX_CONCURRENT: int = max(1, int(os.getenv("MAX_CONCURRENT", "2")))
RETURN_DATA_URL: bool = os.getenv("RETURN_DATA_URL", "0") == "1"
ASSET_TTL_SECONDS: int = int(os.getenv("ASSET_TTL_SECONDS", "3600"))
MAX_ASSET_FILES: int = int(os.getenv("MAX_ASSET_FILES", "200"))
JOB_TTL_SECONDS: int = int(os.getenv("JOB_TTL_SECONDS", "3600"))
CORS_ALLOW_ORIGINS: str = os.getenv("CORS_ALLOW_ORIGINS", "*")
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()

# ── 目录 ─────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parents[2]
TEMP_ROOT = BASE_DIR / "temp"
UPLOAD_DIR = TEMP_ROOT / "uploads"
ASSET_DIR = TEMP_ROOT / "assets"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ASSET_DIR.mkdir(parents=True, exist_ok=True)


def validate_config() -> None:
    """启动时校验必填配置，缺失则抛出清晰错误"""
    if not DMXAPI_KEY:
        raise RuntimeError(
            "缺少必要环境变量：DMXAPI_KEY。"
            "请复制 .env.example 为 .env 并填入你的 DMXAPI 密钥。"
        )
