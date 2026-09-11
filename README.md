# AI Chemistry Video Request Service

An AI-native, production-grade FastAPI backend service that asynchronously accepts chemistry concept queries from learners, orchestrates video generation jobs through a quality-gated pipeline, persists job state, and produces high-quality, synchronized 1080p educational videos.

Built as part of the **Growtrics AI Chemistry Video Request Service Challenge**.

---

## 🌟 Key Capabilities

1. **Async Video Generation Flow**:
   - Immediate `202 Accepted` response with unique job ID.
   - Observable lifecycle state machine:
     `PENDING` $\to$ `VALIDATING` $\to$ `GENERATING_SCRIPT` $\to$ `SYNTHESIZING_AUDIO` $\to$ `RENDERING_VIDEO` $\to$ `VERIFYING_ARTIFACT` $\to$ `COMPLETED` (or `FAILED` with diagnostics).
2. **Reliability Under Non-Determinism**:
   - Treats non-determinism as an engineering challenge.
   - Strict Pydantic schema validation (`VideoScript`, `Scene`).
   - Automatic retry with temperature tightening on schema failure.
   - Seamless fallback to curated pedagogical script templates guaranteeing 100% reliable generation across repeated runs.
3. **High-Fidelity Chemistry Visual Compositor**:
   - Generates crisp 1080p ($1920 \times 1080$) scientific visual cards tailored for target concepts:
     - **pH Scale**: 14-stop gradient scale, $[H^+]$ vs $[OH^-]$ markers, common chemical indicators (battery acid, lemon, water, bleach).
     - **Covalent Bonds**: Dual-atom orbital overlaps, Bohr valence shells, glowing shared electron pairs.
     - **Ionic vs Covalent**: Side-by-side comparison of $Na \to Cl$ electron transfer & crystal lattice vs $H_2O$ molecular bonding.
4. **Synchronized Audio Narration**:
   - Natural voiceover synthesized via `edge-tts` (with macOS `say` and FFmpeg synthetic fallbacks).
   - Dynamically calculates exact scene durations via `ffprobe` to eliminate desync or truncated audio.
5. **Clean Architecture & Cost-Conscious Boundaries**:
   - Decoupled REST routes (`app/api/`), business orchestration (`app/services/`), persistence (`app/repositories/`), and generation pipeline (`app/pipeline/`).
   - In-database state persistence using async SQLite (`aiosqlite`).
   - Default generation cost is **$0.00/video** locally (or **~$0.002 - $0.05** with external LLM/TTS).

---

## 📁 Repository Structure

```
├── app/
│   ├── api/                  # FastAPI routers and endpoints
│   │   └── v1/
│   │       └── endpoints/    # /jobs, /health, /metrics
│   ├── core/                 # App configuration & settings
│   ├── models/               # Pydantic domain models (Job, Scene, VideoScript)
│   ├── pipeline/             # Video generation pipeline
│   │   ├── classifier.py     # Natural language chemistry query classifier
│   │   ├── script_generator.py # Guardrailed script generator with retry/fallback
│   │   ├── templates.py      # Curated pedagogical script storyboards
│   │   ├── audio_synthesizer.py # Voiceover synthesis & ffprobe duration alignment
│   │   ├── visual_compositor.py # 1080p Pillow chemistry visual graphics renderer
│   │   ├── video_assembler.py   # FFmpeg MP4 compiler & artifact verifier
│   │   └── pipeline.py       # End-to-end pipeline orchestrator
│   ├── repositories/         # Abstract JobRepository & SQLite implementation
│   ├── services/             # VideoService & AsyncIO background worker queue
│   └── main.py               # FastAPI application entrypoint & lifespan
├── artifacts/
│   └── videos/               # Committed sample MP4s and metadata manifests
├── docs/
│   ├── ARCHITECTURE.md       # Detailed architecture note & boundary specifications
│   ├── DEMO_WALKTHROUGH.md   # Step-by-step curl API walkthrough guide
│   └── plans/                # Design doc, implementation plan, and live task tracker
├── scripts/
│   └── generate_sample_videos.py # Runner for generating sample videos
├── tests/
│   ├── unit/                 # Unit tests (classifier, scripts, audio, visuals, repo)
│   └── integration/          # Integration tests (FastAPI endpoints, E2E generation)
└── pyproject.toml            # Project dependencies and tool configuration
```

---

## 🚀 Setup & Installation

### Prerequisites
- Python 3.12+ (or Python 3.12 managed by `uv`)
- `ffmpeg` and `ffprobe` (installed via `brew install ffmpeg` on macOS or `apt install ffmpeg` on Linux)
- `uv` (recommended: `curl -LsSf https://astral.sh/uv/install.sh | sh`)

### 1. Clone & Setup Virtual Environment
```bash
# Clone the repository
git clone <repo-url>
cd talotrace-coding-challenge

# Create Python 3.12 virtual environment using uv
uv venv --python 3.12 .venv
source .venv/bin/activate

# Install dependencies in editable mode with development packages
uv pip install -e ".[dev]"
```

---

## 🏃 Running the Server

Start the FastAPI application with Uvicorn:

```bash
# Using uv run
uv run --python .venv uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Or with activated venv
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The interactive OpenAPI Swagger documentation is available at:
👉 **`http://localhost:8000/docs`**

---

## 📡 API Reference & Examples

### 1. Request Video Generation
**Endpoint:** `POST /api/v1/videos/jobs`

```bash
curl -X POST http://localhost:8000/api/v1/videos/jobs \
  -H "Content-Type: application/json" \
  -d '{"query": "How does the pH scale work?"}'
```

**Response (`202 Accepted`):**
```json
{
  "id": "job_a1b2c3d4e5f6",
  "query": "How does the pH scale work?",
  "topic": "PH_SCALE",
  "status": "PENDING",
  "progress_pct": 0,
  "current_step": "Job accepted and enqueued",
  "error_detail": null,
  "video_url": null,
  "video_duration_seconds": null,
  "metadata": {},
  "created_at": "2026-09-12T03:00:00Z",
  "updated_at": "2026-09-12T03:00:00Z",
  "completed_at": null
}
```

---

### 2. Poll Job Status
**Endpoint:** `GET /api/v1/videos/jobs/{job_id}`

```bash
curl http://localhost:8000/api/v1/videos/jobs/job_a1b2c3d4e5f6
```

**Response when Completed (`200 OK`):**
```json
{
  "id": "job_a1b2c3d4e5f6",
  "query": "How does the pH scale work?",
  "topic": "PH_SCALE",
  "status": "COMPLETED",
  "progress_pct": 100,
  "current_step": "Completed",
  "error_detail": null,
  "video_url": "/api/v1/videos/jobs/job_a1b2c3d4e5f6/video",
  "video_duration_seconds": 34.35,
  "metadata": {
    "topic": "PH_SCALE",
    "title": "How the pH Scale Works: Acids, Bases, and Ions",
    "scenes_count": 3,
    "fallback_used": false,
    "estimated_cost_usd": 0.0
  },
  "created_at": "2026-09-12T03:00:00Z",
  "updated_at": "2026-09-12T03:00:35Z",
  "completed_at": "2026-09-12T03:00:35Z"
}
```

---

### 3. Retrieve / Stream Completed Video
**Endpoint:** `GET /api/v1/videos/jobs/{job_id}/video`

```bash
# Download the generated MP4 file
curl -O http://localhost:8000/api/v1/videos/jobs/job_a1b2c3d4e5f6/video
```

---

### 4. List All Jobs
**Endpoint:** `GET /api/v1/videos/jobs?limit=10&offset=0`

```bash
curl "http://localhost:8000/api/v1/videos/jobs?status=COMPLETED&limit=10"
```

---

### 5. Health & System Metrics
**Endpoints:** `GET /health` and `GET /api/v1/metrics`

```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/metrics
```

---

## 🧪 Testing & Code Quality

Run tests and linters using `uv`:

```bash
# Run complete test suite (Unit + Integration + E2E)
uv run --python .venv pytest -v

# Run lint checks with Ruff
uv run --python .venv ruff check .

# Run code format checks with Ruff
uv run --python .venv ruff format --check .
```

---

## 🎬 Required Chemistry Concepts & Committed Sample Videos

The repository includes pre-generated, verified 1080p MP4 videos for the 3 required queries in `artifacts/videos/`:

| Concept | Input Learner Query | Artifact File | Duration | Resolution |
| :--- | :--- | :--- | :--- | :--- |
| **pH Scale** | *"How does the pH scale work?"* | [`artifacts/videos/ph_scale.mp4`](artifacts/videos/ph_scale.mp4) | ~34.35s | 1080p (1920x1080) |
| **Covalent Bonds** | *"Why do atoms form covalent bonds?"* | [`artifacts/videos/covalent_bonds.mp4`](artifacts/videos/covalent_bonds.mp4) | ~35.87s | 1080p (1920x1080) |
| **Ionic vs Covalent** | *"What is the difference between ionic and covalent bonding?"* | [`artifacts/videos/ionic_vs_covalent.mp4`](artifacts/videos/ionic_vs_covalent.mp4) | ~46.38s | 1080p (1920x1080) |

To re-generate all sample videos from scratch:
```bash
uv run --python .venv python scripts/generate_sample_videos.py
```
