# AI Chemistry Video Request Service — Demo & API Walkthrough

This guide demonstrates an end-to-end API walkthrough showcasing the **8 chemistry concepts** generated as ~30-second explainer videos with LaTeX formulas and 3Blue1Brown-style Manim animations:

### Original Concepts:
1. *"How does the pH scale work?"* (`PH_SCALE`)
2. *"Why do atoms form covalent bonds?"* (`COVALENT_BONDS`)
3. *"What is the difference between ionic and covalent bonding?"* (`IONIC_VS_COVALENT`)

### 5 New Video Requirements:
4. *"What is the structure of an atom and its subatomic particles?"* (`ATOMIC_STRUCTURE`)
5. *"How do exothermic and endothermic reactions differ?"* (`EXO_VS_ENDOTHERMIC`)
6. *"How does the periodic table organize chemical elements?"* (`PERIODIC_TRENDS`)
7. *"What are the states of matter and phase transitions?"* (`STATES_OF_MATTER`)
8. *"What happens during an acid-base neutralization reaction?"* (`ACID_BASE_NEUTRALIZATION`)

---

## 1. Automated 8-Video Request Runner

The easiest way to request, poll, and download all 8 videos via the live FastAPI service is using the automated runner script:

```bash
# Start the FastAPI service
uv run --python .venv uvicorn app.main:app --host 127.0.0.1 --port 8000

# In a second terminal, execute the client automation runner:
uv run --python .venv python -m scripts.generate_via_api
```

This runner:
1. Performs a `/health` check against the service.
2. Sends `POST /api/v1/videos/jobs` for each of the 8 concepts.
3. Polls `GET /api/v1/videos/jobs/{id}` at 1.5-second intervals until reaching `COMPLETED`.
4. Streams `GET /api/v1/videos/jobs/{id}/video` directly into `artifacts/videos/<concept>.mp4`.
5. Saves the metadata manifest into `artifacts/videos/<concept>.json`.

---

## 2. Manual Step-by-Step API Walkthrough via `curl`

### Step 2.1: Check Health
```bash
curl -s http://localhost:8000/health | jq .
```
Response:
```json
{
  "status": "healthy",
  "service": "AI Chemistry Video Request Service",
  "version": "0.1.0",
  "database_connected": true,
  "worker_running": true,
  "ffmpeg_installed": true,
  "ffprobe_installed": true
}
```

### Step 2.2: Submit a Video Generation Job
```bash
curl -X POST http://localhost:8000/api/v1/videos/jobs \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the structure of an atom and its subatomic particles?"}' | jq .
```
Response (`202 Accepted`):
```json
{
  "id": "job_a3bbfce68de4",
  "query": "What is the structure of an atom and its subatomic particles?",
  "topic": "ATOMIC_STRUCTURE",
  "status": "PENDING",
  "progress_pct": 0,
  "current_step": "Job accepted and enqueued"
}
```

### Step 2.3: Poll Job Progress
```bash
curl -s http://localhost:8000/api/v1/videos/jobs/job_a3bbfce68de4 | jq .
```
Observable pipeline steps:
- `10%` (`VALIDATING`): Classifying query and checking guardrails
- `25%` (`GENERATING_SCRIPT`): Generating educational script with Gemini LLM / fallback
- `45%` (`SYNTHESIZING_AUDIO`): Synthesizing voice narration and scene durations
- `65%` (`RENDERING_VIDEO`): Rendering 3Blue1Brown-style vector animations with Manim
- `100%` (`COMPLETED`): Video rendered and verified!

### Step 2.4: Stream & Download the Video
```bash
curl -O http://localhost:8000/api/v1/videos/jobs/job_a3bbfce68de4/video
```

---

## 3. View Aggregated Metrics
```bash
curl -s http://localhost:8000/api/v1/metrics | jq .
```
```json
{
  "total_jobs": 8,
  "completed_jobs": 8,
  "failed_jobs": 0,
  "active_jobs": 0,
  "average_video_duration_seconds": 29.45,
  "queue_size": 0,
  "worker_running": true
}
```
