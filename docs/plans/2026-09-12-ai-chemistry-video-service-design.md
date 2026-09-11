# AI Chemistry Video Request Service — System Architecture & Design

**Date:** 2026-09-12  
**Status:** Approved  
**Author:** Antigravity Pairing Assistant & Engineering Team  
**Scope:** Backend prototype for educational chemistry video request service  

---

## 1. Executive Summary & Context

Growtrics is building AI-native learning experiences. This backend service allows learners to submit chemistry concept queries (specifically targeting three required topics: pH scale, covalent bonding, and ionic vs. covalent bonding), asynchronously processes these requests through a resilient video generation pipeline, tracks job state with high observability, and produces high-quality, synchronized `.mp4` educational videos.

The system is designed with a hybrid, cost-conscious architecture:
- **Resilience under non-determinism**: Structured Pydantic validation, schema retries, and high-fidelity deterministic fallback templates guarantee 100% reliable output across repeated runs.
- **Production Boundary**: Clear separation between API, business orchestration, async job queue, database persistence (SQLite via Repository pattern), artifact storage, and the video generation pipeline.
- **Cost Efficiency**: Zero-cost default local execution (~$0.00/video) with pluggable hooks for live cloud LLM / TTS providers (~$0.002 - $0.05/video).

---

## 2. System Architecture & Boundaries

The project adopts Hexagonal / Layered Architecture principles:

```
                  ┌────────────────────────────────────────┐
                  │          FastAPI HTTP Client           │
                  │   POST /jobs | GET /jobs | GET /video  │
                  └──────────────────┬─────────────────────┘
                                     │
                                     ▼
                  ┌────────────────────────────────────────┐
                  │       VideoRequestService Layer        │
                  │   Job orchestration & query routing    │
                  └───────────┬────────────────┬───────────┘
                              │                │
            ┌─────────────────┴─┐            ┌─┴─────────────────┐
            │                   │            │                   │
            ▼                   ▼            ▼                   ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────┐ ┌──────────────────┐
│  Job Repository  │ │ Background Queue │ │   Artifact   │ │ Video Generation │
│ (SQLite / Async) │ │ (AsyncIO Worker) │ │ Store (Disk) │ │     Pipeline     │
└──────────────────┘ └──────────────────┘ └──────────────┘ └─────────┬────────┘
                                                                      │
                                                ┌─────────────────────┴─────────────────────┐
                                                │                                           │
                                                ▼                                           ▼
                                    ┌───────────────────────┐                   ┌───────────────────────┐
                                    │ LLM & Script Provider │                   │ Media & Audio Engine  │
                                    │ - Live LLM (OpenAI)   │                   │ - Edge-TTS / Local    │
                                    │ - Curated Fallbacks   │                   │ - Chemistry Visuals   │
                                    │ - Guardrail Validator │                   │ - FFmpeg Compositor   │
                                    └───────────────────────┘                   └───────────────────────┘
```

### Component Boundaries:
1. **API Layer (`app/api/v1/`)**:
   - Handles REST requests, validates query models, returns proper HTTP status codes (`202 Accepted`, `200 OK`, `404 Not Found`), and streams video files with byte-range support.
2. **Service Layer (`app/services/video_service.py`)**:
   - Coordinates business rules: job creation, dispatching async tasks to the worker queue, querying job progress, and gathering execution metrics.
3. **Repository Layer (`app/repositories/job_repository.py`)**:
   - Abstract `JobRepository` interface backed by an asynchronous SQLite database using `aiosqlite`. Encapsulates SQL queries and schema migrations.
4. **Artifact Storage (`app/storage/artifact_store.py`)**:
   - Manages physical filesystem paths for generated assets (`artifacts/videos/`, `artifacts/audio/`, `artifacts/frames/`). Validates file integrity (size > 0, valid MP4 headers).
5. **Generation Pipeline (`app/pipeline/`)**:
   - Decoupled into isolated sub-components:
     - `ConceptClassifier`: Maps raw learner queries to canonical chemistry topics (`PH_SCALE`, `COVALENT_BONDS`, `IONIC_VS_COVALENT`).
     - `ScriptGenerator`: Produces multi-scene pedagogical scripts conforming to `VideoScript` Pydantic models.
     - `AudioSynthesizer`: Generates clear voice narration (`edge-tts` or local TTS fallback) and extracts exact scene durations via `ffprobe`.
     - `VisualCompositor`: Programmatically generates clean, high-resolution chemistry diagrams and visual title cards for each scene.
     - `VideoAssembler`: Uses `ffmpeg` to assemble visual cards, lower-thirds subtitles, and audio tracks into a web-optimized 1080p MP4.

---

## 3. Job Lifecycle & State Machine

Each video generation job progresses through discrete states:

```
[ PENDING ]
    │
    ▼
[ VALIDATING ]  ──► (Invalid query or unsupported) ──► [ FAILED ]
    │
    ▼
[ GENERATING_SCRIPT ] ──► (LLM retry exhausted) ──► [ Fallback to Template ]
    │
    ▼
[ SYNTHESIZING_AUDIO ]
    │
    ▼
[ RENDERING_VIDEO ]
    │
    ▼
[ VERIFYING_ARTIFACT ] ──► (Corrupt file or zero bytes) ──► [ FAILED ]
    │
    ▼
[ COMPLETED ]
```

### Job State Model:
- **`id`**: String UUID (`job_<uuid4>`)
- **`query`**: Original learner prompt
- **`topic`**: Canonical concept enum (`PH_SCALE`, `COVALENT_BONDS`, `IONIC_VS_COVALENT`, `OTHER_STEM`)
- **`status`**: `JobStatus` enum:
  - `PENDING` (0%): Job accepted and enqueued
  - `VALIDATING` (10%): Query classified and checked against guardrails
  - `GENERATING_SCRIPT` (25%): Storyboard scenes generated and validated
  - `SYNTHESIZING_AUDIO` (50%): Narration audio generated and timed
  - `RENDERING_VIDEO` (75%): Visual scenes composited and rendered via FFmpeg
  - `VERIFYING_ARTIFACT` (90%): Artifact existence, duration, and container sanity verified
  - `COMPLETED` (100%): Video ready for download/streaming
  - `FAILED`: Failure recorded with detailed reason
- **`progress_pct`**: Integer between `0` and `100`
- **`current_step`**: Human-readable step description
- **`error_detail`**: Nullable string with failure trace or reason
- **`video_path`**: Relative or absolute path to the `.mp4` artifact
- **`video_duration_seconds`**: Float total duration
- **`metadata`**: JSON dictionary containing script scenes, audio voice used, generation cost estimate, and retry telemetry.
- **`created_at` / `updated_at` / `completed_at`**: ISO timestamps

---

## 4. Video Generation Pipeline & Handling Non-Determinism

### 4.1 Non-Determinism as an Engineering Problem
Generative AI outputs vary across runs. To guarantee reliability:
1. **Pydantic Schema Validation**: Every generated script must parse into:
   ```python
   class Scene(BaseModel):
       scene_id: int
       title: str
       narration: str
       visual_type: str  # e.g. "ph_spectrum", "electron_sharing", "lattice_comparison"
       key_takeaway: str


   class VideoScript(BaseModel):
       topic: str
       title: str
       scenes: List[Scene]
   ```
2. **Quality Gates & Auto-Retry**:
   - If an external LLM outputs invalid JSON, missing scenes, or fewer than 3 scenes, the pipeline retries once with a stricter temperature and system prompt.
3. **Deterministic Fallback Engine**:
   - If the LLM is unreachable, exceeds quota, or fails validation on retry, the pipeline immediately falls back to a curated pedagogical script template for the detected concept.
   - The job succeeds with consistent, verified content, and the fallback event is recorded in the job's `metadata["fallback_used"] = True`.
4. **Artifact Sanity Gate**:
   - Before a job transitions to `COMPLETED`, `ffprobe` validates that the video container has valid audio and video streams, non-zero frame count, and non-zero duration.

### 4.2 Chemistry Visual Compositor
Generates custom, crisp vector/Pillow visual scenes:
1. **"How does the pH scale work?"**:
   - Color gradient scale from $0$ (Red/Acidic) to $7$ (Green/Neutral) to $14$ (Purple/Alkaline).
   - Dynamic indicators for $[H^+]$ concentration and common reference substances (Stomach acid pH 1, Lemon juice pH 2, Pure water pH 7, Bleach pH 12).
2. **"Why do atoms form covalent bonds?"**:
   - Visual orbital representation of two Hydrogen atoms ($\text{H}$) with $1$ valence electron each.
   - Animated visual transition showing electron sharing in overlapping valence shells forming a stable $\text{H}_2$ duet.
3. **"What is the difference between ionic and covalent bonding?"**:
   - Side-by-side comparison diagram:
     - Left: Ionic bonding ($\text{Na} \to \text{Cl}$ complete electron transfer creating $\text{Na}^+$ and $\text{Cl}^-$ ions bound by electrostatic attraction in a crystal lattice).
     - Right: Covalent bonding ($\text{H}_2\text{O}$ mutual sharing of valence electron pairs).

---

## 5. API Specification

- `POST /api/v1/videos/jobs`:
  - Request: `{"query": "How does the pH scale work?"}`
  - Response (`202 Accepted`):
    ```json
    {
      "job_id": "job_a1b2c3d4",
      "status": "PENDING",
      "query": "How does the pH scale work?",
      "topic": "PH_SCALE",
      "created_at": "2026-09-12T02:50:00Z",
      "estimated_duration_seconds": 15
    }
    ```
- `GET /api/v1/videos/jobs`:
  - Query parameters: `status`, `limit` (default 50), `offset` (default 0).
  - Response: List of jobs with pagination metadata.
- `GET /api/v1/videos/jobs/{job_id}`:
  - Response: Detailed job status, progress percentage, current step, script metadata, and artifact URL.
- `GET /api/v1/videos/jobs/{job_id}/video`:
  - Streams or downloads the `.mp4` video with `Content-Type: video/mp4` and HTTP Range support.
- `GET /health`:
  - Returns service status, worker health, database connectivity, and FFmpeg version.

---

## 6. Cost Analysis

| Component | Cloud Generative Approach | Our Hybrid Approach |
| :--- | :--- | :--- |
| **Scripting** | GPT-4o / Claude ($0.002 - $0.005) | Pluggable LLM with Local Fallback ($0.00 - $0.002) |
| **Voice Narration** | ElevenLabs ($0.03 / min) | Edge-TTS / Local Speech ($0.00) |
| **Visual Rendering** | Runway / Luma ($0.50 - $1.50 / clip) | Procedural Canvas Compositor ($0.00) |
| **Total per Video** | **~$0.55 – $1.60** | **~$0.000 – $0.002** |

---

## 7. Extensibility to other STEM Topics

The system uses a pluggable `ConceptRegistry`:
```python
class ConceptDefinition:
    key: str
    subject: str  # e.g. "chemistry", "physics", "biology"
    canonical_name: str
    keywords: List[str]
    template_script: VideoScript
    visual_renderer: Callable[[Scene, Path], Path]
```
Adding new topics (e.g. *"Photosynthesis"*, *"Newton's Third Law"*) simply requires registering a new `ConceptDefinition` without altering the core pipeline, worker, or API layers.

---

## 8. Testing & Verification Strategy

1. **Unit Tests**:
   - `test_concept_classifier.py`: Query classification for exact and fuzzy matching.
   - `test_script_guardrails.py`: Schema validation, malformed input rejection, fallback trigger on failure.
   - `test_audio_engine.py`: Audio generation and duration measurement.
   - `test_visual_compositor.py`: Image generation for the 3 required chemistry concepts.
2. **Integration Tests**:
   - `test_job_repository.py`: Async SQLite CRUD operations and state transitions.
   - `test_api_endpoints.py`: FastAPI TestClient tests for `POST /jobs`, `GET /jobs`, `GET /jobs/{id}`, `GET /jobs/{id}/video`.
   - `test_end_to_end_generation.py`: Full end-to-end execution producing real MP4 files for all 3 required queries.
3. **Artifact Verification**:
   - Automate FFprobe validation verifying video stream codec (`h264`), audio stream codec (`aac`), resolution ($1920 \times 1080$), and non-zero duration.
