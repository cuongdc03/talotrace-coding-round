"""Unit tests for script generator and schema guardrails."""

import pytest

from app.models.script import SupportedTopic, VideoScript
from app.pipeline.script_generator import ScriptGenerator


@pytest.mark.asyncio
async def test_generate_script_deterministic_template_ph_scale():
    generator = ScriptGenerator(use_gemini=False)
    script, fallback_used = await generator.generate(
        query="How does the pH scale work?",
        topic=SupportedTopic.PH_SCALE,
    )
    assert isinstance(script, VideoScript)
    assert script.topic == SupportedTopic.PH_SCALE
    assert len(script.scenes) >= 3
    for scene in script.scenes:
        assert len(scene.narration) > 15
        assert scene.visual_type is not None
        assert len(scene.title) > 0


@pytest.mark.asyncio
async def test_generate_script_all_required_topics():
    # Test deterministic template retrieval without external LLM call
    generator = ScriptGenerator(use_gemini=False)
    for topic in [
        SupportedTopic.PH_SCALE,
        SupportedTopic.COVALENT_BONDS,
        SupportedTopic.IONIC_VS_COVALENT,
        SupportedTopic.ATOMIC_STRUCTURE,
        SupportedTopic.EXO_VS_ENDOTHERMIC,
        SupportedTopic.PERIODIC_TRENDS,
        SupportedTopic.STATES_OF_MATTER,
        SupportedTopic.ACID_BASE_NEUTRALIZATION,
    ]:
        script, _ = await generator.generate(query="Test query", topic=topic)
        assert isinstance(script, VideoScript)
        assert script.topic == topic
        assert len(script.scenes) >= 3
        # Ensure LaTeX formulas are present in our 30s explainer templates
        assert any(s.latex_formula is not None for s in script.scenes)


@pytest.mark.asyncio
async def test_script_guardrail_rejection_and_fallback():
    generator = ScriptGenerator()

    # Mock LLM returning invalid schema
    async def bad_llm_provider(*args, **kwargs):
        return {"invalid": "not conforming to VideoScript"}

    script, fallback_used = await generator.generate(
        query="Why do atoms form covalent bonds?",
        topic=SupportedTopic.COVALENT_BONDS,
        llm_provider=bad_llm_provider,
    )
    assert fallback_used is True
    assert isinstance(script, VideoScript)
    assert script.topic == SupportedTopic.COVALENT_BONDS
