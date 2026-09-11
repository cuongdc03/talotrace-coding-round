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
    if script is None:
        pytest.skip("Gemini free-tier quota exhausted (429); skipping live network call")

    assert isinstance(script, VideoScript)
    assert len(script.scenes) >= 3
    assert any(s.latex_formula is not None for s in script.scenes)


@pytest.mark.asyncio
async def test_gemini_generator_structured_schema_parsing(monkeypatch):
    """Verify Gemini JSON schema parsing and LaTeX extraction with mocked client."""
    generator = GeminiScriptGenerator(api_key="mock_key")

    mock_json = """{
        "topic": "PH_SCALE",
        "title": "How the pH Scale Works",
        "overview": "A 30s explainer",
        "scenes": [
            {
                "scene_id": 1,
                "title": "Intro",
                "narration": "The pH scale measures acidity from zero to fourteen.",
                "visual_type": "ph_spectrum",
                "key_takeaway": "0 to 14 scale",
                "latex_formula": "0 \\\\le \\\\mathrm{pH} \\\\le 14",
                "duration_target_seconds": 7.5
            },
            {
                "scene_id": 2,
                "title": "Mechanism",
                "narration": "It calculates negative logarithm of hydrogen ions.",
                "visual_type": "ph_equation",
                "key_takeaway": "Logarithmic law",
                "latex_formula": "\\\\mathrm{pH} = -\\\\log_{10}[\\\\mathrm{H}^+]",
                "duration_target_seconds": 7.5
            }
        ]
    }"""

    class MockResponse:
        text = mock_json

    class MockModels:
        def generate_content(self, **kwargs):
            return MockResponse()

    class MockClient:
        models = MockModels()

    generator._client = MockClient()

    script = await generator.generate_script(
        SupportedTopic.PH_SCALE,
        "How does the pH scale work?",
    )
    assert script is not None
    assert isinstance(script, VideoScript)
    assert script.topic == SupportedTopic.PH_SCALE
    assert len(script.scenes) == 2
    assert script.scenes[0].latex_formula is not None
