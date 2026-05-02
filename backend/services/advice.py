from __future__ import annotations

from typing import Any


def _join_items(value: Any) -> str:
    if isinstance(value, list):
        return "、".join(str(item) for item in value if item)
    if value:
        return str(value)
    return ""


def build_advice_from_plan(plan: dict[str, Any]) -> dict[str, str]:
    """根据 plan 生成结构化建议块（避免再次调用模型）"""
    person = plan.get("person", {}) or {}
    garment = plan.get("garment", {}) or {}
    variants = plan.get("variants", []) or []
    # 优先使用 analyze_garment_style() 专门分析的风格DNA
    style_dna = plan.get("style_dna", {}) or {}

    # ── 人物特征：从 person 字段读取，无 vibe 时不用固定词填充 ──
    vibe = _join_items(person.get("vibe_keywords"))
    body = person.get("body_silhouette", "")
    skin = person.get("skin_tone", "")
    person_parts = []
    if vibe:
        person_parts.append(f"气质关键词：{vibe}")
    if body:
        person_parts.append(f"身材轮廓为{body}")
    if skin:
        person_parts.append(f"肤色偏{skin}")
    person_text = "，".join(person_parts) + "。" if person_parts else "人物信息待分析。"

    # ── 衣物分析：优先用 style_dna，fallback 到 garment 字段 ──
    category = garment.get("category", "")
    fit = garment.get("fit", "")
    details = _join_items(garment.get("details"))
    # style_keywords 和 colors 优先读 style_dna
    style = _join_items(style_dna.get("style_keywords") or garment.get("style_tags"))
    colors = _join_items(
        style_dna.get("color_palette") or garment.get("main_colors")
    )
    dna_vibe = style_dna.get("vibe", "")

    garment_parts = []
    if category:
        garment_parts.append(f"服装为{category}")
    if fit:
        garment_parts.append(fit)
    if style:
        garment_parts.append(f"风格偏{style}")
    if colors:
        garment_parts.append(f"主色{colors}")
    garment_text = "，".join(garment_parts) + "。" if garment_parts else "服装信息待分析。"
    if details:
        garment_text += f" 细节：{details}。"
    if dna_vibe:
        garment_text += f" 整体气质：{dna_vibe}。"

    # ── 搭配建议：完全来自 style_dna，与 variants 场景无关 ──
    # occasions / avoid_scenes 是 analyze_garment_style() 对衣服本身的分析结果
    occasions = _join_items(style_dna.get("occasions"))
    avoid = _join_items(style_dna.get("avoid_scenes"))
    pose_hints = _join_items(style_dna.get("pose_suggestions"))

    styling_parts = []
    if occasions:
        styling_parts.append(f"适合场合：{occasions}")
    if avoid:
        styling_parts.append(f"不建议场合：{avoid}")
    if pose_hints:
        styling_parts.append(f"推荐姿势：{pose_hints}")
    styling_text = "；".join(styling_parts) + "。" if styling_parts else "按衣服风格搭配。"

    # ── 品质约束：加入 vibe 让描述更具体 ──
    quality_base = "整体保持真实摄影质感，强调人脸与衣服细节不变"
    quality_text = (
        f"{quality_base}，呈现{dna_vibe}的视觉氛围。"
        if dna_vibe
        else f"{quality_base}。"
    )

    return {
        "person": person_text,
        "garment": garment_text,
        "styling": styling_text,
        "quality": quality_text,
    }
