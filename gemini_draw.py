"""
gemini_draw.py — 科研绘图 / 图片编辑脚本
使用 DMXAPI · gemini-3-pro-image-preview

使用方法：修改下方「配置区」的参数，然后直接运行此文件即可。
"""

from google import genai
from google.genai import types
from PIL import Image
from datetime import datetime
from pathlib import Path

# =============================================================================
# ★ 配置区：每次使用只需修改这里 ★
# =============================================================================

# DMXAPI 密钥
API_KEY = "sk-VmjMBo9BepKNB2NqPkuf0UA39J348RtfEpjLF8AWILbcA9kK"

# 提示词
PROMPT = (
"Create a clean flat minimalist high-end scientific infographic diagram in a modern flat design style similar to PaperBanana Framework but flatter and more serious engineering style clean vector art professional blue white and gray color palette soft flat shadows minimal details white background high contrast perfectly balanced composition for academic paper Title at the top in large bold font Concurrency Control and JSON Fault Tolerance The diagram is divided into two clear vertical sections side by side Left section titled Concurrency Control with a central semaphore icon and professional robot managing multiple API calls connected by arrows showing controlled flow Text below reads The system uses asyncio Semaphore mechanism to control the number of concurrent requests to external APIs preventing exceeding API rate limits and resource exhaustion Right section titled JSON Fault Tolerance with a four step vertical flowchart showing error handling pipeline First step direct json loads parsing Second step extract curly brace block and reparse Third step call Qwen text model to repair JSON Fourth step fallback to build default plan fixed scheme Use flat minimalist engineering style simple clean icons modern sans-serif typography subtle color blocks no heavy decorations clean layout ultra high resolution perfect for research paper sixteen to nine ratio masterpiece best quality")

# 参考图片路径（填写路径则进入图片编辑模式，留空 "" 则纯文字生成）
REF_IMAGE = ""
# REF_IMAGE = r"E:\AIproject\tryonproject\qwen-vl\output\gen_20260412_153201.png"

# 输出图片宽高比
# 可选：1:1 / 2:3 / 3:2 / 3:4 / 4:3 / 4:5 / 5:4 / 9:16 / 16:9 / 21:9
# 对应分辨率（1K）：
#   1:1  → 1024×1024   适合示意图
#   4:3  → 1200×896    适合图表、幻灯片
#   16:9 → 1376×768    适合横向数据可视化
ASPECT_RATIO = "16:9"

# 输出分辨率：1K / 2K / 4K
IMAGE_SIZE = "1K"

# 结果保存目录（默认脚本同级的 output 文件夹）
OUTPUT_DIR = Path(__file__).parent / "output"

# =============================================================================
# 以下代码无需修改
# =============================================================================

def _save_response(response, prefix: str) -> Path:
    OUTPUT_DIR.mkdir(exist_ok=True)
    if not response.candidates:
        raise RuntimeError("API 未返回候选结果，可能触发了安全过滤器。")
    finish = str(response.candidates[0].finish_reason)
    if finish not in ("FinishReason.STOP", "STOP", "1"):
        raise RuntimeError(f"生成未正常结束，finish_reason={finish}")
    if response.parts is None:
        raise RuntimeError("响应 parts 为空，请检查提示词或账户余额。")
    for part in response.parts:
        if part.text:
            print(f"模型文字回复：{part.text}")
        elif part.inline_data:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            out = OUTPUT_DIR / f"{prefix}_{ts}.png"
            part.as_image().save(out)
            return out
    raise RuntimeError("响应中未找到图像数据。")


def main():
    client = genai.Client(
        api_key=API_KEY,
        http_options={"base_url": "https://www.dmxapi.cn"},
    )

    if REF_IMAGE:
        ref_path = Path(REF_IMAGE)
        if not ref_path.exists():
            raise FileNotFoundError(f"找不到参考图片：{REF_IMAGE}")
        print(f"[图片编辑] 参考图：{ref_path.name} | {ASPECT_RATIO} / {IMAGE_SIZE}")
        contents = [PROMPT, Image.open(ref_path)]
        prefix = "edit"
    else:
        print(f"[文字生成] {ASPECT_RATIO} / {IMAGE_SIZE}")
        contents = [PROMPT]
        prefix = "gen"

    response = client.models.generate_content(
        model="gemini-3-pro-image-preview",
        contents=contents,
        config=types.GenerateContentConfig(
            response_modalities=["Image"],
            image_config=types.ImageConfig(
                aspect_ratio=ASPECT_RATIO,
                image_size=IMAGE_SIZE,
            ),
        ),
    )

    saved = _save_response(response, prefix)
    print(f"✓ 已保存：{saved}")


if __name__ == "__main__":
    main()
