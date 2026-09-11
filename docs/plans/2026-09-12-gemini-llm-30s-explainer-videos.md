# Gemini LLM Integration, 30s Explainer Pacing, and 5 New Video Requirements Implementation Plan

> **For Antigravity:** REQUIRED WORKFLOW: Use `.agent/workflows/execute-plan.md` to execute this plan in single-flow mode.

**Goal:** Upgrade the video generation pipeline to use Gemini 2.5 Flash for generating ~30-second pedagogical explainer scripts with LaTeX chemistry equations, support 5 new core chemistry topics (8 total), render beautiful vector animations with embedded LaTeX formulas via Manim, and execute the generation through the FastAPI REST service.

**Architecture:** 
1. `app/pipeline/latex_renderer.py` compiles mathematical and chemical LaTeX notations into transparent PNGs using `matplotlib.mathtext` with zero TeX/dvisvgm dependency.
2. `app/pipeline/gemini_generator.py` invokes `google-genai` (`gemini-2.5-flash`) with structured JSON schema output to produce 4–5 scene explainer scripts (~75–90 words narration, target ~30s duration) with embedded LaTeX formulas, falling back to deterministic templates if offline.
3. `app/pipeline/classifier.py` and `app/pipeline/templates.py` expand to 8 concepts (3 original + 5 new: Atomic Structure, Exothermic/Endothermic, Periodic Trends, States of Matter, Acid-Base Neutralization).
4. `app/pipeline/manim_renderer.py` renders 3Blue1Brown vector animations incorporating LaTeX formula callouts for all 8 topics.
5. `scripts/generate_via_api.py` boots the FastAPI service, posts all jobs to `POST /api/v1/videos/jobs`, polls progress asynchronously, and downloads/verifies the final 30s MP4 artifacts.

**Tech Stack:** Python 3.12, FastAPI, `google-genai`, `matplotlib` (mathtext), `manim`, `edge-tts`, `ffmpeg`/`ffprobe`, `aiosqlite`, `pytest`, `ruff`.

---

### Task 1: Zero-Dependency LaTeX Equation Renderer Utility
- Files: `app/pipeline/latex_renderer.py`, `tests/unit/test_latex_renderer.py`

### Task 2: Gemini LLM Script Generator with Structured Output & Fallback
- Files: `app/models/script.py`, `app/pipeline/gemini_generator.py`, `app/pipeline/script_generator.py`, `tests/unit/test_gemini_generator.py`

### Task 3: Expand Classification & Explainer Templates for All 8 Concepts
- Files: `app/models/job.py`, `app/pipeline/classifier.py`, `app/pipeline/templates.py`, `tests/unit/test_classifier.py`, `tests/unit/test_script_generator.py`

### Task 4: Manim Explainer Animation Engine for All 8 Topics with LaTeX Callouts
- Files: `app/pipeline/manim_renderer.py`, `tests/unit/test_manim_renderer.py`

### Task 5: End-to-End FastAPI Client Automation & Video Generation
- Files: `scripts/generate_via_api.py`, `tests/integration/test_api.py`

### Task 6: Final Verification, Linter & Documentation
- Files: `README.md`, `docs/DEMO_WALKTHROUGH.md`, `docs/plans/task.md`
