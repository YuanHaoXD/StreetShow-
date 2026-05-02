# StreetShow 运行流程（中文版）

本文档描述 StreetShow 项目的运行流程、文件职责与 API 使用方式。

## 0) 快速索引
- 后端入口：main.py -> backend/app.py
- 前端入口：frontend/app/page.tsx
- 后端接口：
  - POST /api/process
  - POST /api/process-advanced
  - GET  /health
- 静态图片：/assets/* -> temp/assets/

## 1) 启动流程
- 后端：
  1) main.py 调用 create_app()
  2) backend/app.py 设置 CORS、挂载 /assets、注册路由
  3) backend/core/model.py 在导入时加载 Qwen 模型与 processor
- 前端：
  - frontend/app/page.tsx 为主页面（App Router）

## 2) 前端流程（详细）
1) 用户上传人物图 + 衣物图
   - 组件：frontend/components/ImageUploader.tsx
   - 生成预览并支持取消
2) 用户选择模式（左侧功能栏）
   - 标准试衣 -> /api/process
   - Lookbook / Pose / Try-on+ -> /api/process-advanced
3) 用户点击按钮
   - 页面逻辑：frontend/app/page.tsx -> handleSubmit()
   - 构造 FormData 并发起 fetch()
4) UI 状态
   - 请求中显示转圈
   - 多图结果用卡片网格展示
   - 点击卡片弹窗查看大图 + prompt

## 3) 后端流程：/api/process（标准试衣）
入口：backend/routers/process.py -> process_images()

步骤：
1) 读取上传文件（UploadFile）
2) sanitize_and_save_image() 处理与保存输入
   - 文件：backend/utils/images.py
   - 校验大小、修正 EXIF、转 RGB、缩放、保存 JPEG
3) 并行运行 Qwen 与 Nanobanana（受信号量限制）
   - Qwen：backend/services/qwen.py -> run_qwen_advice()
   - Nano：backend/services/nanobanana.py -> call_nanobanana_api()
4) 保存输出图片到 temp/assets/
5) 返回 JSON：
   - advice
   - tryon_image_url
   - meta
   - tryon_image_data_url（当 RETURN_DATA_URL=1 时）
6) 清理：
   - 删除 temp/uploads/<uuid>
   - cleanup_assets() 清理旧输出

## 4) 后端流程：/api/process-advanced（Lookbook/Pose/Try-on+）
入口：backend/routers/advanced.py -> process_images_advanced()

步骤：
1) 读取上传文件并处理（同标准流程）
2) Qwen 生成结构化 plan JSON
   - backend/services/qwen.py -> build_qwen_plan()
   - JSON 无效时自动修复/兜底
3) Qwen 生成中文建议
   - backend/services/qwen.py -> run_qwen_advice()
4) 对每个 variant：
   - 生成 prompt + negative prompt
   - 调 Nanobanana 生成图片（受信号量限制）
   - 保存图片到 temp/assets/
5) 返回 JSON：
   - advice
   - plan
   - results[]（多图 + prompt）
   - meta（耗时与设备信息）
6) 清理：
   - 删除 temp/uploads/<uuid>
   - cleanup_assets() 清理旧输出

## 5) Prompt 生成与日志位置
- Qwen 计划 prompt：backend/services/qwen.py -> build_qwen_plan()
- variant prompt 拼接：backend/services/qwen.py -> _build_variant_prompt()
- Nanobanana prompt 日志：backend/services/nanobanana.py -> call_nanobanana_api()
- 前端控制台 prompt：frontend/app/page.tsx

## 6) 存储与清理
- 输入：temp/uploads/<uuid>/（请求结束后删除）
- 输出：temp/assets/（按 TTL + 数量清理）

## 7) 并发控制
- backend/core/state.py 定义 SEM（asyncio.Semaphore）
- /api/process 与 /api/process-advanced 都受 SEM 限制

## 8) 文件与函数索引（详细）

### 后端入口
- main.py
  - app = create_app()

- backend/app.py
  - create_app()：初始化 FastAPI + CORS + 静态目录 + 路由 + /health

### 后端 core
- backend/core/config.py
  - 常量：环境变量、路径、限制配置

- backend/core/logging.py
  - setup_logging()：配置日志格式与级别

- backend/core/model.py
  - load_model_and_processor()：加载模型与 processor
  - model / processor：全局单例

- backend/core/state.py
  - SEM：全局并发限制

### 后端 utils
- backend/utils/images.py
  - sanitize_and_save_image()：上传图片处理
  - encode_image_data_url()：可选 base64 输出

- backend/utils/files.py
  - cleanup_assets()：按 TTL 与最大数清理输出图片

### 后端 services
- backend/services/qwen.py
  - run_qwen_advice()：生成中文建议
  - build_qwen_plan()：生成 Lookbook JSON 计划
  - _normalize_plan()：修正/补全 plan
  - _default_plan()：plan 兜底
  - _repair_json_with_qwen()：JSON 修复
  - _extract_json_block()：截取 JSON 文本
  - _try_parse_json()：安全解析 JSON
  - _build_variant_prompt()：生成单条 prompt
  - build_vision_inputs()：视觉输入适配

- backend/services/nanobanana.py
  - call_nanobanana_api()：主调用逻辑（失败降级为 mock）
  - compose_prompt()：合并 prompt 与 negative prompt
  - make_mock_image()：生成 mock 图
  - _extract_inline_image()：解析返回图片
  - _mime_to_ext()：扩展名映射

### 后端 routers
- backend/routers/process.py
  - process_images()：/api/process

- backend/routers/advanced.py
  - process_images_advanced()：/api/process-advanced

### 前端
- frontend/app/page.tsx
  - handleSubmit()：发送请求
  - renderInsight()：显示建议/plan
  - renderResults()：多图展示与弹窗

- frontend/components/ImageUploader.tsx
  - handleFile()：预览与回传
  - handleDrop()：拖拽上传
  - clearFile()：取消图片

- frontend/app/globals.css
  - 霓虹/玻璃/扫描线/加载动画

## 9) API 示例

### /api/process（标准试衣）
请求：

curl -X POST http://localhost:8000/api/process \
  -F "person_image=@/path/to/person.jpg" \
  -F "garment_image=@/path/to/garment.jpg"

响应示例：
{
  "advice": "...",
  "tryon_image_url": "/assets/tryon_xxx.png",
  "meta": {
    "qwen_ms": 1200,
    "nano_ms": 980,
    "device": "cuda:0",
    "nanobanana_used": true,
    "nanobanana_error": null
  },
  "tryon_image_data_url": "data:image/png;base64,..." // RETURN_DATA_URL=1 才会出现
}

### /api/process-advanced（Lookbook）
请求：

curl -X POST http://localhost:8000/api/process-advanced \
  -F "person_image=@/path/to/person.jpg" \
  -F "garment_image=@/path/to/garment.jpg" \
  -F "k_variants=4" \
  -F "mode=lookbook" \
  -F "user_prompt=neon street"

响应示例：
{
  "advice": "...",
  "plan": {
    "person": {"vibe_keywords": ["..."], "body_silhouette": "...", "skin_tone": "...", "do_not_change": ["..."]},
    "garment": {"category": "...", "style_tags": ["..."], "fit": "...", "material_guess": ["..."], "main_colors": ["..."], "details": ["..."]},
    "base_constraints": {"identity_lock": "...", "garment_lock": "...", "quality": "...", "avoid": ["..."]},
    "variants": [
      {"id": "v1", "title": "...", "pose": "...", "wearing": "...", "styling": "...", "scene": "...", "camera": "...", "lighting": "...", "nanobanana_prompt": "...", "negative_prompt": "..."}
    ]
  },
  "results": [
    {
      "variant_id": "v1",
      "title": "...",
      "prompt_used": "...",
      "negative_prompt_used": "...",
      "image_url": "/assets/tryon_abc.png",
      "error": null
    }
  ],
  "meta": {
    "qwen_ms": 2100,
    "nano_ms": 1600,
    "device": "cuda:0",
    "nanobanana_used": true,
    "nanobanana_error": null,
    "k_variants": 4,
    "mode": "lookbook"
  }
}
