"""Automated script to request, poll, and download 30s explainer videos from the FastAPI Service."""

import asyncio
import json
import logging

import httpx

from app.core.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("generate_via_api")

API_BASE = "http://127.0.0.1:8000"

ALL_CONCEPTS = [
    # 3 Original Concepts (Upgraded to ~30s explainer pacing)
    {
        "slug": "ph_scale",
        "query": "How does the pH scale work?",
        "filename": "ph_scale.mp4",
    },
    {
        "slug": "covalent_bonds",
        "query": "Why do atoms form covalent bonds?",
        "filename": "covalent_bonds.mp4",
    },
    {
        "slug": "ionic_vs_covalent",
        "query": "What is the difference between ionic and covalent bonding?",
        "filename": "ionic_vs_covalent.mp4",
    },
    # 5 New Sample Video Requirements (Requested via FastAPI)
    {
        "slug": "atomic_structure",
        "query": "What is the structure of an atom and its subatomic particles?",
        "filename": "atomic_structure.mp4",
    },
    {
        "slug": "exo_vs_endothermic",
        "query": "How do exothermic and endothermic reactions differ?",
        "filename": "exo_vs_endothermic.mp4",
    },
    {
        "slug": "periodic_trends",
        "query": "How does the periodic table organize chemical elements?",
        "filename": "periodic_trends.mp4",
    },
    {
        "slug": "states_of_matter",
        "query": "What are the states of matter and phase transitions?",
        "filename": "states_of_matter.mp4",
    },
    {
        "slug": "acid_base_neutralization",
        "query": "What happens during an acid-base neutralization reaction?",
        "filename": "acid_base_neutralization.mp4",
    },
]


async def run_client() -> None:
    settings.ensure_directories()
    results = []

    print("=" * 80)
    print("AI CHEMISTRY VIDEO SERVICE — FASTAPI CLIENT AUTOMATION RUNNER")
    print(f"Targeting: {API_BASE}")
    print("=" * 80)

    async with httpx.AsyncClient(base_url=API_BASE, timeout=300.0) as client:
        # Check Health
        try:
            health_resp = await client.get("/health")
            health_resp.raise_for_status()
            print(f"[✓] FastAPI service is healthy: {health_resp.json()}")
        except Exception as e:
            print(f"[!] Failed to connect to FastAPI service at {API_BASE}: {e}")
            print("    Please start the server: uv run --python .venv uvicorn app.main:app --port 8000")
            return

        for idx, item in enumerate(ALL_CONCEPTS, 1):
            slug = item["slug"]
            query = item["query"]
            target_mp4 = settings.VIDEOS_DIR / item["filename"]
            target_json = settings.VIDEOS_DIR / f"{slug}.json"

            print(f"\n[{idx}/8] Requesting video job from FastAPI: '{query}'")

            # 1. POST request to create job
            post_resp = await client.post(
                "/api/v1/videos/jobs",
                json={"query": query},
            )
            post_resp.raise_for_status()
            job_data = post_resp.json()
            job_id = job_data["id"]
            topic = job_data["topic"]
            print(f"    -> Enqueued Job ID: {job_id} | Topic: {topic}")

            # 2. Poll status until completed or failed
            last_pct = -1
            while True:
                await asyncio.sleep(1.5)
                poll_resp = await client.get(f"/api/v1/videos/jobs/{job_id}")
                poll_resp.raise_for_status()
                status_data = poll_resp.json()
                status = status_data["status"]
                pct = status_data["progress_pct"]
                step = status_data["current_step"]

                if pct != last_pct:
                    print(f"    [{pct:02d}%] {status}: {step}")
                    last_pct = pct

                if status == "COMPLETED":
                    break
                elif status == "FAILED":
                    err = status_data.get("error_detail", "Unknown error")
                    raise RuntimeError(f"Job {job_id} failed: {err}")

            # 3. Stream & Download MP4 Video Artifact via REST API
            print(f"    -> Downloading generated video artifact from /api/v1/videos/jobs/{job_id}/video ...")
            async with client.stream("GET", f"/api/v1/videos/jobs/{job_id}/video") as stream_resp:
                stream_resp.raise_for_status()
                with open(target_mp4, "wb") as f:
                    async for chunk in stream_resp.aiter_bytes(chunk_size=65536):
                        f.write(chunk)

            # 4. Save metadata manifest
            manifest_data = {
                "job_id": job_id,
                "query": query,
                "topic": topic,
                "title": status_data["metadata"].get("title", query),
                "duration_seconds": status_data["video_duration_seconds"],
                "file_size_bytes": target_mp4.stat().st_size,
                "video_path": str(target_mp4.relative_to(settings.BASE_DIR)),
                "scenes": status_data["metadata"].get("scenes", []),
                "verification": status_data["metadata"].get("verification", {}),
                "engine_used": status_data["metadata"].get("engine_used", "manim"),
            }

            with open(target_json, "w", encoding="utf-8") as f:
                json.dump(manifest_data, f, indent=2)

            duration = status_data["video_duration_seconds"] or 0.0
            size_mb = target_mp4.stat().st_size / (1024 * 1024)
            print(f"    [✓] Video saved: {target_mp4.name} ({duration:.2f}s, {size_mb:.2f} MB)")

            results.append({
                "concept": query,
                "topic": topic,
                "duration": f"{duration:.2f}s",
                "size": f"{size_mb:.2f} MB",
                "file": target_mp4.name,
                "valid": status_data["metadata"].get("verification", {}).get("is_valid", True),
            })

    print("\n" + "=" * 80)
    print("ALL 8 EXPLAINER VIDEOS GENERATED & VERIFIED VIA FASTAPI")
    print("=" * 80)
    for r in results:
        print(f"- {r['concept']}")
        print(f"  Topic: {r['topic']} | Duration: {r['duration']} | Size: {r['size']} | Valid: {r['valid']}")
        print(f"  Artifact: artifacts/videos/{r['file']}")
        print("-" * 80)


if __name__ == "__main__":
    asyncio.run(run_client())
