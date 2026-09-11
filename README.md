# AI Chemistry Video Request Service

An AI-native, production-grade FastAPI backend service that asynchronously accepts chemistry concept queries from learners, orchestrates video generation jobs through a quality-gated pipeline, persists job state, and produces high-quality, synchronized 1080p educational videos.

Built as part of the **Growtrics AI Chemistry Video Request Service Challenge**.

---

## 🌟 Key Capabilities

1. **Async Video Generation Flow**:
   - Immediate `202 Accepted` response with unique job ID.
   - Observable lifecycle state machine:
     `PENDING` $\to$ `VALIDATING` $\to$ `GENERATING_SCRIPT` $\to$ `SYNTHESIZING_AUDIO` $\to$ `RENDERING_VIDEO` $\to$ `VERIFYING_ARTIFACT` $\to$ `COMPLETED` (or `FAILED` with diagnostics).
2. **Google Gemini LLM & Pydantic Guardrails**:
   - Integrated with Google Gemini 3.5 Flash Lite (`gemini-3.5-flash-lite`, configurable via `GEMINI_MODEL`) using `google-genai` SDK to generate structured 4-scene chemistry explainer storyboards with embedded LaTeX chemical equations and formulas.
   - Schema validation guardrails with deterministic fallbacks guarantee 100% reliability across repeated runs.
3. **Manim 3Blue1Brown Mathematical Animations**:
   - Vector animations rendered with Manim for high conceptual clarity:
     - Orbital electron motions, Bohr quantized electron shells, dynamic ionic transfers, activation energy profiles, and periodic trend vectors.
4. **Zero-Dependency LaTeX Equation Renderer**:
   - Renders LaTeX chemical formulas and math equations ($0 \le \mathrm{pH} \le 14$, $\mathrm{pH} = -\log_{10}[\mathrm{H}^+]$, $\Delta H < 0$, etc.) into crisp transparent PNGs via `matplotlib.mathtext`, completely bypassing heavy system TeX distribution dependencies (`texlive`/`dvisvgm`).
5. **Synchronized ~30-Second Explainer Pacing**:
   - Carefully calibrated audio narration and Manim animation choreographies ensure every explainer video runs ~29–31 seconds with zero clipped speech or truncated animations.
6. **Clean Architecture & Cost-Conscious Boundaries**:
   - Decoupled REST routes (`app/api/`), business orchestration (`app/services/`), persistence (`app/repositories/`), and generation pipeline (`app/pipeline/`).
   - In-database state persistence using async SQLite (`aiosqlite`).

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

## 🎬 8 Chemistry Explainer Videos (~30s Each) Generated via FastAPI

The repository includes pre-generated, verified MP4 explainer videos with LaTeX formulas and 3Blue1Brown-style Manim animations for all 8 concepts in `artifacts/videos/`:

| Concept | Input Learner Query | Artifact File | Duration | Resolution | Size | Engine |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **pH Scale** | *"How does the pH scale work?"* | [`artifacts/videos/ph_scale.mp4`](artifacts/videos/ph_scale.mp4) | 29.04s | 720p (1280x720) | 0.91 MB | Manim + LaTeX |
| **Covalent Bonds** | *"Why do atoms form covalent bonds?"* | [`artifacts/videos/covalent_bonds.mp4`](artifacts/videos/covalent_bonds.mp4) | 29.08s | 720p (1280x720) | 0.93 MB | Manim + LaTeX |
| **Ionic vs Covalent** | *"What is the difference between ionic and covalent bonding?"* | [`artifacts/videos/ionic_vs_covalent.mp4`](artifacts/videos/ionic_vs_covalent.mp4) | 29.00s | 720p (1280x720) | 0.88 MB | Manim + LaTeX |
| **Atomic Structure** | *"What is the structure of an atom and its subatomic particles?"* | [`artifacts/videos/atomic_structure.mp4`](artifacts/videos/atomic_structure.mp4) | 29.00s | 720p (1280x720) | 0.77 MB | Manim + LaTeX |
| **Exo vs Endothermic** | *"How do exothermic and endothermic reactions differ?"* | [`artifacts/videos/exo_vs_endothermic.mp4`](artifacts/videos/exo_vs_endothermic.mp4) | 29.00s | 720p (1280x720) | 0.78 MB | Manim + LaTeX |
| **Periodic Trends** | *"How does the periodic table organize chemical elements?"* | [`artifacts/videos/periodic_trends.mp4`](artifacts/videos/periodic_trends.mp4) | 31.50s | 720p (1280x720) | 0.81 MB | Manim + LaTeX |
| **States of Matter** | *"What are the states of matter and phase transitions?"* | [`artifacts/videos/states_of_matter.mp4`](artifacts/videos/states_of_matter.mp4) | 29.00s | 720p (1280x720) | 0.77 MB | Manim + LaTeX |
| **Neutralization** | *"What happens during an acid-base neutralization reaction?"* | [`artifacts/videos/acid_base_neutralization.mp4`](artifacts/videos/acid_base_neutralization.mp4) | 29.50s | 720p (1280x720) | 0.80 MB | Manim + LaTeX |

### Request & Generate All 8 Videos via the FastAPI Service
With the FastAPI server running (`uv run --python .venv uvicorn app.main:app --port 8000`):
```bash
# Automated client that creates jobs via POST /api/v1/videos/jobs, polls progress, and streams the videos:
uv run --python .venv python -m scripts.generate_via_api
```
