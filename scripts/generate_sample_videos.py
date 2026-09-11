"""Script to generate and verify sample educational videos for the 3 required chemistry queries."""

import asyncio
import json
import logging
import shutil

from app.core.config import settings
from app.models.job import JobStatus
from app.pipeline.pipeline import GenerationPipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("generate_sample_videos")

REQUIRED_CONCEPTS = [
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
]


async def generate_all() -> None:
    settings.ensure_directories()
    pipeline = GenerationPipeline()

    print("=" * 80)
    print("AI CHEMISTRY VIDEO SERVICE — SAMPLE GENERATION RUNNER")
    print("=" * 80)

    summary_results = []

    for item in REQUIRED_CONCEPTS:
        slug = item["slug"]
        query = item["query"]
        target_filename = item["filename"]
        target_video_path = settings.VIDEOS_DIR / target_filename
        target_json_path = settings.VIDEOS_DIR / f"{slug}.json"

        print(f"\n[+] Generating video for query: '{query}'")
        print(f"    Target artifact: {target_video_path}")

        async def progress(status: JobStatus, pct: int, step: str):
            print(f"    [{pct:02d}%] {status.value}: {step}")

        result = await pipeline.run(
            job_id=slug,
            query=query,
            on_progress=progress,
        )

        # Copy/move to canonical target video path
        if result.video_path != target_video_path:
            shutil.copy2(result.video_path, target_video_path)

        # Save metadata manifest
        manifest_data = {
            "query": query,
            "topic": result.topic.value,
            "title": result.script.title,
            "overview": result.script.overview,
            "duration_seconds": result.duration_seconds,
            "video_path": str(target_video_path.relative_to(settings.BASE_DIR)),
            "file_size_bytes": target_video_path.stat().st_size,
            "fallback_used": result.fallback_used,
            "scenes": [s.model_dump() for s in result.script.scenes],
            "verification": result.verification,
        }

        with open(target_json_path, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2)

        summary_results.append(
            {
                "query": query,
                "topic": result.topic.value,
                "duration": f"{result.duration_seconds:0.2f}s",
                "size_mb": f"{target_video_path.stat().st_size / (1024 * 1024):0.2f} MB",
                "file": target_filename,
                "valid": result.verification.get("is_valid", False),
            }
        )

    print("\n" + "=" * 80)
    print("GENERATION SUMMARY")
    print("=" * 80)
    for r in summary_results:
        print(f"Query:    {r['query']}")
        print(f"Topic:    {r['topic']}")
        print(f"Duration: {r['duration']} | Size: {r['size_mb']} | Verified: {r['valid']}")
        print(f"Artifact: artifacts/videos/{r['file']}")
        print("-" * 80)


if __name__ == "__main__":
    asyncio.run(generate_all())
