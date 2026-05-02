#   Gemini 2.5 Flash Image 文生图
通过 Gemini 2.5 Flash Image 模型快速生成图像，支持 10 种宽高比，固定 1K 分辨率。

接口地址

https://www.dmxapi.cn/v1beta/models/gemini-2.5-flash-image:generateContent
注意：

需要升级谷歌sdk为最新版

模型名称
Gemini 2.5 Flash Image
模型名称: gemini-2.5-flash-image
特点: 快速生成，固定 1K 分辨率
示例代码

SDK

request

"""
DMXAPI Gemini 2.5 Flash Image 图像生成示例
使用 Google Gemini API 生成图像，并保存到本地 output 文件夹
"""

from google import genai
from google.genai import types
import os
from datetime import datetime

# ============================================================================
# 配置部分
# ============================================================================

# DMXAPI 密钥和基础 URL
api_key = "sk-************************************"  # 替换为你的 DMXAPI 密钥
BASE_URL = "https://www.dmxapi.cn"

# 创建 Gemini 客户端
client = genai.Client(api_key=api_key, http_options={'base_url': BASE_URL})

# ============================================================================
# 图像生成提示词
# ============================================================================

# 定义图像生成的提示词
prompt = (
    "Visualize the current weather forecast for the next 5 days in ShangHi as a clean, modern weather chart. Add a visual on what I should wear each day"
)

# ============================================================================
# 调用 DMXAPI 生成图像
# ============================================================================

response = client.models.generate_content(
    # 模型名称
    model="gemini-2.5-flash-image",

    # 输入内容
    contents=[prompt],

    # 生成配置
    config=types.GenerateContentConfig(
        # image_config: 图像配置选项
        image_config=types.ImageConfig(
            # aspect_ratio: 设置输出图片的宽高比
            #
            # ┌──────────┬─────────────┬────────┐
            # │ 宽高比    │ 分辨率      │ 令牌    │
            # ├──────────┼─────────────┼────────┤
            # │ 1:1      │ 1024x1024   │ 1290   │
            # │ 2:3      │ 832x1248    │ 1290   │
            # │ 3:2      │ 1248x832    │ 1290   │
            # │ 3:4      │ 864x1184    │ 1290   │
            # │ 4:3      │ 1184x864    │ 1290   │
            # │ 4:5      │ 896x1152    │ 1290   │
            # │ 5:4      │ 1152x896    │ 1290   │
            # │ 9:16     │ 768x1344    │ 1290   │
            # │ 16:9     │ 1344x768    │ 1290   │
            # │ 21:9     │ 1536x672    │ 1290   │
            # └──────────┴─────────────┴────────┘
            #
            aspect_ratio="1:1",
        ),
    )
)

# ============================================================================
# 处理响应并保存图像
# ============================================================================

for part in response.parts:
    # 处理文本响应（如果有）
    if part.text is not None:
        print(part.text)

    # 处理图像响应
    elif part.inline_data is not None:
        # 确保 output 文件夹存在
        os.makedirs("output", exist_ok=True)

        # 生成带时间戳的文件名
        # 格式: generated_image_20250121_143052.png (年月日_时分秒)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"output/generated_image_{timestamp}.png"

        # 将响应数据转换为 PIL Image 对象
        image = part.as_image()

        # 保存图像到文件
        image.save(filename)

        # 输出保存成功的提示信息
        print(f"图片已保存到 {filename}")
返回示例

SDK

request

图片已保存到 output/generated_image_20260227_183649.png
# Gemini 2.5 Flash Image 图片编辑
使用 Gemini 2.5 Flash Image 模型进行快速图片编辑

接口地址

https://www.dmxapi.cn/v1beta/models/gemini-2.5-flash-image:generateContent
注意：

需要升级谷歌sdk为最新版

模型名称
gemini-2.5-flash-image：快速图像编辑，固定 1K 分辨率
示例代码

SDK

request

"""
DMXAPI Gemini 2.5 Flash Image 图像修改示例
使用 Google Gemini API 修改图像，并保存到本地 output 文件夹
"""

from google import genai
from google.genai import types
from PIL import Image
import os
from datetime import datetime

# ============================================================================
# 配置部分
# ============================================================================

# DMXAPI 密钥和基础 URL
api_key = "sk-***********************************"  # 替换为你的 DMXAPI 密钥
BASE_URL = "https://www.dmxapi.cn"

# 输入图像路径
INPUT_IMAGE_PATH = "./b1.png"  # 替换为你要修改的图片路径

# 创建 Gemini 客户端
client = genai.Client(api_key=api_key, http_options={'base_url': BASE_URL})

# ============================================================================
# 图像修改提示词
# ============================================================================

# 读取要修改的图像
image = Image.open(INPUT_IMAGE_PATH)

# 定义图像修改的提示词
prompt = (
    "让图里的人手里拿着鲜花"
)

# ============================================================================
# 调用 DMXAPI 修改图像
# ============================================================================

response = client.models.generate_content(
    # 模型名称
    model="gemini-2.5-flash-image",

    # 输入内容：提示词 + 原始图像
    contents=[prompt, image],

    # 生成配置
    config=types.GenerateContentConfig(
        # image_config: 图像配置选项
        image_config=types.ImageConfig(
            # aspect_ratio: 设置输出图片的宽高比
            #
            # ┌──────────┬─────────────┬────────┐
            # │ 宽高比    │ 分辨率      │ 令牌    │
            # ├──────────┼─────────────┼────────┤
            # │ 1:1      │ 1024x1024   │ 1290   │
            # │ 2:3      │ 832x1248    │ 1290   │
            # │ 3:2      │ 1248x832    │ 1290   │
            # │ 3:4      │ 864x1184    │ 1290   │
            # │ 4:3      │ 1184x864    │ 1290   │
            # │ 4:5      │ 896x1152    │ 1290   │
            # │ 5:4      │ 1152x896    │ 1290   │
            # │ 9:16     │ 768x1344    │ 1290   │
            # │ 16:9     │ 1344x768    │ 1290   │
            # │ 21:9     │ 1536x672    │ 1290   │
            # └──────────┴─────────────┴────────┘
            #
            aspect_ratio="1:1",
        ),
    )
)

# ============================================================================
# 处理响应并保存修改后的图像
# ============================================================================

# 检查响应是否有效
if not response.candidates:
    print("API 未返回任何候选结果。")
    print(f"完整响应: {response}")
elif response.candidates[0].finish_reason:
    print(f"结束原因: {response.candidates[0].finish_reason}")

if response.parts is None:
    print("响应中没有内容 (response.parts 为 None)，可能原因：")
    print("  1. 请求被安全过滤器拦截")
    print("  2. 模型/参数组合不支持")
    print("  3. API 返回了空响应")
    print(f"完整响应: {response}")
    exit(1)

for part in response.parts:
    # 处理文本响应（如果有）
    if part.text is not None:
        print(part.text)

    # 处理图像响应
    elif part.inline_data is not None:
        # 确保 output 文件夹存在
        os.makedirs("output", exist_ok=True)

        # 生成带时间戳的文件名
        # 格式: edited_image_20250121_143052.png (年月日_时分秒)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"output/edited_image_{timestamp}.png"

        # 将响应数据转换为 PIL Image 对象
        image = part.as_image()

        # 保存图像到文件
        image.save(filename)

        # 输出保存成功的提示信息
        print(f"修改后的图片已保存到 {filename}")
返回示例

SDK

request

结束原因: FinishReason.STOP
修改后的图片已保存到 output/edited_image_20260227_165150.png

Gemini 2.5 Flash Image 多图融合
多图融合功能允许你将多张图像智能融合生成新图像，支持对象合成、场景混合等多种创意应用。通过简单的提示词即可实现复杂的图像合成效果。

接口地址

https://www.dmxapi.cn/v1beta/models/gemini-2.5-flash-image:generateContent
注意：

需要升级谷歌sdk为最新版

模型名称
gemini-2.5-flash-image：固定 1K 分辨率，快速生成，适合快速原型设计和实时应用
示例代码

SDK

request

"""
DMXAPI Gemini 2.5 Flash Image 多图融合示例
使用 Google Gemini API 将多张图像融合生成新图像，并保存到本地 output 文件夹
"""

from google import genai
from google.genai import types
from PIL import Image
import os
from datetime import datetime

# ============================================================================
# 配置部分
# ============================================================================

# DMXAPI 密钥和基础 URL
api_key = "sk-*********************************************"  # 替换为你的 DMXAPI 密钥
BASE_URL = "https://www.dmxapi.cn"

INPUT_IMAGE_PATHS = [
    "output/generated_image_20251121_170850.png",  # 替换为你的图片路径
    "test/example.jpg",
]

# 创建 Gemini 客户端
client = genai.Client(api_key=api_key, http_options={'base_url': BASE_URL})

# ============================================================================
# 多图融合提示词
# ============================================================================

# 读取所有要融合的图像
images = [Image.open(path) for path in INPUT_IMAGE_PATHS]

# 定义多图融合的提示词
prompt = (
    "让第二张图的计算器在第一张图中吃饭"
)

# ============================================================================
# 调用 DMXAPI 融合图像
# ============================================================================

response = client.models.generate_content(
    # 模型名称
    model="gemini-2.5-flash-image",

    contents=[prompt] + images,

    # 生成配置
    config=types.GenerateContentConfig(
        # image_config: 图像配置选项
        image_config=types.ImageConfig(
            # aspect_ratio: 设置输出图片的宽高比（注意：使用下划线命名）
            #
            # ┌──────────┬─────────────┬────────┐
            # │ 宽高比    │ 分辨率      │ 令牌    │
            # ├──────────┼─────────────┼────────┤
            # │ 1:1      │ 1024x1024   │ 1290   │
            # │ 2:3      │ 832x1248    │ 1290   │
            # │ 3:2      │ 1248x832    │ 1290   │
            # │ 3:4      │ 864x1184    │ 1290   │
            # │ 4:3      │ 1184x864    │ 1290   │
            # │ 4:5      │ 896x1152    │ 1290   │
            # │ 5:4      │ 1152x896    │ 1290   │
            # │ 9:16     │ 768x1344    │ 1290   │
            # │ 16:9     │ 1344x768    │ 1290   │
            # │ 21:9     │ 1536x672    │ 1290   │
            # └──────────┴─────────────┴────────┘
            #
            aspect_ratio="16:9",
        ),
    )
)

# ============================================================================
# 处理响应并保存融合后的图像
# ============================================================================

for part in response.parts:
    # 处理文本响应（如果有）
    if part.text is not None:
        print(part.text)

    # 处理图像响应
    elif part.inline_data is not None:
        # 确保 output 文件夹存在
        os.makedirs("output", exist_ok=True)

        # 生成带时间戳的文件名
        # 格式: fused_image_20250121_143052.png (年月日_时分秒)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"output/fused_image_{timestamp}.png"

        # 将响应数据转换为 PIL Image 对象
        image = part.as_image()

        # 保存图像到文件
        image.save(filename)

        # 输出保存成功的提示信息
        print(f"融合后的图片已保存到 {filename}")
返回示例

SDK

request

融合后的图片已保存到 output/fused_image_20251210_111850.png

Gemini 2.5 Flash Image 多轮图片修改 API 文档
Gemini 2.5 Flash Image 的多轮图片修改功能支持你以"对话"的方式来生成并持续调整图片：你可以先用一句话描述想要的画面生成初稿，然后像和设计师沟通一样，在后续轮次里不断补充细节或提出修改要求，例如更换背景、调整风格与色调、添加或删除元素、改变人物姿态与表情等。系统会理解上下文并记住前几轮的修改结果，每一次调整都会基于上一张图继续迭代，因此不需要你反复从头描述。整体上，建议用聊天或多轮对话逐步打磨作品，从"先有大方向"到"再精修细节"，效率更高、效果也更可控。

模型名称
gemini-2.5-flash-image

请求地址

 https://www.dmxapi.cn/v1beta/models/gemini-2.5-flash-image:generateContent
WARNING

注意：请妥善保管API密钥，不要泄露给他人。

图片生成 调用示例

"""
================================================================================
Gemini 2.5 Flash Image 图片生成示例 - 01
================================================================================
功能说明：
    本脚本演示如何使用 Gemini 2.5 Flash Image API 根据文本提示生成图片。
    生成的图片会保存到本地，同时 base64 数据也会保存以供后续多轮对话使用。
================================================================================
"""

import requests
import json
import base64
import os
from datetime import datetime

# ==============================================================================
# 配置区域
# ==============================================================================

# API 请求地址
url = "https://www.dmxapi.cn/v1beta/models/gemini-2.5-flash-image:generateContent"

# API 密钥（请妥善保管，不要泄露）
api_key = "sk-***************************************"

# 请求头配置
headers = {
    "x-goog-api-key": api_key,          # API 认证密钥
    "Content-Type": "application/json"   # 内容类型为 JSON
}

# ==============================================================================
# 请求数据构建
# ==============================================================================
#
# 请求结构说明：
# ┌─────────────────────────────────────────────────────────────────────────────┐
# │  contents        : 对话内容，包含用户的文本提示                              │
# │  generationConfig: 生成配置                                                │
# └─────────────────────────────────────────────────────────────────────────────┘
#

data = {
    # -------------------------------------------------------------------------
    # contents: 对话内容列表
    # -------------------------------------------------------------------------
    "contents": [{
        "role": "user",
        "parts": [
            {"text": "一只可爱的小猫在愉快的玩耍"}  # 图片生成提示词
        ]
    }],

    # -------------------------------------------------------------------------
    # generationConfig: 生成配置
    # -------------------------------------------------------------------------
    "generationConfig": {
        "responseModalities": ["TEXT", "IMAGE"]  # 响应模态：同时返回文本和图片
    }
}

# ==============================================================================
# 创建 Base64 数据保存目录
# ==============================================================================

base64_folder = "base64_data"
if not os.path.exists(base64_folder):
    os.makedirs(base64_folder)
    print(f"已创建目录: {base64_folder}")

# ==============================================================================
# 发送 API 请求
# ==============================================================================

print("=" * 60)
print("正在发送请求到 Gemini API...")
print("=" * 60)

response = requests.post(url, headers=headers, json=data)
result = response.json()

if "candidates" in result:
    print("\n" + "=" * 60)
    print("响应解析成功！")
    print("=" * 60 + "\n")

    for candidate in result["candidates"]:
        if "content" in candidate and "parts" in candidate["content"]:
            for part in candidate["content"]["parts"]:
                # -------------------------------------------------------------
                # 处理文本部分
                # -------------------------------------------------------------
                if "text" in part:
                    print("+" + "-" * 58 + "+")
                    print("| 文本内容                                                 |")
                    print("+" + "-" * 58 + "+")
                    print(part["text"])
                    print("+" + "-" * 58 + "+\n")

                # -------------------------------------------------------------
                # 处理图片部分（Base64 格式）
                # -------------------------------------------------------------
                if "inlineData" in part:
                    mime_type = part["inlineData"].get("mimeType", "image/png")
                    base64_data = part["inlineData"].get("data", "")

                    # 生成带时间戳的文件名
                    # 格式：gemini_image_YYYYMMDD_HHMMSS.png
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    extension = mime_type.split("/")[-1]
                    filename = f"gemini_image_{timestamp}.{extension}"

                    # 解码 Base64 数据并保存图片到本地
                    image_data = base64.b64decode(base64_data)
                    with open(filename, "wb") as f:
                        f.write(image_data)

                    # 保存 Base64 数据到文件（供多轮对话使用）
                    base64_filename = os.path.join(base64_folder, f"gemini_base64_{timestamp}.txt")
                    with open(base64_filename, "w", encoding="utf-8") as f:
                        f.write(base64_data)

                    print("+" + "-" * 58 + "+")
                    print("| 图片信息                                                 |")
                    print("+" + "-" * 58 + "+")
                    print(f"| 图片文件: {filename:<46} |")
                    print(f"| Base64文件: {base64_filename:<44} |")
                    print(f"| MIME类型: {mime_type:<46} |")
                    print(f"| 数据长度: {len(base64_data):,} 字符{' ' * (39 - len(f'{len(base64_data):,}'))} |")
                    print("+" + "-" * 58 + "+")
                    print("| 图片和 Base64 数据已成功保存！                            |")
                    print("+" + "-" * 58 + "+\n")

                # -------------------------------------------------------------
                # 处理图片部分（URL 格式）
                # -------------------------------------------------------------
                if "fileData" in part:
                    file_uri = part["fileData"].get("fileUri", "")
                    mime_type = part["fileData"].get("mimeType", "")

                    print("+" + "-" * 58 + "+")
                    print("| 图片链接                                                 |")
                    print("+" + "-" * 58 + "+")
                    print(f"| URL: {file_uri[:50]:<52} |")
                    print(f"| MIME类型: {mime_type:<46} |")
                    print("+" + "-" * 58 + "+\n")

else:
    # -------------------------------------------------------------------------
    # 错误处理：响应中没有 candidates 字段
    # -------------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("响应异常，完整内容如下：")
    print("=" * 60)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("=" * 60 + "\n")

# ==============================================================================
# 脚本结束
# ==============================================================================
print("\n" + "=" * 60)
print("脚本执行完毕")
print("=" * 60)
返回示例
成功响应将返回包含向量数据的JSON对象：


============================================================
正在发送请求到 Gemini API...
============================================================

============================================================
响应解析成功！
============================================================

+----------------------------------------------------------+
| 图片信息                                                 |
+----------------------------------------------------------+
| 图片文件: gemini_image_20260227_192948.png               |
| Base64文件: base64_data\gemini_base64_20260227_192948.txt |
| MIME类型: image/png                                      |
| 数据长度: 2,407,096 字符                               |
+----------------------------------------------------------+
| 图片和 Base64 数据已成功保存！                            |
+----------------------------------------------------------+


============================================================
脚本执行完毕
============================================================
多轮对话 示例代码

"""
================================================================================
Gemini 2.5 Flash Image 多轮图片修改示例 - 02
================================================================================
功能说明：
    本脚本演示如何使用 Gemini 2.5 Flash Image API 进行多轮对话式图片编辑。
    通过传递历史对话和之前生成的图片，可以让 AI 在原图基础上进行修改。
================================================================================
"""
import requests
import json
import base64
from datetime import datetime

# ==============================================================================
# 配置区域
# ==============================================================================

# API 请求地址
url = "https://www.dmxapi.cn/v1beta/models/gemini-2.5-flash-image:generateContent"

# API 密钥（请妥善保管，不要泄露）
api_key = "sk-*********************************************"

# 上一轮生成的图片 base64 数据文件路径
base64_file = r"base64_data\gemini_base64_20260129_181804.txt"
with open(base64_file, "r") as f:
    previous_image_data = f.read().strip()

# 请求头配置
headers = {
    "x-goog-api-key": api_key,          # API 认证密钥
    "Content-Type": "application/json"   # 内容类型为 JSON
}


# ==============================================================================
# 多轮对话数据构建
# ==============================================================================
#
# 对话结构说明：
# ┌─────────────────────────────────────────────────────────────────────────────┐
# │  第 1 轮 (user)  : 用户发起初始请求，要求创建信息图                           │
# │  第 2 轮 (model) : 模型返回生成的图片（base64 格式）                          │
# │  第 3 轮 (user)  : 用户基于上一轮图片，提出修改要求                           │
# └─────────────────────────────────────────────────────────────────────────────┘
#
# 注意：<PREVIOUS_IMAGE_DATA> 需要替换为实际的 base64 编码图片数据
#

data = {
    # -------------------------------------------------------------------------
    # contents: 对话内容列表，按时间顺序排列
    # -------------------------------------------------------------------------
    "contents": [
        # 第 1 轮：用户初始请求
        {
            "role": "user",
            "parts": [{"text": "一只可爱的小猫在愉快的玩耍"}]
        },
        # 第 2 轮：模型返回的图片（需要填入上一次生成的图片数据）
        {
            "role": "model",
            "parts": [{
                "inline_data": {
                    "mime_type": "image/jpeg",           # 图片 MIME 类型
                    "data": previous_image_data          # 从文件读取的 base64 数据
                }
            }]
        },
        # 第 3 轮：用户的修改请求
        {
            "role": "user",
            "parts": [{"text": "给这个小猫加一个红色的帽子，帽子上面写上几个文字'Jonathan'"}]
        }
    ],

    # -------------------------------------------------------------------------
    # generationConfig: 生成配置
    # -------------------------------------------------------------------------
    "generationConfig": {
        # 响应模态：同时返回文本和图片
        "responseModalities": ["TEXT", "IMAGE"],

        # 图片配置
        "imageConfig": {
            "aspectRatio": "16:9"           # 宽高比：16:9（适合横屏展示）
        }
    }
}


# ==============================================================================
# 发送 API 请求
# ==============================================================================

print("=" * 60)
print("正在发送请求到 Gemini API...")
print("=" * 60)

response = requests.post(url, headers=headers, json=data)
result = response.json()

if "candidates" in result:
    print("\n" + "=" * 60)
    print("响应解析成功！")
    print("=" * 60 + "\n")

    for candidate in result["candidates"]:
        if "content" in candidate and "parts" in candidate["content"]:
            for part in candidate["content"]["parts"]:

                # -------------------------------------------------------------
                # 处理文本部分
                # -------------------------------------------------------------
                if "text" in part:
                    print("+" + "-" * 58 + "+")
                    print("| 文本内容                                                 |")
                    print("+" + "-" * 58 + "+")
                    print(part["text"])
                    print("+" + "-" * 58 + "+\n")

                # -------------------------------------------------------------
                # 处理图片部分（Base64 格式）
                # -------------------------------------------------------------
                if "inlineData" in part:
                    mime_type = part["inlineData"].get("mimeType", "image/png")
                    base64_data = part["inlineData"].get("data", "")

                    # 生成带时间戳的文件名
                    # 格式：gemini_image_YYYYMMDD_HHMMSS.png
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    extension = mime_type.split("/")[-1]
                    filename = f"gemini_image_{timestamp}.{extension}"

                    # 解码 Base64 数据并保存到本地文件
                    image_data = base64.b64decode(base64_data)
                    with open(filename, "wb") as f:
                        f.write(image_data)

                    print("+" + "-" * 58 + "+")
                    print("| 图片信息                                                 |")
                    print("+" + "-" * 58 + "+")
                    print(f"| 文件名称: {filename:<46} |")
                    print(f"| MIME类型: {mime_type:<46} |")
                    print(f"| 数据长度: {len(base64_data):,} 字符{' ' * (39 - len(f'{len(base64_data):,}'))} |")
                    print("+" + "-" * 58 + "+")
                    print("| 图片已成功保存到本地！                                    |")
                    print("+" + "-" * 58 + "+\n")

                # -------------------------------------------------------------
                # 处理图片部分（URL 格式）
                # -------------------------------------------------------------
                if "fileData" in part:
                    file_uri = part["fileData"].get("fileUri", "")
                    mime_type = part["fileData"].get("mimeType", "")

                    print("+" + "-" * 58 + "+")
                    print("| 图片链接                                                 |")
                    print("+" + "-" * 58 + "+")
                    print(f"| URL: {file_uri[:50]:<52} |")
                    print(f"| MIME类型: {mime_type:<46} |")
                    print("+" + "-" * 58 + "+\n")

else:
    # -------------------------------------------------------------------------
    # 错误处理：响应中没有 candidates 字段
    # -------------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("响应异常，完整内容如下：")
    print("=" * 60)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("=" * 60 + "\n")


# ==============================================================================
# 脚本结束
# ==============================================================================
print("\n" + "=" * 60)
print("脚本执行完毕")
print("=" * 60)
返回示例

============================================================
正在发送请求到 Gemini API...
============================================================

============================================================
响应解析成功！
============================================================

+----------------------------------------------------------+
| 图片信息                                                 |
+----------------------------------------------------------+
| 文件名称: gemini_image_20260227_193304.png               |
| MIME类型: image/png                                      |
| 数据长度: 8,724,604 字符                               |
+----------------------------------------------------------+
| 图片已成功保存到本地！                                    |
+----------------------------------------------------------+


============================================================
脚本执行完毕
============================================================

🌐 API 统一请求格式
📖 概述
所有模型（包括非 OpenAI 模型）的请求格式已统一转换为 OpenAI 格式，几乎兼容本站的所有模型。

🌐接口地址
https://www.dmxapi.cn/v1/chat/completions

🎯 使用方法
只需替换 "model" 参数为您需要的模型名称即可。

ℹ️ 基础信息
项目	说明
Base URL	https://www.dmxapi.cn
认证方式	API Key (Token)
请求方法	POST
接口路径	/v1/chat/completions
💻 Python 示例代码

"""
DMXAPI 对话接口调用示例
功能：使用 gpt-5-mini 模型进行智能对话
"""

import json
import requests

# ==================== API 配置 ====================

# API 接口地址
url = "https://www.dmxapi.cn/v1/chat/completions"

# 请求头配置
headers = {
    "Authorization": "sk-**********************************",  # 替换为你的 DMXAPI 令牌
    "Content-Type": "application/json"
}

# ==================== 请求参数 ====================

# 构造请求数据
payload = {
    "model": "gpt-5-mini",  # 选择使用的模型
    "messages": [
        {
            "role": "system", 
            "content": "You are a helpful assistant."  # 系统提示词：定义 AI 助手的角色
        },
        {
            "role": "user", 
            "content": "周树人和鲁迅是兄弟吗？"  # 用户问题
        }
    ]
}

# ==================== 发送请求 ====================

try:
    # 发送 POST 请求到 API
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    response.raise_for_status()  # 检查 HTTP 错误
    
    # 输出响应结果
    print("=" * 50)
    print("API 响应结果：")
    print("=" * 50)
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    
except requests.exceptions.RequestException as e:
    # 异常处理
    print(f"❌ 请求失败: {e}")
提示

实际使用时请将 sk-********************************** 替换为你的真实 API 密钥

📤 返回示例
成功响应结构

==================================================
API 响应结果：
==================================================
{
  "choices": [
    {
      "finish_reason": "stop",
      "index": 0,
      "logprobs": null,
      "message": {
        "annotations": [],
        "content": "不是兄弟。周树人就是鲁迅的本名／原名，鲁迅是他的笔名。鲁迅（周树人，1881—1936）是中国现代著名作家、思想家。",
        "refusal": null,
        "role": "assistant"
      }
    }
  ],
  "created": 1762512121,
  "id": "chatcmpl-CZECnsYuphVShao4a6XlUxvzFd5yi",
  "model": "gpt-5-mini-2025-08-07",
  "object": "chat.completion",
  "system_fingerprint": null,
  "usage": {
    "completion_tokens": 378,
    "completion_tokens_details": {
      "accepted_prediction_tokens": 0,
      "audio_tokens": 0,
      "reasoning_tokens": 320,
      "rejected_prediction_tokens": 0
    },
    "prompt_tokens": 27,
    "prompt_tokens_details": {
      "audio_tokens": 0,
      "cached_tokens": 0
    },
    "total_tokens": 405
  }
}


Openai 请求格式 - 网络图片分析 API 文档
📖 接口说明
通过多模态 AI 模型分析图片内容,理解图片、提取图片信息

提示

OpenAI 出了新的 responses 接口,兼容性更好
老接口在部分照片格式兼容上有一定的问题
新接口文档:http://doc.dmxapi.cn/res-url-image.html

🔗 接口地址

https://www.dmxapi.cn/v1/chat/completions
💻 Python 调用示例

"""
图片分析工具 - 使用 Gemini 2.5 Flash 模型进行图片内容分析
============================================================
本脚本演示如何通过 DMX API 调用 Gemini 模型来分析图片内容
适用于图片描述、物体识别、场景理解等应用场景
"""

import requests

# ============================================================
# API 配置区域
# ============================================================
BASE_URL = "https://www.dmxapi.cn/"                                      # API 基础地址
API_ENDPOINT = BASE_URL + "v1/chat/completions"                          # 对话完成接口
API_KEY = "sk-*************************************************"         # API 密钥(请替换为你的密钥)
IMAGE_URL = "https://dmxapi.com/111.jpg"                                 # 待分析图片的 URL 地址

# ============================================================
# 核心功能函数
# ============================================================
def analyze_image(image_url, prompt):
    """
    调用 Gemini 模型分析图片内容
    
    功能说明:
        通过 DMX API 调用 Gemini-2.5-Flash 模型,对指定 URL 的图片进行智能分析
        支持图片描述、物体识别、场景理解等多种分析任务
    
    参数:
        image_url (str): 图片的 URL 地址,需要是公网可访问的链接
        prompt (str): 分析提示词,描述你希望模型如何分析这张图片
    """
    # 构建请求载荷
    payload = {
        "model": "gemini-2.5-flash",                                     # 使用的模型名称
        "messages": [
            {
                "role": "system",                                        # 系统角色:定义助手行为
                "content": [{"type": "text", "text": "你是一个图片分析助手。"}]
            },
            {
                "role": "user",                                          # 用户角色:发送分析请求
                "content": [
                    {"type": "image_url", "image_url": {"url": image_url}},  # 图片 URL
                    {"type": "text", "text": prompt}                     # 分析提示词
                ]
            }
        ],
        "temperature": 0.1                                               # 温度参数:0.1 使输出更确定性和专业
    }
    
    # 构建请求头
    headers = {
        "Content-Type": "application/json",                              # 内容类型:JSON 格式
        "Authorization": f"{API_KEY}"                             # 授权令牌
    }

    # 发送 API 请求并处理响应
    try:
        response = requests.post(API_ENDPOINT, headers=headers, json=payload)
        response.raise_for_status()                                      # 检查 HTTP 状态码
        return response.json()["choices"][0]["message"]["content"]       # 提取分析结果文本
    except Exception as e:
        print(f"❌ 请求失败: {e}")                                        # 错误提示
        return None

# ============================================================
# 程序入口
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("开始分析图片...")
    print("=" * 60)
    
    # 调用图片分析函数
    result = analyze_image(IMAGE_URL, "请描述这张图片的内容")
    
    # 输出分析结果
    if result:
        print("✅ 分析结果:")
        print("-" * 60)
        print(result)
        print("-" * 60)
    else:
        print("❌ 图片分析失败,请检查配置和网络连接")
📤 返回示例

============================================================
开始分析图片...
============================================================
✅ 分析结果:
------------------------------------------------------------
这张图片展示了一张手写的清单或笔记,内容如下:

*   **第一项:** 680,1560 x 2个木饰面
*   **第二项:** 680,1560 x 1个利流政 (这部分文字可能识别有误,"利流政"看起来不太像常见的词语)
*   **第三项:** 710,(800 x 1个利院的) (同样,"利院的"可能识别有误)
*   **第四项:** 1240 木饰面
*   **第五项:** 700,1900个平面、底面不要,这是落地方
*   **第六项:** 795,2030 午市图像地门 (这部分文字也可能识别有误,"午市图像地门"看起来不太像常见的词语)

每项前面都有一个手绘的方框,方框旁边通常是数字,然后是具体的描述。图片底部有"Memo No."和"Date"的字样,以及一些日历相关的标记。
------------------------------------------------------------