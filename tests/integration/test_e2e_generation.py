"""End-to-end integration tests verifying generation for the 3 required chemistry concepts."""

import json

import pytest

from app.core.config import settings
from app.pipeline.video_assembler import VideoAssembler


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "video_slug,expected_topic",
    [
        ("ph_scale", "PH_SCALE"),
        ("covalent_bonds", "COVALENT_BONDS"),
        ("ionic_vs_covalent", "IONIC_VS_COVALENT"),
    ],
)
async def test_sample_video_artifacts_validity(video_slug: str, expected_topic: str):
    """Verify that committed sample videos are non-corrupt, valid MP4s, and have correct metadata."""
    video_path = settings.VIDEOS_DIR / f"{video_slug}.mp4"
    json_path = settings.VIDEOS_DIR / f"{video_slug}.json"

    assert video_path.exists(), f"Sample video artifact missing: {video_path}"
    assert video_path.stat().st_size > 50000, f"Video file abnormally small: {video_path}"

    assert json_path.exists(), f"Sample video manifest missing: {json_path}"
    with open(json_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest["topic"] == expected_topic
    assert len(manifest["scenes"]) >= 3
    assert manifest["duration_seconds"] > 10.0

    # Probe artifact with ffprobe
    assembler = VideoAssembler()
    verification = await assembler.verify_video_artifact(video_path)
    assert verification["is_valid"] is True
    assert verification["has_video"] is True
    assert verification["has_audio"] is True
    assert verification["duration"] > 10.0
