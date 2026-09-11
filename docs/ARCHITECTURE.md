# AI Chemistry Video Request Service — Architecture & Technical Note

## 1. Architectural Overview

The service is structured following **Hexagonal / Layered Architecture** principles, prioritizing strict isolation of concerns, explicit state management, and resilience against generative non-determinism.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           FastAPI REST API Layer                        │
│             /api/v1/videos/jobs  |  /health  |  /api/v1/metrics         │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      VideoRequestService Orchestrator                   │
│          Business logic, query dispatching, and metric gathering        │
└──────────────┬─────────────────────┬─────────────────────┬──────────────┘
               │                     │                     │
               ▼                     ▼                     ▼
┌─────────────────────────┐ ┌─────────────────┐ ┌─────────────────────────┐
│  Async SQLite Database  │ │ AsyncIO Worker  │ │ File Artifact Storage   │
│   (Repository Pattern)  │ │      Queue      │ │   (MP4, Audio, Frames)  │
└─────────────────────────┘ └────────┬────────┘ └─────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     Video Generation Pipeline Boundary                  │
│                                                                         │
│  1. ConceptClassifier  ──► 2. ScriptGenerator (Pydantic Schema & Guard)  │
│                                           │                             │
│  4. Video Composition  ◄── 3. AudioEngine │ (Fallback on failure)       │
│     - Manim Engine (Option B)             ▼                             │
│     - 1080p Canvas Engine      Curated Pedagogical Template             │
│                                                                         │
│  5. FFmpeg Assembly & Artifact Verification (Stream sanity gate)        │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Job Lifecycle & State Machine

Every video generation request is tracked via an asynchronous state machine with explicit percentage progress:

```
[ PENDING (0%) ]
       │
       ▼
[ VALIDATING (10%) ] ──► (Query malformed/unsupported) ──► [ FAILED ]
       │
       ▼
[ GENERATING_SCRIPT (25%) ] ──► (LLM schema retry fails) ──► [ Fallback Template ]
       │
       ▼
[ SYNTHESIZING_AUDIO (45%) ]
       │
       ▼
[ RENDERING_VIDEO (75%) ]
       │
       ▼
[ VERIFYING_ARTIFACT (95%) ] ──► (Zero-byte/corrupt container) ──► [ FAILED ]
       │
       ▼
[ COMPLETED (100%) ]
```

### State Transitions:
1. `PENDING` (0%): Job persisted in SQLite database and enqueued into the worker queue. API returns `202 Accepted`.
2. `VALIDATING` (10%): Query classified into canonical topics (`PH_SCALE`, `COVALENT_BONDS`, `IONIC_VS_COVALENT`, `OTHER_STEM`).
3. `GENERATING_SCRIPT` (25%): Storyboard scenes generated and validated against `VideoScript` Pydantic schema.
4. `SYNTHESIZING_AUDIO` (45%): Narration audio generated via `edge-tts` (or local speech fallback). Actual duration per scene measured via `ffprobe`.
5. `RENDERING_VIDEO` (75%): Animation and visual graphics compiled.
6. `VERIFYING_ARTIFACT` (95%): Artifact sanity checks verified via `ffprobe`.
7. `COMPLETED` (100%): Output MP4 ready for streaming/download via `/video` endpoint.

---

## 3. Persistence & Artifact Boundary

- **Persistence Layer (`app/repositories/`)**:
  - `JobRepository` defines an abstract interface.
  - `SQLiteJobRepository` implements async SQLite operations using `aiosqlite`.
  - Database schema includes indexes on `status` and `created_at DESC` for fast polling and listing.
  - Decoupled from ORM bloat; uses clean parameterized queries preventing SQL injection.
- **Artifact Boundary (`app/storage/` & `settings`)**:
  - Video artifacts are saved to `artifacts/videos/<job_id>.mp4`.
  - Audio and scene frame assets are organized in isolated job directories (`artifacts/audio/<job_id>/`, `artifacts/frames/<job_id>/`).
  - The API streams videos using `FileResponse` with native HTTP byte-range support (`206 Partial Content`), allowing learners to seek through the video in any web browser or mobile client.

---

## 4. Engineering Around Non-Determinism

Generative LLMs and video models are inherently stochastic and prone to hallucinating scientific formulas, mangling text, or timing out. We treat non-determinism as an engineering problem through a multi-tier defense:

1. **Strict Pydantic Schema Validation**:
   - Every script must validate against `VideoScript` (title, overview, $\ge 2$ scenes with non-empty narration, visual type, and key takeaway).
2. **Auto-Retry Gate**:
   - If an external LLM fails schema parsing or omits required scenes, the system attempts 1 retry with stricter formatting instructions.
3. **Deterministic Fallback Templates**:
   - If an external model is unavailable, rate-limited, or fails validation on retry, the pipeline immediately falls back to a curated pedagogical script template.
   - The job succeeds reliably with 100% verified chemistry content, logging `metadata["fallback_used"] = True`.
4. **Artifact Sanity Gate**:
   - Before transitioning to `COMPLETED`, `VideoAssembler.verify_video_artifact` probes the generated MP4 with `ffprobe` to verify non-zero size, valid video/audio streams, and valid duration. If corrupt, it fails safely with structured diagnostics rather than returning broken media.

---

## 5. Cost Analysis

| Component | Pure Cloud Generative API | Our Hybrid Architecture |
| :--- | :--- | :--- |
| **Script Generation** | GPT-4o / Claude ($0.002 - $0.005) | Pluggable LLM with Local Fallback ($0.00 - $0.002) |
| **Voiceover Narration** | ElevenLabs ($0.03 / min) | Edge-TTS / Local Speech ($0.00) |
| **Visual Rendering** | Runway / Luma ($0.50 - $1.50 / clip) | Manim / Procedural Compositor ($0.00) |
| **Total per Video** | **~$0.55 – $1.60** | **~$0.000 – $0.002** |

---

## 6. Extensibility to Other STEM Topics

To support new science topics (e.g., Photosynthesis, Newton's Laws):
1. Add the topic enum to `SupportedTopic` in `app/models/script.py`.
2. Register matching regex keywords in `ConceptClassifier.rules` in `app/pipeline/classifier.py`.
3. Add a fallback script storyboard to `TEMPLATES` in `app/pipeline/templates.py`.
4. Add a visual rendering scene in `VisualCompositor` or `ManimRenderer`.
No changes to the API, database schema, or worker queue are needed.
