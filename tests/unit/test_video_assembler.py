"""Unit tests for FFmpeg video assembler and artifact verification."""

import subprocess
from pathlib import Path

import pytest
from PIL import Image

from app.pipeline.video_assembler import SceneMedia, VideoAssembler


@pytest.fixture
def sample_scenes(tmp_path: Path):
    """Create sample dummy image and audio files for testing assembly."""
    scenes = []
    for i in range(2):
        img_path = tmp_path / f"img_{i}.png"
        img = Image.new("RGB", (1920, 1080), color=(20 * i + 10, 30 * i + 20, 50 * i + 30))
        img.save(img_path)

        audio_path = tmp_path / f"audio_{i}.mp3"
        # Generate 1.5s sine audio using ffmpeg
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                "sine=frequency=440:duration=1.5",
                "-c:a",
                "libmp3lame",
                str(audio_path),
            ],
            check=True,
            capture_output=True,
        )

        scenes.append(SceneMedia(image_path=img_path, audio_path=audio_path, duration_seconds=1.5))

    return scenes


@pytest.mark.asyncio
async def test_assemble_and_verify_video(tmp_path: Path, sample_scenes):
    assembler = VideoAssembler()
    output_mp4 = tmp_path / "test_output.mp4"

    result_path = await assembler.assemble(scenes=sample_scenes, output_path=output_mp4)

    assert result_path.exists()
    assert result_path.stat().st_size > 0

    # Verify artifact
    verification = await assembler.verify_video_artifact(result_path)
    assert verification["is_valid"] is True
    assert verification["duration"] >= 2.8
    assert verification["has_video"] is True
    assert verification["has_audio"] is True
