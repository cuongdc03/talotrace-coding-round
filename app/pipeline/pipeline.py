"""Unified video generation pipeline orchestrator."""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from app.core.config import settings
from app.models.job import JobStatus
from app.models.script import SupportedTopic, VideoScript
from app.pipeline.audio_synthesizer import AudioSynthesizer
from app.pipeline.classifier import ConceptClassifier
from app.pipeline.script_generator import ScriptGenerator
from app.pipeline.video_assembler import SceneMedia, VideoAssembler
from app.pipeline.visual_compositor import VisualCompositor

logger = logging.getLogger(__name__)


@dataclass
class GenerationResult:
    """Result of a video generation pipeline run."""

    topic: SupportedTopic
    script: VideoScript
    video_path: Path
    duration_seconds: float
    fallback_used: bool
    verification: Dict[str, Any]
    metadata: Dict[str, Any]


class GenerationPipeline:
    """Orchestrates end-to-end video generation pipeline with progress callbacks and quality gates."""

    def __init__(
        self,
        classifier: Optional[ConceptClassifier] = None,
        script_generator: Optional[ScriptGenerator] = None,
        audio_synthesizer: Optional[AudioSynthesizer] = None,
        visual_compositor: Optional[VisualCompositor] = None,
        video_assembler: Optional[VideoAssembler] = None,
    ) -> None:
        self.classifier = classifier or ConceptClassifier()
        self.script_generator = script_generator or ScriptGenerator()
        self.audio_synthesizer = audio_synthesizer or AudioSynthesizer()
        self.visual_compositor = visual_compositor or VisualCompositor()
        self.video_assembler = video_assembler or VideoAssembler()

    async def run(
        self,
        job_id: str,
        query: str,
        on_progress: Optional[Callable[[JobStatus, int, str], Any]] = None,
    ) -> GenerationResult:
        """
        Execute full generation workflow:
        1. Classify query (10%)
        2. Generate and validate script with schema guardrails (30%)
        3. Synthesize audio per scene and measure durations (55%)
        4. Render visual diagram frames per scene (75%)
        5. Assemble video with FFmpeg (85%)
        6. Verify artifact integrity (95%)
        """

        async def notify(status: JobStatus, pct: int, step: str) -> None:
            if on_progress:
                res = on_progress(status, pct, step)
                if hasattr(res, "__await__"):
                    await res

        # 1. Classification & Validation
        await notify(
            JobStatus.VALIDATING, 10, "Classifying chemistry query and checking guardrails"
        )
        topic = self.classifier.classify(query)
        logger.info("Job %s: Classified query '%s' as %s", job_id, query, topic)

        # 2. Script Generation
        await notify(
            JobStatus.GENERATING_SCRIPT, 30, f"Generating educational script for {topic.value}"
        )
        script, fallback_used = await self.script_generator.generate(query=query, topic=topic)

        # Prepare job artifact directories
        job_audio_dir = settings.AUDIO_DIR / job_id
        job_frames_dir = settings.FRAMES_DIR / job_id
        job_video_path = settings.VIDEOS_DIR / f"{job_id}.mp4"

        # 3. Audio Synthesis
        await notify(
            JobStatus.SYNTHESIZING_AUDIO,
            55,
            "Synthesizing voice narration and calculating scene durations",
        )
        scene_audios = await self.audio_synthesizer.synthesize_script_audios(
            script, output_dir=job_audio_dir
        )

        # 4. Visual Rendering
        await notify(
            JobStatus.RENDERING_VIDEO,
            75,
            "Rendering high-resolution chemistry diagrams and visual cards",
        )
        scene_medias: list[SceneMedia] = []
        for scene, (audio_path, duration) in zip(script.scenes, scene_audios):
            frame_path = job_frames_dir / f"scene_{scene.scene_id:02d}.png"
            self.visual_compositor.render_scene_frame(scene, topic, frame_path)
            scene_medias.append(
                SceneMedia(image_path=frame_path, audio_path=audio_path, duration_seconds=duration)
            )

        # 5. Video Assembly
        await notify(JobStatus.RENDERING_VIDEO, 85, "Assembling synchronized 1080p MP4 with FFmpeg")
        await self.video_assembler.assemble(scenes=scene_medias, output_path=job_video_path)

        # 6. Artifact Verification
        await notify(
            JobStatus.VERIFYING_ARTIFACT,
            95,
            "Verifying video stream integrity and container duration",
        )
        verification = await self.video_assembler.verify_video_artifact(job_video_path)
        if not verification.get("is_valid"):
            error_msg = verification.get("error", "Unknown artifact verification failure")
            raise RuntimeError(f"Video artifact verification failed: {error_msg}")

        total_duration = verification.get("duration", 0.0)
        metadata = {
            "topic": topic.value,
            "title": script.title,
            "scenes_count": len(script.scenes),
            "scenes": [s.model_dump() for s in script.scenes],
            "fallback_used": fallback_used,
            "estimated_cost_usd": 0.00,
            "verification": verification,
        }

        return GenerationResult(
            topic=topic,
            script=script,
            video_path=job_video_path,
            duration_seconds=total_duration,
            fallback_used=fallback_used,
            verification=verification,
            metadata=metadata,
        )
