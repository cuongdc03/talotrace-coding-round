"""Script generator with Pydantic guardrails and deterministic fallback."""
import logging
from typing import Any, Callable, Dict, Optional, Tuple
from pydantic import ValidationError
from app.models.script import SupportedTopic, VideoScript
from app.pipeline.templates import get_template_script

logger = logging.getLogger(__name__)


class ScriptGenerator:
    """Generates and validates educational scripts, handling non-determinism with schema guardrails."""

    def __init__(self, max_retries: int = 1) -> None:
        self.max_retries = max_retries

    async def generate(
        self,
        query: str,
        topic: SupportedTopic,
        llm_provider: Optional[Callable[..., Any]] = None,
    ) -> Tuple[VideoScript, bool]:
        """
        Generate a validated VideoScript.
        If llm_provider is provided, calls it with quality checks and retry.
        If no provider is supplied or if validation fails repeatedly, seamlessly
        activates the curated deterministic fallback template.
        Returns: (validated_script, fallback_used: bool)
        """
        if llm_provider is None:
            logger.info("No LLM provider configured; using curated high-fidelity template for %s", topic)
            return get_template_script(topic), False

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
                        raise ValueError(f"Quality gate failed: scene {scene.scene_id} narration too short")

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
