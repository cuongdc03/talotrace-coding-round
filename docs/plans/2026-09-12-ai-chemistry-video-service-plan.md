# AI Chemistry Video Request Service Implementation Plan

> **For Antigravity:** REQUIRED WORKFLOW: Use `.agent/workflows/execute-plan.md` to execute this plan in single-flow mode.

**Goal:** Build a robust, production-grade FastAPI backend service that asynchronously accepts chemistry concept queries, manages job lifecycle state with an async SQLite repository, generates high-quality 1080p educational videos using a quality-gated hybrid pipeline (Pydantic script validation, audio synthesis, procedural chemistry visual composition, and FFmpeg assembly), and serves/streams completed video artifacts.

**Architecture:** Hexagonal / Layered Architecture separating REST API routes, domain models, service orchestration, async worker queue, SQLite persistence (Repository pattern), artifact storage, and a modular video generation pipeline with deterministic fallback guardrails for non-deterministic LLM/media generation.

**Tech Stack:** Python 3.12+, FastAPI, Uvicorn, Pydantic v2, aiosqlite, Pillow, edge-tts / pyttsx3 fallback, FFmpeg/FFprobe, Pytest, Pytest-Asyncio, HTTPX.

---

### Task 1: Environment & Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `app/__init__.py`
- Create: `app/core/config.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`

**Step 1: Write configuration and pyproject.toml**
Define dependencies: `fastapi`, `uvicorn[standard]`, `pydantic`, `pydantic-settings`, `aiosqlite`, `pillow`, `edge-tts`, `pytest`, `pytest-asyncio`, `httpx`.

**Step 2: Install dependencies with uv**
Run: `uv pip install -e .` or `uv sync`
Expected: Successfully installs packages.

**Step 3: Verify environment**
Run: `python3 -c "import fastapi, aiosqlite, PIL; print('Environment OK')"`
Expected: Prints `Environment OK`.

**Step 4: Commit**
Run: `git add pyproject.toml app/ tests/ && git commit -m "chore: scaffold project structure and dependencies"`

---

### Task 2: Core Domain Models & Asynchronous SQLite Repository

**Files:**
- Create: `app/models/job.py`
- Create: `app/models/script.py`
- Create: `app/repositories/base.py`
- Create: `app/repositories/sqlite_job_repository.py`
- Test: `tests/unit/test_job_repository.py`

**Step 1: Write the failing repository unit test**
Test creating a job, querying by ID, updating status and progress, and listing jobs with pagination.

**Step 2: Run test to verify it fails**
Run: `pytest tests/unit/test_job_repository.py -v`
Expected: FAIL (modules not found).

**Step 3: Implement domain models and SQLiteJobRepository**
- Implement `JobStatus` enum: `PENDING`, `VALIDATING`, `GENERATING_SCRIPT`, `SYNTHESIZING_AUDIO`, `RENDERING_VIDEO`, `VERIFYING_ARTIFACT`, `COMPLETED`, `FAILED`.
- Implement `Job` model and `SQLiteJobRepository` with async SQLite table creation and parameterized SQL queries.

**Step 4: Run test to verify it passes**
Run: `pytest tests/unit/test_job_repository.py -v`
Expected: PASS.

**Step 5: Commit**
Run: `git add app/models/ app/repositories/ tests/unit/test_job_repository.py && git commit -m "feat: implement domain models and async sqlite job repository"`

---

### Task 3: Video Generation Pipeline — Concept Classification & Script Generator with Guardrails

**Files:**
- Create: `app/pipeline/classifier.py`
- Create: `app/pipeline/script_generator.py`
- Create: `app/pipeline/templates.py`
- Test: `tests/unit/test_classifier.py`
- Test: `tests/unit/test_script_generator.py`

**Step 1: Write the failing tests for classification and script validation**
- Test classification of the 3 required queries ("How does the pH scale work?", "Why do atoms form covalent bonds?", "What is the difference between ionic and covalent bonding?").
- Test script generation schema compliance, retry on malformed output, and fallback template activation.

**Step 2: Run tests to verify they fail**
Run: `pytest tests/unit/test_classifier.py tests/unit/test_script_generator.py -v`
Expected: FAIL.

**Step 3: Implement ConceptClassifier and ScriptGenerator**
- Implement keyword and semantic matching for chemistry topics.
- Implement `ScriptGenerator` with Pydantic validation of `VideoScript` (title, scenes, narration, visual types).
- Provide rich, scientifically accurate templates for the 3 target concepts.

**Step 4: Run tests to verify they pass**
Run: `pytest tests/unit/test_classifier.py tests/unit/test_script_generator.py -v`
Expected: PASS.

**Step 5: Commit**
Run: `git add app/pipeline/ tests/unit/ && git commit -m "feat: implement concept classifier and guardrailed script generator"`

---

### Task 4: Video Generation Pipeline — Audio Synthesis & Scene Duration Alignment

**Files:**
- Create: `app/pipeline/audio_synthesizer.py`
- Test: `tests/unit/test_audio_synthesizer.py`

**Step 1: Write failing audio synthesis tests**
Test narration synthesis for a scene, file generation, and exact duration measurement using `ffprobe`.

**Step 2: Run test to verify it fails**
Run: `pytest tests/unit/test_audio_synthesizer.py -v`
Expected: FAIL.

**Step 3: Implement AudioSynthesizer**
- Synthesize voice narration using `edge-tts` (with fallback to local speech or silent audio generator for headless/offline testing).
- Calculate exact duration in seconds using `ffprobe`.

**Step 4: Run test to verify it passes**
Run: `pytest tests/unit/test_audio_synthesizer.py -v`
Expected: PASS.

**Step 5: Commit**
Run: `git add app/pipeline/audio_synthesizer.py tests/unit/test_audio_synthesizer.py && git commit -m "feat: implement audio synthesizer and duration alignment"`

---

### Task 5: Video Generation Pipeline — Chemistry Visual Compositor & FFmpeg Stitcher

**Files:**
- Create: `app/pipeline/visual_compositor.py`
- Create: `app/pipeline/video_assembler.py`
- Create: `app/pipeline/pipeline.py`
- Test: `tests/unit/test_visual_compositor.py`
- Test: `tests/unit/test_video_assembler.py`

**Step 1: Write failing visual compositor and video assembler tests**
- Test rendering 1080p graphics for `PH_SCALE`, `COVALENT_BONDS`, and `IONIC_VS_COVALENT`.
- Test stitching images + audio into valid `.mp4` using FFmpeg.
- Test artifact verification gate (non-zero size, valid video/audio streams).

**Step 2: Run tests to verify they fail**
Run: `pytest tests/unit/test_visual_compositor.py tests/unit/test_video_assembler.py -v`
Expected: FAIL.

**Step 3: Implement VisualCompositor, VideoAssembler, and GenerationPipeline**
- Render crisp, educational cards using Pillow (pH gradient scale with indicators, electron sharing Bohr/orbital diagrams, ionic lattice transfer).
- Assemble with FFmpeg into 1080p H.264/AAC MP4.
- Verify output artifact with `ffprobe`.

**Step 4: Run tests to verify they pass**
Run: `pytest tests/unit/test_visual_compositor.py tests/unit/test_video_assembler.py -v`
Expected: PASS.

**Step 5: Commit**
Run: `git add app/pipeline/ tests/unit/ && git commit -m "feat: implement visual compositor and ffmpeg video assembler"`

---

### Task 6: Async Worker Queue & Video Service Layer

**Files:**
- Create: `app/services/worker.py`
- Create: `app/services/video_service.py`
- Test: `tests/unit/test_video_service.py`

**Step 1: Write failing worker and service unit test**
Test job submission, worker processing through states, error handling on corrupt input, and status reporting.

**Step 2: Run test to verify it fails**
Run: `pytest tests/unit/test_video_service.py -v`
Expected: FAIL.

**Step 3: Implement AsyncIO Worker Queue & VideoService**
- Background worker processing jobs with progress updates:
  `PENDING` (0%) $\to$ `VALIDATING` (10%) $\to$ `GENERATING_SCRIPT` (30%) $\to$ `SYNTHESIZING_AUDIO` (55%) $\to$ `RENDERING_VIDEO` (80%) $\to$ `VERIFYING_ARTIFACT` (95%) $\to$ `COMPLETED` (100%).
- Graceful error capturing transitioning to `FAILED` with details.

**Step 4: Run test to verify it passes**
Run: `pytest tests/unit/test_video_service.py -v`
Expected: PASS.

**Step 5: Commit**
Run: `git add app/services/ tests/unit/test_video_service.py && git commit -m "feat: implement async job worker queue and video service layer"`

---

### Task 7: FastAPI REST API Endpoints & Video Streaming

**Files:**
- Create: `app/api/v1/endpoints/jobs.py`
- Create: `app/api/v1/router.py`
- Create: `app/main.py`
- Test: `tests/integration/test_api.py`

**Step 1: Write integration tests for all API endpoints**
- Test `POST /api/v1/videos/jobs` returns 202 and job metadata.
- Test `GET /api/v1/videos/jobs` lists jobs with pagination.
- Test `GET /api/v1/videos/jobs/{id}` returns real-time progress.
- Test `GET /api/v1/videos/jobs/{id}/video` streams video artifact with Range header.
- Test `GET /health` returns healthy system status.

**Step 2: Run tests to verify they fail**
Run: `pytest tests/integration/test_api.py -v`
Expected: FAIL.

**Step 3: Implement FastAPI routes and application**
- Implement routers, exception handlers, and streaming responses with `FileResponse` / custom range generator.
- Setup lifespan handler to start/stop the background worker and database.

**Step 4: Run tests to verify they pass**
Run: `pytest tests/integration/test_api.py -v`
Expected: PASS.

**Step 5: Commit**
Run: `git add app/api/ app/main.py tests/integration/ && git commit -m "feat: implement fastapi endpoints and video streaming router"`

---

### Task 8: End-to-End Generation of the 3 Required Chemistry Videos

**Files:**
- Create: `scripts/generate_sample_videos.py`
- Test: `tests/integration/test_e2e_generation.py`
- Output:
  - `artifacts/videos/ph_scale.mp4`
  - `artifacts/videos/covalent_bonds.mp4`
  - `artifacts/videos/ionic_vs_covalent.mp4`

**Step 1: Write E2E test verifying all 3 required queries generate valid MP4s**
Queries:
1. "How does the pH scale work?"
2. "Why do atoms form covalent bonds?"
3. "What is the difference between ionic and covalent bonding?"

**Step 2: Run script to generate and verify all three videos**
Run: `python3 scripts/generate_sample_videos.py`
Expected: Generates 3 playable 1080p MP4 videos with audio narration and graphics.

**Step 3: Run E2E test suite**
Run: `pytest tests/integration/test_e2e_generation.py -v`
Expected: 3 passed.

**Step 4: Commit generated sample videos and generation script**
Run: `git add scripts/ artifacts/videos/ tests/integration/test_e2e_generation.py && git commit -m "feat: generate and commit sample videos for the 3 required chemistry concepts"`

---

### Task 9: Documentation, Architecture Note, & Verification Walkthrough

**Files:**
- Create: `README.md`
- Create: `docs/ARCHITECTURE.md`
- Create: `docs/DEMO_WALKTHROUGH.md`

**Step 1: Write comprehensive README.md**
Include:
- System overview and features
- Setup and installation instructions (using `uv` or `pip`)
- Running the server (`uvicorn app.main:app`)
- API endpoints documentation with sample `curl` commands
- Running test suite (`pytest`)

**Step 2: Write docs/ARCHITECTURE.md**
Detailed breakdown covering:
- Job lifecycle and state transitions
- Persistence boundary & SQLite repository
- Generation engine boundary & pluggability
- Engineering for non-determinism (schema validation, fallbacks, quality gates)
- Cost analysis ($0.00 default vs cloud APIs)
- Extensibility guide for adding new STEM topics

**Step 3: Write docs/DEMO_WALKTHROUGH.md**
Step-by-step curl walkthrough showing job submission, polling, retrieval, and video playback.

**Step 4: Final verification run**
Run: `pytest -v`
Expected: All tests pass.

**Step 5: Commit**
Run: `git add README.md docs/ && git commit -m "docs: complete readme, architecture note, and demo walkthrough"`
