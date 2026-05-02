# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**StreetShow** is a virtual try-on + AI styling consultant platform combining:
- **DMXAPI qwen3.5-flash** (cloud API) for visual analysis, style DNA extraction, and plan generation
- **DMXAPI gemini-2.5-flash-image** (cloud API) for image generation/editing
- **FastAPI** backend with 3 try-on endpoints
- **Next.js 14** frontend with 4 mode pages

**Single API key**: Both services use one `DMXAPI_KEY` from `.env`.

## Setup

```bash
# 1. Copy environment template and fill in your key
cp .env.example .env
# Edit .env and set DMXAPI_KEY=your_key_here

# 2. Install backend dependencies
pip install -r requirements.txt

# 3. Run backend (dev)
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 4. Health check
curl http://localhost:8000/health
```

### Frontend
```bash
cd frontend
npm install
npm run dev      # http://localhost:3000
npm run build
npm run lint
```

### Test endpoints
```bash
curl -X POST http://localhost:8000/api/process -F "person_image=@model.jpg" -F "garment_image=@cloth.jpg"
curl -X POST http://localhost:8000/api/process-advanced \
  -F "person_image=@model.jpg" -F "garment_image=@cloth.jpg" \
  -F "mode=lookbook" -F "k_variants=4"
```

## Architecture

### Backend (`backend/`)

**Entry point**: `main.py` (loads `.env` via python-dotenv) → `backend/app.py` creates the FastAPI app, calls `validate_config()`, mounts static `/assets` dir, and registers routers.

**Three API endpoints:**
- `POST /api/process` — basic single-variant try-on (sync)
- `POST /api/process-advanced` — multi-variant try-on with structured plan (sync)
- `POST /api/process-advanced-async` — returns immediately with `job_id` for polling via `GET /api/process-advanced/jobs/{job_id}`

**Request pipeline (advanced):**
1. `utils/images.py` — validates, normalizes (JPEG), saves uploads to `temp/uploads/`
2. `services/qwen.py:analyze_garment_style()` — extracts style DNA from garment image (keywords, vibe, occasions, avoid_scenes)
3. `services/qwen.py:build_qwen_plan()` — uses style DNA + person image to generate structured JSON plan with `k_variants`
4. `services/plan_modes.py:apply_mode_constraints()` — enforces mode-specific field locks
5. `services/nanobanana.py:call_nanobanana_api()` — POSTs person+garment images to DMXAPI Gemini, saves result to `temp/assets/`
6. Background cleanup removes temp files

**Concurrency**: Global semaphore (`backend/core/state.py`) limits to `MAX_CONCURRENT` (default 2) simultaneous API calls.

**Mode constraints** (`services/plan_modes.py`): The `MODE_SPECS` dict defines locked fields per mode:
- `lookbook` — vary pose, scene, and lighting freely (style DNA driven)
- `pose` — lock scene/camera/lighting to studio, vary only pose
- `tryon` — lock everything, minimal changes for stable garment swap

**Async jobs** (`services/job_store.py`): In-memory dict with UUID keys and TTL cleanup. Lost on restart.

**JSON repair**: When Qwen outputs malformed JSON, `_repair_json_with_qwen()` sends raw text back to Qwen to fix it, then falls back to `build_default_plan()` if still invalid.

### DMXAPI Integration

**Vision analysis** (`services/qwen.py`):
- Endpoint: `POST https://www.dmxapi.cn/v1/chat/completions` (OpenAI-compatible)
- Auth header: `Authorization: <DMXAPI_KEY>`
- Model: `qwen3.5-flash` (configurable via `DMXAPI_VL_MODEL`)
- Image format: `{"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,<b64>"}}`

**Image generation** (`services/nanobanana.py`):
- Endpoint: `POST https://www.dmxapi.cn/v1beta/models/gemini-2.5-flash-image:generateContent`
- Auth header: `x-goog-api-key: <DMXAPI_KEY>` ← different header name!
- Response: `candidates[].content.parts[].inlineData.data` (base64 image)
- Aspect ratio: `2:3` (portrait, ~832×1248)

### Frontend (`frontend/`)

**Pages** (`app/`): `page.tsx` redirects to `/lookbook`. Each mode page (`/basic`, `/lookbook`, `/pose`, `/tryon`) renders `components/ModePage.tsx` with a different `mode` prop.

**`ModePage.tsx`** handles all UI logic: uploads, API calls, async polling (2.5s interval), typewriter animation for advice text, results grid with modal preview, and a toggleable plan JSON viewer.

**API targeting**: Frontend calls `http://localhost:8000` by default. Override with `NEXT_PUBLIC_API_URL` in `frontend/.env.local`.

## Key Configuration (`backend/core/config.py`)

| Variable | Default | Notes |
|---|---|---|
| `DMXAPI_KEY` | — | **Required**. Set in `.env` |
| `DMXAPI_VL_MODEL` | `qwen3.5-flash` | Vision analysis model |
| `DMXAPI_IMAGE_MODEL` | `gemini-2.5-flash-image` | Image generation model |
| `DMXAPI_TIMEOUT` | `90` | API request timeout (seconds) |
| `MAX_CONCURRENT` | `2` | Semaphore limit |
| `MAX_UPLOAD_MB` | `10` | Upload size cap |
| `MAX_IMAGE_EDGE` | `2048` | Resize cap |
| `ASSET_TTL_SECONDS` | `3600` | Output image lifetime |
| `JOB_TTL_SECONDS` | `3600` | Async job lifetime |

`validate_config()` raises `RuntimeError` at startup if `DMXAPI_KEY` is missing.

On API failure, `make_mock_image()` returns a gray placeholder so the app doesn't crash.

## Temp Directories

- `temp/uploads/` — incoming images, deleted after each request
- `temp/assets/` — generated output images, served at `/assets/*`, cleaned by TTL + file count limit (`MAX_ASSET_FILES=200`)

## Style DNA Flow

1. User uploads person + garment images
2. `analyze_garment_style(garment_path)` → `{"style_keywords": [...], "occasions": [...], "vibe": "...", "avoid_scenes": [...]}`
3. Style DNA injected into `build_plan_prompt()` via `garment_style` param
4. Qwen generates scene/pose/lighting matched to the garment's actual vibe, not generic defaults
5. `apply_mode_constraints()` enforces mode-specific overrides on top

## 全程使用中文回答