from __future__ import annotations

import base64
import json
import time
from pathlib import Path
from typing import Any

import requests

from ..core.config import DMXAPI_BASE_URL, DMXAPI_KEY, DMXAPI_TIMEOUT, DMXAPI_VL_MODEL
from ..core.logging import logger
from .plan_modes import apply_mode_constraints, build_default_plan, build_plan_prompt


# ── 基础工具 ──────────────────────────────────────────────────────────────────

def _encode_image(path: Path) -> str:
    """将本地图片转为 base64 data URL"""
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    return f"data:image/jpeg;base64,{data}"


def _dmx_headers() -> dict[str, str]:
    return {
        "Authorization": DMXAPI_KEY,
        "Content-Type": "application/json",
    }


def _call_qwen_vl(messages: list[dict]) -> str:
    """调用 DMXAPI 多模态接口（OpenAI 兼容格式）"""
    resp = requests.post(
        f"{DMXAPI_BASE_URL}/v1/chat/completions",
        headers=_dmx_headers(),
        json={"model": DMXAPI_VL_MODEL, "messages": messages},
        timeout=DMXAPI_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _call_qwen_text(messages: list[dict]) -> str:
    """调用 DMXAPI 纯文本接口（用于 JSON 修复等不需要图片的任务）"""
    resp = requests.post(
        f"{DMXAPI_BASE_URL}/v1/chat/completions",
        headers=_dmx_headers(),
        json={"model": DMXAPI_VL_MODEL, "messages": messages},
        timeout=DMXAPI_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


# ── JSON 工具 ─────────────────────────────────────────────────────────────────

def _extract_json_block(text: str) -> str | None:
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        return text[start : end + 1]
    return None


def _try_parse_json(text: str | None) -> dict[str, Any] | None:
    if not text:
        return None
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        return None


def _repair_json_with_qwen(raw_text: str) -> dict[str, Any] | None:
    """调用文本模型修复格式错误的 JSON"""
    try:
        repaired = _call_qwen_text([
            {
                "role": "system",
                "content": (
                    "你是JSON修复器。你必须只输出严格合法的JSON，"
                    "不要输出任何解释、markdown或多余文字。"
                ),
            },
            {
                "role": "user",
                "content": f"修复下面内容为合法JSON：\n{raw_text}",
            },
        ])
        parsed = _try_parse_json(repaired)
        if parsed:
            return parsed
        block = _extract_json_block(repaired)
        return _try_parse_json(block)
    except Exception as e:
        logger.warning("JSON 修复失败: %s", e)
        return None


# ── 核心功能 ──────────────────────────────────────────────────────────────────

def run_qwen_advice(person_img_path: Path, garment_img_path: Path) -> tuple[str, int]:
    """生成穿搭建议文本，返回 (文本, 耗时ms)"""
    person_url = _encode_image(person_img_path)
    garment_url = _encode_image(garment_img_path)

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": person_url}},
                {"type": "image_url", "image_url": {"url": garment_url}},
                {
                    "type": "text",
                    "text": (
                        "你是前卫造型师。请用中文输出更具体的建议，格式如下：\n"
                        "1) 用户特征：身材轮廓、肤色倾向、气质关键词。\n"
                        "2) 服装解析：版型、材质、风格标签、主色/辅色。\n"
                        "3) 搭配方案：给出颜色搭配、鞋/配饰建议、场景建议。\n"
                        "4) 一句犀利总结（不超过30字）。\n"
                        "整体字数控制在150字以内，语言利落、有态度。"
                    ),
                },
            ],
        }
    ]

    start = time.perf_counter()
    text = _call_qwen_vl(messages)
    elapsed = int((time.perf_counter() - start) * 1000)
    return text, elapsed


def analyze_garment_style(garment_path: Path) -> dict[str, Any]:
    """分析衣服的风格DNA，用于动态生成提示词。

    返回结构：
    {
        "style_keywords": ["街头", "oversize", "酷感"],
        "color_palette": ["黑色", "米白"],
        "occasions": ["日常", "逛街", "音乐节"],
        "vibe": "都市街头感，慵懒中带叛逆",
        "avoid_scenes": ["正式场合", "商务会议"]
    }
    """
    garment_url = _encode_image(garment_path)

    messages = [
        {
            "role": "system",
            "content": "你是时尚分析师。只输出严格合法的JSON，不输出任何解释或markdown代码块。",
        },
        {
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": garment_url}},
                {
                    "type": "text",
                    "text": (
                        "分析这件衣服的风格DNA，只输出JSON：\n"
                        "{\n"
                        '  "style_keywords": ["风格词1","风格词2"],\n'
                        '  "color_palette": ["主色","辅色"],\n'
                        '  "occasions": ["适用场合1","适用场合2"],\n'
                        '  "vibe": "一句话描述整体氛围感",\n'
                        '  "avoid_scenes": ["不适合场景1","不适合场景2"],\n'
                        '  "pose_suggestions": ["与该衣服气质匹配的姿势1","姿势2","姿势3"]\n'
                        "}\n"
                        "pose_suggestions 要根据衣服风格推断：西装/正装→挺拔/严肃动作，"
                        "卫衣/街头→慵懒/放松动作，运动装→动感有力，连衣裙/礼服→优雅流动。"
                    ),
                },
            ],
        },
    ]

    try:
        raw = _call_qwen_vl(messages)
        parsed = _try_parse_json(raw)
        if not parsed:
            block = _extract_json_block(raw)
            parsed = _try_parse_json(block)
        if parsed and isinstance(parsed, dict):
            logger.info("风格DNA提取成功: vibe=%s", parsed.get("vibe"))
            return parsed
    except Exception as e:
        logger.warning("analyze_garment_style 失败: %s", e)

    return {
        "style_keywords": ["时尚", "现代"],
        "color_palette": ["主色保持"],
        "occasions": ["日常", "休闲"],
        "vibe": "现代都市感",
        "avoid_scenes": [],
        "pose_suggestions": ["正面站立，放松自然", "微侧身，轻松气质", "双手插兜，随意感"],
    }


# ── plan 构建 ─────────────────────────────────────────────────────────────────

def _default_plan(k_variants: int, mode: str, user_prompt: str | None) -> dict[str, Any]:
    return build_default_plan(k_variants, mode, user_prompt)


def _ensure_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


_TOP_KEYWORDS = ["上装", "T恤", "衬衫", "外套", "毛衣", "卫衣", "西装", "夹克", "背心", "针织", "连帽"]
_BOTTOM_KEYWORDS = ["裤子", "下装", "短裤", "牛仔裤", "半裙", "裙子", "裙"]


def _category_lock(category: str) -> str:
    """根据服装类别生成'只换这部分，其余不动'的约束句"""
    if any(kw in category for kw in _TOP_KEYWORDS):
        return "只替换上半身上装，保持下装/裤子/裙子/鞋子不变；"
    if any(kw in category for kw in _BOTTOM_KEYWORDS):
        return "只替换下半身下装，保持上装/外套不变；"
    # 连衣裙/全身/未知：不额外约束，让模型判断
    return "只替换图中对应的服装，其他服装保持原图不变；"


def _build_variant_prompt(
    plan: dict[str, Any], variant: dict[str, Any], mode: str = "lookbook"
) -> str:
    garment = plan.get("garment", {}) or {}
    constraints = plan.get("base_constraints", {}) or {}
    style_tags = "、".join(_ensure_list(garment.get("style_tags")))
    colors = "、".join(_ensure_list(garment.get("main_colors")))
    details = "、".join(_ensure_list(garment.get("details")))
    category = garment.get("category", "服装")
    identity_lock = constraints.get("identity_lock", "保持模特身份一致（脸不变）")
    garment_lock = constraints.get("garment_lock", "衣服颜色/材质/图案/Logo保持不变")
    quality = constraints.get("quality", "真实摄影质感")
    scene = variant.get("scene", "")
    pose = variant.get("pose", "")
    wearing = variant.get("wearing", "")
    styling = variant.get("styling", "")
    camera = variant.get("camera", "")
    lighting = variant.get("lighting", "")
    garment_desc = f"{category}，{style_tags}，主色：{colors}，细节：{details}"
    shot = f"{scene}，{pose}，{wearing}，{styling}，{camera}，{lighting}"

    # 所有模式都加上类别约束，确保只换对应部位
    cat_lock = _category_lock(category)

    # pose 模式：明确先换衣、再改姿势，其余全锁
    if mode == "pose":
        return (
            f"将第二张图中的{category}穿到模特身上；"
            f"姿势改为：{pose}；"
            f"{cat_lock}"
            f"背景、裤子、裙子、鞋子、配件保持完全不变；"
            f"{identity_lock}；{garment_lock}；{quality}。"
            f"{garment_desc}。{camera}，{lighting}"
        )

    return f"{cat_lock}{identity_lock}；{garment_lock}；{quality}。{garment_desc}。{shot}"


def _normalize_plan(
    plan: dict[str, Any], k_variants: int, mode: str, user_prompt: str | None,
) -> dict[str, Any]:
    if not isinstance(plan, dict):
        plan = _default_plan(k_variants, mode, user_prompt)

    person = plan.get("person") or {}
    garment = plan.get("garment") or {}
    base_constraints = plan.get("base_constraints") or {}
    variants = plan.get("variants") if isinstance(plan.get("variants"), list) else []

    person = {
        "vibe_keywords": _ensure_list(person.get("vibe_keywords")),
        "body_silhouette": person.get("body_silhouette", "正常体型"),
        "skin_tone": person.get("skin_tone", "中性"),
        "do_not_change": _ensure_list(person.get("do_not_change")),
    }
    garment = {
        "category": garment.get("category", "服装"),
        "style_tags": _ensure_list(garment.get("style_tags")),
        "fit": garment.get("fit", "标准版型"),
        "material_guess": _ensure_list(garment.get("material_guess")),
        "main_colors": _ensure_list(garment.get("main_colors")),
        "details": _ensure_list(garment.get("details")),
    }
    base_constraints = {
        "identity_lock": base_constraints.get("identity_lock", "保持模特身份一致（脸不变）"),
        "garment_lock": base_constraints.get(
            "garment_lock", "衣服颜色/材质/图案/Logo保持不变"
        ),
        "quality": base_constraints.get("quality", "真实摄影质感"),
        "avoid": _ensure_list(base_constraints.get("avoid")),
    }

    normalized_variants: list[dict[str, Any]] = []
    for idx, variant in enumerate(variants):
        if not isinstance(variant, dict):
            continue
        v = {
            "id": variant.get("id", f"v{idx + 1}"),
            "title": variant.get("title", f"Look {idx + 1}"),
            "pose": variant.get("pose", "站立姿势"),
            "wearing": variant.get("wearing", "标准穿法"),
            "styling": variant.get("styling", "按衣服风格搭配"),
            "scene": variant.get("scene", "棚拍背景"),
            "camera": variant.get("camera", "中景/全身"),
            "lighting": variant.get("lighting", "柔和主光"),
            "nanobanana_prompt": str(variant.get("nanobanana_prompt", "")),
            "negative_prompt": str(variant.get("negative_prompt", "")),
        }
        normalized_variants.append(v)

    if not normalized_variants:
        normalized_variants = _default_plan(k_variants, mode, user_prompt)["variants"]

    for v in normalized_variants:
        if user_prompt and user_prompt not in v.get("styling", ""):
            v["styling"] = f"{v.get('styling', '按衣服风格搭配')}，{user_prompt}"
        if not v.get("nanobanana_prompt") or mode == "pose":
            v["nanobanana_prompt"] = _build_variant_prompt(
                {"person": person, "garment": garment, "base_constraints": base_constraints},
                v,
                mode,
            )
        if not v.get("negative_prompt"):
            v["negative_prompt"] = "，".join(base_constraints.get("avoid", []))

    if normalized_variants:
        normalized_variants[0].update(
            {
                "title": "标准换衣",
                "pose": "正面站立，姿势不变",
                "wearing": "标准穿法",
            }
        )

    if len(normalized_variants) < k_variants:
        fallback = _default_plan(k_variants, mode, user_prompt)["variants"]
        for v in fallback[len(normalized_variants) : k_variants]:
            normalized_variants.append(v)

    normalized_variants = normalized_variants[:k_variants]
    for idx, v in enumerate(normalized_variants):
        v["id"] = f"v{idx + 1}"

    return {
        "person": person,
        "garment": garment,
        "base_constraints": base_constraints,
        "variants": normalized_variants,
    }


def build_qwen_plan(
    person_path: Path,
    garment_path: Path,
    k_variants: int,
    mode: str,
    user_prompt: str | None,
    garment_style: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """生成结构化 JSON 计划，支持风格DNA注入以实现动态提示词"""
    person_url = _encode_image(person_path)
    garment_url = _encode_image(garment_path)

    system_text, user_text = build_plan_prompt(mode, k_variants, user_prompt, garment_style)

    messages = [
        {"role": "system", "content": system_text},
        {
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": person_url}},
                {"type": "image_url", "image_url": {"url": garment_url}},
                {"type": "text", "text": user_text},
            ],
        },
    ]

    try:
        raw_text = _call_qwen_vl(messages)
    except Exception as e:
        logger.warning("build_qwen_plan Qwen API 调用失败，使用兜底计划: %s", e)
        return apply_mode_constraints(_default_plan(k_variants, mode, user_prompt), mode)

    parsed = _try_parse_json(raw_text)
    if not parsed:
        block = _extract_json_block(raw_text)
        parsed = _try_parse_json(block)
    if not parsed:
        parsed = _repair_json_with_qwen(raw_text)
    if not parsed:
        logger.warning("build_qwen_plan JSON 解析全部失败，使用兜底计划")
        parsed = _default_plan(k_variants, mode, user_prompt)

    plan = _normalize_plan(parsed, k_variants, mode, user_prompt)
    plan = apply_mode_constraints(plan, mode)
    logger.info(
        "Qwen plan 生成完毕: %s 个方案, mode=%s", len(plan.get("variants", [])), mode
    )
    for variant in plan.get("variants", []):
        logger.info("方案 %s 提示词: %s", variant.get("id"), variant.get("nanobanana_prompt"))
    return plan
