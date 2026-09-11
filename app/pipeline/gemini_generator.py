"""Gemini LLM script generator for creating structured ~30s pedagogical chemistry scripts."""

import asyncio
import logging
import os
from typing import Optional

from google import genai
from google.genai import types

from app.core.config import settings
from app.models.script import SupportedTopic, VideoScript

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an award-winning chemistry educator creating 30-second explainer videos in the style of 3Blue1Brown.
Your goal is to thoroughly explain the given chemistry question with high conceptual clarity, pedagogical depth, and mathematical/chemical rigor.

Requirements:
1. Structure: Exactly 4 pedagogical scenes (Introduction hook, microscopic mechanism, dynamic visual transformation, practical takeaway).
2. Duration target: Exactly 30 seconds total video length.
3. Voiceover narration: Spoken narration across all scenes MUST total between 65 and 75 words (~2.3 words/second, totaling ~28 seconds of spoken audio). Each individual scene MUST have between 15 and 18 words of spoken narration. Do NOT write less than 60 words and do NOT exceed 80 words.
4. Formulas & Equations: For scenes highlighting chemical formulas, reactions, or laws, provide a valid LaTeX math string in the `latex_formula` field (e.g., "\\mathrm{pH} = -\\log_{10}[\\mathrm{H}^+]" or "\\mathrm{H}_2 + \\mathrm{Cl}_2 \\rightarrow 2\\mathrm{HCl}").
5. The `topic` field MUST match the requested topic enum string exactly.
"""


class GeminiScriptGenerator:
    """Uses Google Gemini 2.5 Flash to generate structured educational scripts."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        if api_key is not None:
            self.api_key = api_key if api_key.strip() else None
        else:
            self.api_key = settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY")

        self._client: Optional[genai.Client] = None
        if self.api_key:
            try:
                self._client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini client: {e}")

    async def generate_script(
        self, topic: SupportedTopic, query: str
    ) -> Optional[VideoScript]:
        """Generate a validated 30s VideoScript using Gemini LLM with structured schema output."""
        if not self._client:
            logger.info("Gemini API key not configured. Skipping LLM script generation.")
            return None

        prompt = f"""Topic Category: {topic.value}
Student Query: "{query}"

Generate a 4-to-5 scene educational video storyboard explaining this concept in ~30 seconds with LaTeX formulas and high pedagogical clarity.
Ensure the topic is set to "{topic.value}".
"""

        try:
            logger.info(f"Invoking Gemini LLM (gemini-2.5-flash) for query: '{query}'")
            loop = asyncio.get_running_loop()

            def _call_gemini() -> str:
                response = self._client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        response_mime_type="application/json",
                        response_schema=VideoScript,
                        temperature=0.3,
                    ),
                )
                return response.text

            json_text = await loop.run_in_executor(None, _call_gemini)
            script = VideoScript.model_validate_json(json_text)
            logger.info(
                f"Successfully generated script via Gemini LLM for '{query}' ({len(script.scenes)} scenes)"
            )
            return script
        except Exception as e:
            logger.warning(
                f"Gemini LLM script generation failed for '{query}': {e}. Falling back to template.",
                exc_info=True,
            )
            return None
