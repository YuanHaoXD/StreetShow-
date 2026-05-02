from __future__ import annotations

import time

from ..core.config import ASSET_DIR, ASSET_TTL_SECONDS, MAX_ASSET_FILES


def cleanup_assets() -> None:
    """清理输出目录中的过期文件"""
    if not ASSET_DIR.exists():
        return
    now = time.time()
    files = []
    for item in ASSET_DIR.iterdir():
        if item.is_file():
            try:
                stat = item.stat()
            except OSError:
                continue
            age = now - stat.st_mtime
            if age > ASSET_TTL_SECONDS:
                try:
                    item.unlink()
                except OSError:
                    pass
            else:
                files.append((stat.st_mtime, item))
    if len(files) <= MAX_ASSET_FILES:
        return
    files.sort(key=lambda entry: entry[0])
    for _, item in files[:-MAX_ASSET_FILES]:
        try:
            item.unlink()
        except OSError:
            pass
