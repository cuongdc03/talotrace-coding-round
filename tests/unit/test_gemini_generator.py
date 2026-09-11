import pytest

from app.models.script import SupportedTopic, VideoScript
from app.pipeline.gemini_generator import GeminiScriptGenerator


@pytest.mark.asyncio
async def test_gemini_generator_fallback_without_key():
    generator = GeminiScriptGenerator(api_key="")
    script = await generator.generate_script(
        SupportedTopic.PH_SCALE,
        "How does the pH scale work?",
    )
    # Without key, returns None so caller falls back cleanly
    assert script is None


@pytest.mark.asyncio
async def test_gemini_generator_with_valid_key():
    generator = GeminiScriptGenerator()
    if not generator.api_key:
        pytest.skip("GEMINI_API_KEY not configured in environment")

    script = await generator.generate_script(
        SupportedTopic.PH_SCALE,
        "How does the pH scale work?",
    )
    assert script is not None
    assert isinstance(script, VideoScript)
    assert len(script.scenes) >= 3
    assert any(s.latex_formula is not None for s in script.scenes)
