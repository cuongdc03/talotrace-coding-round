"""Unified video generation pipeline orchestrator with Manim integration."""

import asyncio
import logging
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from app.core.config import settings
from app.models.job import JobStatus
from app.models.script import SupportedTopic, VideoScript
from app.pipeline.audio_synthesizer import AudioSynthesizer
from app.pipeline.classifier import ConceptClassifier
from app.pipeline.manim_renderer import ManimRenderer
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
    """Orchestrates end-to-end video generation pipeline with Manim and procedural fallbacks."""

    def __init__(
        self,
        classifier: Optional[ConceptClassifier] = None,
        script_generator: Optional[ScriptGenerator] = None,
        audio_synthesizer: Optional[AudioSynthesizer] = None,
        visual_compositor: Optional[VisualCompositor] = None,
        video_assembler: Optional[VideoAssembler] = None,
        manim_renderer: Optional[ManimRenderer] = None,
    ) -> None:
        self.classifier = classifier or ConceptClassifier()
        self.script_generator = script_generator or ScriptGenerator()
        self.audio_synthesizer = audio_synthesizer or AudioSynthesizer()
        self.visual_compositor = visual_compositor or VisualCompositor()
        self.video_assembler = video_assembler or VideoAssembler()
        self.manim_renderer = manim_renderer or ManimRenderer(quality="m")

    async def _combine_video_and_audio(
        self,
        video_path: Path,
        audio_paths: list[Path],
        output_path: Path,
    ) -> Path:
        """Combine Manim video track with synthesized narration audio tracks."""
        ffmpeg_bin = shutil.which("ffmpeg") or "ffmpeg"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Concatenate audio files first if multiple scenes
        if len(audio_paths) == 1:
            full_audio = audio_paths[0]
            concat_txt = None
        else:
            concat_txt = output_path.parent / f"{output_path.stem}_audio_concat.txt"
            with open(concat_txt, "w", encoding="utf-8") as f:
                for a in audio_paths:
                    f.write(f"file '{a.resolve()}'\n")

            full_audio = output_path.parent / f"{output_path.stem}_combined_audio.mp3"
            proc_audio = await asyncio.create_subprocess_exec(
                ffmpeg_bin,
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_txt),
                "-c",
                "copy",
                str(full_audio),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc_audio.communicate()

        # Merge video and audio with AAC and H.264
        # Using -af apad ensures audio is padded with silence to match full video length
        cmd = [
            ffmpeg_bin,
            "-y",
            "-i",
            str(video_path),
            "-i",
            str(full_audio),
            "-c:v",
            "copy",
            "-af",
            "apad",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            "-movflags",
            "+faststart",
            str(output_path),
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            logger.error("FFmpeg audio-video merge failed: %s", stderr.decode())
            raise RuntimeError("Failed merging audio with Manim video")

        if concat_txt and concat_txt.exists():
            concat_txt.unlink(missing_ok=True)
        if full_audio != audio_paths[0] and full_audio.exists():
            full_audio.unlink(missing_ok=True)

        return output_path

    async def run(
        self,
        job_id: str,
        query: str,
        on_progress: Optional[Callable[[JobStatus, int, str], Any]] = None,
    ) -> GenerationResult:
        """
        Execute full generation workflow:
        1. Classify query (10%)
        2. Generate and validate script with schema guardrails (25%)
        3. Synthesize audio per scene and measure durations (45%)
        4. Render video:
           - Try Manim 3Blue1Brown vector animation if available (70%)
           - Fall back to high-resolution procedural chemistry compositor (75%)
        5. Verify artifact integrity (95%)
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
            JobStatus.GENERATING_SCRIPT, 25, f"Generating educational script for {topic.value}"
        )
        script, fallback_used = await self.script_generator.generate(query=query, topic=topic)

        # Prepare job artifact directories
        job_audio_dir = settings.AUDIO_DIR / job_id
        job_frames_dir = settings.FRAMES_DIR / job_id
        job_video_path = settings.VIDEOS_DIR / f"{job_id}.mp4"

        # 3. Audio Synthesis
        await notify(
            JobStatus.SYNTHESIZING_AUDIO,
            45,
            "Synthesizing voice narration and calculating scene durations",
        )
        scene_audios = await self.audio_synthesizer.synthesize_script_audios(
            script, output_dir=job_audio_dir
        )
        total_audio_duration = sum(dur for _, dur in scene_audios)

        rendered_with_manim = False

        # 4. Attempt Manim Rendering if available
        if self.manim_renderer.is_available():
            await notify(
                JobStatus.RENDERING_VIDEO,
                65,
                "Rendering 3Blue1Brown-style vector animations with Manim",
            )
            manim_raw_mp4 = settings.VIDEOS_DIR / f"{job_id}_manim_raw.mp4"
            try:
                target_video_duration = max(29.0, total_audio_duration)
                rendered_manim = await self.manim_renderer.render_topic_video(
                    topic=topic,
                    output_path=manim_raw_mp4,
                    duration=target_video_duration,
                )
                if rendered_manim and rendered_manim.exists():
                    # Combine Manim video with synthesized audio
                    audio_paths = [p for p, _ in scene_audios]
                    await self._combine_video_and_audio(rendered_manim, audio_paths, job_video_path)
                    rendered_with_manim = True
                    logger.info("Job %s successfully generated via Manim engine", job_id)
            except Exception as e:
                logger.warning(
                    "Manim rendering failed (%s); falling back to procedural visual engine", e
                )

        # 5. Fallback to Procedural Visual Compositor if Manim wasn't used
        if not rendered_with_manim:
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
                    SceneMedia(
                        image_path=frame_path, audio_path=audio_path, duration_seconds=duration
                    )
                )

            await notify(JobStatus.RENDERING_VIDEO, 85, "Assembling synchronized MP4 with FFmpeg")
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
            "engine_used": "manim" if rendered_with_manim else "procedural_compositor",
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
