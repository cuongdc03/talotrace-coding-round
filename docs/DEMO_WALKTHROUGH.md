# AI Chemistry Video Request Service — Demo & API Walkthrough

This guide demonstrates an end-to-end API walkthrough showcasing the **three required chemistry concepts**:
1. *"How does the pH scale work?"*
2. *"Why do atoms form covalent bonds?"*
3. *"What is the difference between ionic and covalent bonding?"*

---

## 1. Start the Server

```bash
uv run --python .venv uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Verify service health:
```bash
curl -s http://localhost:8000/health | jq .
```
Expected output:
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

---

## 2. Concept 1: "How does the pH scale work?"

### Step 2.1: Submit Video Request
```bash
curl -X POST http://localhost:8000/api/v1/videos/jobs \
  -H "Content-Type: application/json" \
  -d '{"query": "How does the pH scale work?"}' | jq .
```

Response (`202 Accepted`):
```json
{
  "id": "job_ph_scale_01",
  "query": "How does the pH scale work?",
  "topic": "PH_SCALE",
  "status": "PENDING",
  "progress_pct": 0,
  "current_step": "Job accepted and enqueued"
}
```

### Step 2.2: Poll Status
```bash
curl -s http://localhost:8000/api/v1/videos/jobs/job_ph_scale_01 | jq .
```
Progress advances in real time:
- `10%` (`VALIDATING`): Classifying query and checking guardrails
- `25%` (`GENERATING_SCRIPT`): Generating educational script
- `45%` (`SYNTHESIZING_AUDIO`): Synthesizing voiceover
- `75%` (`RENDERING_VIDEO`): Rendering animations & visual cards
- `95%` (`VERIFYING_ARTIFACT`): Probing stream integrity
- `100%` (`COMPLETED`): Artifact ready!

### Step 2.3: Download / Stream Video
```bash
curl -O http://localhost:8000/api/v1/videos/jobs/job_ph_scale_01/video
```

---

## 3. Concept 2: "Why do atoms form covalent bonds?"

### Submit Request
```bash
curl -X POST http://localhost:8000/api/v1/videos/jobs \
  -H "Content-Type: application/json" \
  -d '{"query": "Why do atoms form covalent bonds?"}' | jq .
```

### Check Status
```bash
curl -s http://localhost:8000/api/v1/videos/jobs/<job_id> | jq .
```

---

## 4. Concept 3: "What is the difference between ionic and covalent bonding?"

### Submit Request
```bash
curl -X POST http://localhost:8000/api/v1/videos/jobs \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the difference between ionic and covalent bonding?"}' | jq .
```

---

## 5. View Aggregated Metrics
```bash
curl -s http://localhost:8000/api/v1/metrics | jq .
```
```json
{
  "total_jobs": 3,
  "completed_jobs": 3,
  "failed_jobs": 0,
  "active_jobs": 0,
  "average_video_duration_seconds": 38.86,
  "queue_size": 0,
  "worker_running": true
}
```
