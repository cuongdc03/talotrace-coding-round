"""Script generator with Pydantic guardrails and deterministic fallback."""

import logging
from typing import Any, Callable, Optional, Tuple

from pydantic import ValidationError

from app.models.script import SupportedTopic, VideoScript
from app.pipeline.gemini_generator import GeminiScriptGenerator
from app.pipeline.templates import get_template_script

logger = logging.getLogger(__name__)


class ScriptGenerator:
    """Generates and validates educational scripts, handling non-determinism with schema guardrails."""

    def __init__(
        self,
        max_retries: int = 1,
        gemini_generator: Optional[GeminiScriptGenerator] = None,
        use_gemini: bool = True,
    ) -> None:
        self.max_retries = max_retries
        if not use_gemini:
            self.gemini_generator = None
        else:
            self.gemini_generator = (
                gemini_generator if gemini_generator is not None else GeminiScriptGenerator()
            )

    async def generate(
        self,
        query: str,
        topic: SupportedTopic,
        llm_provider: Optional[Callable[..., Any]] = None,
    ) -> Tuple[VideoScript, bool]:
        """
        Generate a validated VideoScript.
        If llm_provider is provided, calls it with quality checks and retry.
        Otherwise, attempts Gemini LLM generation if configured.
        If no provider is supplied or if generation fails, seamlessly
        activates the curated deterministic fallback template.
        Returns: (validated_script, fallback_used: bool)
        """
        if llm_provider is None and self.gemini_generator:
            try:
                gemini_script = await self.gemini_generator.generate_script(topic=topic, query=query)
                if gemini_script:
                    total_words = sum(len(s.narration.split()) for s in gemini_script.scenes)
                    if 60 <= total_words <= 85:
                        logger.info(
                            "Successfully validated Gemini LLM script for %s (%d words)",
                            topic,
                            total_words,
                        )
                        return gemini_script, False
                    else:
                        logger.warning(
                            "Gemini script has %d words (target: 60-85 words for ~30s); falling back to 30s template for %s",
                            total_words,
                            topic,
                        )
            except Exception as exc:
                logger.warning("Gemini script generation attempt failed: %s", exc)

        if llm_provider is None:
            logger.info(
                "No LLM provider available or succeeded; using curated high-fidelity template for %s",
                topic,
            )
            return get_template_script(topic), True

        # Attempt LLM generation with retry on schema failure
        for attempt in range(self.max_retries + 1):
            try:
                raw_result = await llm_provider(query=query, topic=topic, attempt=attempt)
                if isinstance(raw_result, dict):
                    script = VideoScript.model_validate(raw_result)
                elif isinstance(raw_result, VideoScript):
                    script = raw_result
                else:
                    raise ValueError(f"Unsupported LLM output type: {type(raw_result)}")

                # Quality gate: verify scene count and narration length
                if len(script.scenes) < 2:
                    raise ValueError("Quality gate failed: script must contain at least 2 scenes")

                for scene in script.scenes:
                    if len(scene.narration.strip()) < 10:
                        raise ValueError(
                            f"Quality gate failed: scene {scene.scene_id} narration too short"
                        )

                logger.info("Successfully validated LLM-generated script for %s", topic)
                return script, False

            except (ValidationError, ValueError, Exception) as exc:
                logger.warning(
                    "Script validation failed on attempt %d for query '%s': %s",
                    attempt + 1,
                    query,
                    exc,
                )

        logger.warning(
            "All LLM generation attempts failed or were rejected by quality gate. Activating curated fallback template for %s.",
            topic,
        )
        return get_template_script(topic), True
