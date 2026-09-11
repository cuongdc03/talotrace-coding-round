"""Unit tests for audio synthesizer and duration alignment."""

from pathlib import Path

import pytest

from app.models.script import Scene, SupportedTopic, VideoScript
from app.pipeline.audio_synthesizer import AudioSynthesizer


@pytest.mark.asyncio
async def test_synthesize_scene_audio(tmp_path: Path):
    synthesizer = AudioSynthesizer()
    audio_path = tmp_path / "test_scene.mp3"
    narration = "The pH scale measures acidity from 0 to 14."

    duration = await synthesizer.synthesize_scene_audio(
        narration=narration,
        output_path=audio_path,
    )

    assert audio_path.exists()
    assert audio_path.stat().st_size > 0
    assert duration > 0.5


@pytest.mark.asyncio
async def test_synthesize_script_audios(tmp_path: Path):
    synthesizer = AudioSynthesizer()
    script = VideoScript(
        topic=SupportedTopic.PH_SCALE,
        title="pH Scale Test",
        overview="Testing script audio synthesis",
        scenes=[
            Scene(
                scene_id=1,
                title="Scene 1",
                narration="Acids release hydrogen ions in aqueous solution.",
                visual_type="ph_spectrum",
                key_takeaway="Acids release H+ ions.",
            ),
            Scene(
                scene_id=2,
                title="Scene 2",
                narration="Bases neutralize acids by accepting hydrogen ions.",
                visual_type="ph_ions",
                key_takeaway="Bases neutralize acids.",
            ),
        ],
    )

    results = await synthesizer.synthesize_script_audios(script, output_dir=tmp_path)
    assert len(results) == 2
    for path, duration in results:
        assert path.exists()
        assert path.stat().st_size > 0
        assert duration > 0.5


@pytest.mark.asyncio
async def test_get_audio_duration_with_fallback(tmp_path: Path):
    synthesizer = AudioSynthesizer()
    # Test measuring a generated file
    fallback_path = tmp_path / "fallback.mp3"
    duration = await synthesizer._generate_fallback_audio(
        text="A short test sentence.",
        output_path=fallback_path,
        target_duration=3.0,
    )
    assert fallback_path.exists()
    assert duration > 0.5
