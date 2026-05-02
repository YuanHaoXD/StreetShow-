from __future__ import annotations

import random
from typing import Any


MODE_SPECS: dict[str, dict[str, Any]] = {
    "lookbook": {
        "label": "Lookbook",
        "guidance": (
            "模式重点：多场景、多气质变化，允许姿势与场景变化，但保持服装风格一致。"
        ),
        "title_prefix": "Look",
        "pose_list": [
            "正面站立，自信姿态",
            "微侧身，轻微转头",
            "行走抓拍，动态感",
            "坐姿半身，放松自然",
            "双手插兜，街头感",
            "手持配件，轻松互动",
        ],
        "scene_list": [
            "纯色棚拍背景",
            "夜景霓虹街头",
            "工业风室内",
            "自然光室外",
            "时尚展厅",
            "街头路口",
        ],
        "camera_list": [
            "中景/全身，真实镜头感",
            "半身特写，略带景深",
            "全身广角，带环境",
            "低角度仰拍，强调气势",
            "俯拍四十五度，时尚杂志感",
            "移轴感，主体清晰背景虚化",
        ],
        "lighting_list": [
            "柔和主光+轮廓光",
            "对比光，立体质感",
            "自然散射光",
            "黄金时刻暖光，氛围感",
            "夜间人工补光，霓虹色调",
            "高调白棚光，干净通透",
        ],
        "wearing_list": [
            "标准穿法",
            "轻微层次搭配",
            "配饰点缀",
        ],
        "fixed_scene": None,
        "fixed_camera": None,
        "fixed_lighting": None,
        "force_wearing": None,
    },
    "pose": {
        "label": "Pose Lab",
        "guidance": (
            "模式重点：只改变人物姿势与身体动势，背景/裤子/鞋子/配件完全锁定不变。"
            "根据衣物风格DNA推断适合的动作气质：正装/西装→挺拔正式；卫衣/休闲→慵懒放松；"
            "运动装→动感有力；连衣裙→优雅流动。每个方案姿势必须明显不同。"
        ),
        "title_prefix": "Pose",
        "pose_list": [
            "正面站立，肩部放松",
            "微侧身，轻微转头",
            "双手插兜，放松站姿",
            "单手扶腰，挺拔姿态",
            "手臂轻垂，平静气质",
            "行走瞬间，轻微动态",
        ],
        "scene_list": ["纯色棚拍背景"],
        "camera_list": ["中景/全身，稳定机位"],
        "lighting_list": ["柔和主光+轮廓光"],
        "wearing_list": ["标准穿法"],
        "fixed_scene": "纯色棚拍背景",
        "fixed_camera": "中景/全身，稳定机位",
        "fixed_lighting": "柔和主光+轮廓光",
        "force_wearing": "标准穿法",
    },
    "multi": {
        "label": "Multi-Fit",
        "guidance": (
            "模式重点：多件衣物同时上身，上下装分别替换，保持模特身份、配件和背景完全一致。"
        ),
        "title_prefix": "Multi",
        "pose_list": [
            "正面站立，展示全身搭配",
        ],
        "scene_list": ["纯色棚拍背景"],
        "camera_list": ["全身，稳定机位"],
        "lighting_list": ["均匀柔光"],
        "wearing_list": ["标准穿法"],
        "fixed_scene": "纯色棚拍背景",
        "fixed_camera": "全身，稳定机位",
        "fixed_lighting": "均匀柔光",
        "force_wearing": "标准穿法",
    },
}


def get_mode_spec(mode: str) -> dict[str, Any]:
    return MODE_SPECS.get(mode, MODE_SPECS["lookbook"])


def build_plan_prompt(
    mode: str,
    k_variants: int,
    user_prompt: str | None,
    garment_style: dict[str, Any] | None = None,
) -> tuple[str, str]:
    spec = get_mode_spec(mode)
    system_text = (
        "你是时尚造型总监+摄影导演+提示词工程师。你必须只输出严格合法的 JSON，"
        "不要输出任何额外文字、解释、markdown、代码块。JSON 必须能被 Python json.loads 直接解析。"
    )

    # 将衣服风格DNA注入提示词，驱动动态场景/姿势生成
    style_context = ""
    if garment_style:
        keywords = "、".join(garment_style.get("style_keywords", []))
        occasions = "、".join(garment_style.get("occasions", []))
        vibe = garment_style.get("vibe", "")
        avoid = "、".join(garment_style.get("avoid_scenes", []))
        pose_suggestions = garment_style.get("pose_suggestions", [])
        pose_hint = ""
        if pose_suggestions and mode == "pose":
            pose_hint = (
                f"  推荐姿势（基于服装气质）：{'、'.join(pose_suggestions)}\n"
                "  请以上述推荐姿势为基础，为每个 variant 生成明显不同且与服装气质匹配的姿势。\n"
            )
        style_context = (
            "\n【衣服风格DNA（已预分析）】\n"
            f"  风格关键词：{keywords}\n"
            f"  适用场合：{occasions}\n"
            f"  整体氛围：{vibe}\n"
            f"  应避免的场景：{avoid or '无'}\n"
            f"{pose_hint}"
            "请让所有 variants 的场景、动作、光影与上述风格DNA高度匹配，"
            "根据衣服气质自由创作，而不是使用通用的随机场景。\n"
        )

    # pose 模式专属约束提示
    pose_mode_extra = ""
    if mode == "pose":
        pose_mode_extra = (
            "【Pose Lab 严格约束】\n"
            "- 每个 variant 的 nanobanana_prompt 必须以【只改变人物姿势，背景/裤子/鞋子/配件完全不变】开头\n"
            "- 每个 variant 的 pose 字段必须是与服装气质匹配且彼此明显不同的姿势描述\n"
            "- scene/lighting/camera 字段在所有 variant 中保持完全相同\n\n"
        )

    # Lookbook 模式专属：要求场景/姿势/光影各方案明显不同
    lookbook_diversity = ""
    if mode == "lookbook":
        lookbook_diversity = (
            "【Lookbook 多样性强制要求】\n"
            f"- 共 {k_variants} 个方案，每个方案的 scene / pose / lighting 必须明显不同\n"
            "- 禁止两个方案使用相同或高度相似的场景、姿势\n"
            "- 场景之间要有明显气质差异，例如：室内棚拍 vs 街头户外、日间自然光 vs 夜间霓虹、"
            "工业风 vs 自然风，以此类推\n"
            "- 姿势之间要有明显动势差异：站立 vs 行走 vs 坐姿，正面 vs 侧面 vs 背面等\n\n"
        )

    user_text = (
        "给你两张图片：第一张是人物模特，第二张是衣服。\n"
        f"{style_context}"
        f"{lookbook_diversity}"
        f"{pose_mode_extra}"
        "任务：\n"
        "1) 分析人物风格与特征（气质关键词、身材轮廓、肤色冷暖倾向），并给出【不要改变】的列表。\n"
        "2) 分析衣服：类别、版型、材质、风格标签、主色/辅色、细节特征。\n"
        f"3) 生成 {spec['label']} variants 数组，共 {k_variants} 个方案：\n"
        "   - 至少 1 个为【姿势不变标准换衣，只改变上传衣服的部分】\n"
        "   - 其余方案：根据衣服风格DNA，生成与该衣服气质完全匹配的场景/姿势/光影\n"
        "   - 每个方案必须包含：pose/wearing/scene/camera/lighting\n"
        "   - 每个方案必须给出 nanobanana_prompt（可直接喂给图像编辑API）和 negative_prompt\n"
        f"4) 模式补充要求：{spec['guidance']}\n"
        "5) 强约束：保持模特身份一致（脸不变），衣服图案/颜色/材质/Logo 不乱改，真实摄影质感。\n"
        f"user_prompt: {user_prompt or '无'}\n"
        f"mode: {mode}\n"
        "只输出 JSON。"
    )
    return system_text, user_text


def build_default_plan(
    k_variants: int, mode: str, user_prompt: str | None
) -> dict[str, Any]:
    """兜底 plan，保证可用"""
    spec = get_mode_spec(mode)
    variants: list[dict[str, Any]] = []

    base_plan = {
        "person": {
            "vibe_keywords": ["干净", "利落"],
            "body_silhouette": "正常体型",
            "skin_tone": "中性",
            "do_not_change": ["脸部五官", "发型", "肤色"],
        },
        "garment": {
            "category": "上装",
            "style_tags": ["基础", "街头"],
            "fit": "标准版型",
            "material_guess": ["棉"],
            "main_colors": ["主色保持"],
            "details": ["logo/图案保持不变"],
        },
        "base_constraints": {
            "identity_lock": "保持模特身份一致（脸不变）",
            "garment_lock": "衣服颜色/材质/图案/Logo保持不变",
            "quality": "真实摄影质感",
            "avoid": ["脸部变形", "衣服细节错乱", "质感塑料化"],
        },
        "variants": variants,
    }

    # lookbook 模式随机无重复选取，确保兜底场景也有多样性
    def _pick(lst: list, n: int) -> list:
        if n <= len(lst):
            return random.sample(lst, n)
        # 数量超出列表时：先全取一遍，剩余继续随机补
        result = lst[:]
        while len(result) < n:
            result += random.sample(lst, min(len(lst), n - len(result)))
        return result[:n]

    if mode == "lookbook":
        scenes   = _pick(spec["scene_list"],   k_variants)
        poses    = _pick(spec["pose_list"],    k_variants)
        cameras  = _pick(spec["camera_list"],  k_variants)
        lightings = _pick(spec["lighting_list"], k_variants)
        wearings  = _pick(spec["wearing_list"],  k_variants)
        # 第一个永远是标准换衣（棚拍）
        scenes[0]    = spec["scene_list"][0]
        poses[0]     = "正面站立，姿势不变"
        cameras[0]   = spec["camera_list"][0]
        lightings[0] = spec["lighting_list"][0]
        wearings[0]  = "标准穿法"
    else:
        scenes    = [spec["scene_list"][i % len(spec["scene_list"])]    for i in range(k_variants)]
        poses     = [spec["pose_list"][i % len(spec["pose_list"])]     for i in range(k_variants)]
        cameras   = [spec["camera_list"][i % len(spec["camera_list"])]  for i in range(k_variants)]
        lightings = [spec["lighting_list"][i % len(spec["lighting_list"])] for i in range(k_variants)]
        wearings  = [spec["wearing_list"][i % len(spec["wearing_list"])]   for i in range(k_variants)]

    for idx in range(k_variants):
        is_standard = idx == 0
        pose    = poses[idx]
        scene   = scenes[idx]
        camera  = cameras[idx]
        lighting = lightings[idx]
        wearing  = wearings[idx]
        title = "标准换衣" if is_standard else f"{spec['title_prefix']} {idx + 1}"
        styling = "按衣服风格搭配"
        if user_prompt:
            styling = f"{styling}，{user_prompt}"
        variant = {
            "id": f"v{idx + 1}",
            "title": title,
            "pose": pose,
            "wearing": "标准穿法" if is_standard else wearing,
            "styling": styling,
            "scene": scene,
            "camera": camera,
            "lighting": lighting,
            "nanobanana_prompt": "",
            "negative_prompt": "人脸变形，服装图案错误，材质失真，过度美颜，涂抹感",
        }
        variants.append(variant)

    return base_plan


def apply_mode_constraints(plan: dict[str, Any], mode: str) -> dict[str, Any]:
    """根据模式做轻量约束，确保差异化"""
    spec = get_mode_spec(mode)
    variants = plan.get("variants", [])
    if not isinstance(variants, list):
        return plan

    for variant in variants:
        if not isinstance(variant, dict):
            continue
        if spec.get("fixed_scene"):
            variant["scene"] = spec["fixed_scene"]
        if spec.get("fixed_camera"):
            variant["camera"] = spec["fixed_camera"]
        if spec.get("fixed_lighting"):
            variant["lighting"] = spec["fixed_lighting"]
        if spec.get("force_wearing"):
            variant["wearing"] = spec["force_wearing"]

    return plan
