"""Audio synthesis and duration alignment engine."""

import asyncio
import logging
import shutil
from pathlib import Path
from typing import List, Optional, Tuple

import edge_tts

from app.core.config import settings
from app.models.script import VideoScript

logger = logging.getLogger(__name__)


class AudioSynthesizer:
    """Synthesizes scene narration audio with multi-tier fallback and exact duration extraction."""

    def __init__(self, voice: Optional[str] = None) -> None:
        self.voice = voice or settings.TTS_VOICE

    async def measure_audio_duration(self, audio_path: Path) -> float:
        """Measure the duration in seconds of an audio file using ffprobe."""
        ffprobe_bin = shutil.which("ffprobe")
        if not ffprobe_bin:
            # Fallback to ffmpeg output inspection if ffprobe is not present
            logger.warning("ffprobe not found; attempting duration estimation via file size")
            # 128kbps mp3: ~16000 bytes per second
            size = audio_path.stat().st_size
            return max(1.0, round(size / 16000.0, 2))

        proc = await asyncio.create_subprocess_exec(
            ffprobe_bin,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(audio_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        try:
            return float(stdout.decode().strip())
        except (ValueError, TypeError):
            logger.warning("Failed to parse duration from ffprobe output: %s", stdout)
            return 5.0

    async def _generate_fallback_audio(
        self,
        text: str,
        output_path: Path,
        target_duration: float = 5.0,
    ) -> float:
        """Fallback audio generation using macOS 'say' command or FFmpeg synthesized tone."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        say_bin = shutil.which("say")
        ffmpeg_bin = shutil.which("ffmpeg")

        # Try macOS native 'say'
        if say_bin and ffmpeg_bin:
            try:
                aiff_path = output_path.with_suffix(".aiff")
                say_proc = await asyncio.create_subprocess_exec(
                    say_bin,
                    "-o",
                    str(aiff_path),
                    text,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await say_proc.communicate()

                if aiff_path.exists() and aiff_path.stat().st_size > 0:
                    # Convert AIFF to MP3
                    conv_proc = await asyncio.create_subprocess_exec(
                        ffmpeg_bin,
                        "-y",
                        "-i",
                        str(aiff_path),
                        "-c:a",
                        "libmp3lame",
                        "-b:a",
                        "128k",
                        str(output_path),
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    await conv_proc.communicate()
                    aiff_path.unlink(missing_ok=True)
                    if output_path.exists() and output_path.stat().st_size > 0:
                        return await self.measure_audio_duration(output_path)
            except Exception as e:
                logger.warning("macOS say fallback failed: %s", e)

        # Final fallback: FFmpeg sine tone / silence generator
        if ffmpeg_bin:
            try:
                # Approximate 150 words per minute ~ 2.5 words per second
                word_count = len(text.split())
                calc_duration = max(3.0, round(word_count / 2.5, 1))
                duration = target_duration if target_duration > 0 else calc_duration

                proc = await asyncio.create_subprocess_exec(
                    ffmpeg_bin,
                    "-y",
                    "-f",
                    "lavfi",
                    "-i",
                    f"sine=frequency=440:duration={duration}",
                    "-c:a",
                    "libmp3lame",
                    "-b:a",
                    "128k",
                    str(output_path),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await proc.communicate()
                if output_path.exists() and output_path.stat().st_size > 0:
                    return duration
            except Exception as e:
                logger.error("FFmpeg synthetic fallback failed: %s", e)

        raise RuntimeError("Failed to generate audio through any available audio engine")

    async def synthesize_scene_audio(
        self,
        narration: str,
        output_path: Path,
        target_duration: float = 5.0,
    ) -> float:
        """
        Synthesize voice narration for a single scene to an MP3 file.
        Returns the duration of the audio in seconds.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            communicate = edge_tts.Communicate(narration, voice=self.voice)
            await asyncio.wait_for(communicate.save(str(output_path)), timeout=10.0)
            if output_path.exists() and output_path.stat().st_size > 0:
                duration = await self.measure_audio_duration(output_path)
                if duration > 0.1:
                    return duration
        except Exception as exc:
            logger.warning(
                "edge-tts synthesis failed or timed out ('%s'): %s. Switching to fallback audio engine.",
                narration[:30],
                exc,
            )

        # Fallback
        return await self._generate_fallback_audio(
            text=narration,
            output_path=output_path,
            target_duration=target_duration,
        )

    async def synthesize_script_audios(
        self,
        script: VideoScript,
        output_dir: Path,
    ) -> List[Tuple[Path, float]]:
        """
        Synthesize audio for all scenes in a script.
        Returns a list of (scene_audio_path, duration_seconds) tuples.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        results: List[Tuple[Path, float]] = []

        for scene in script.scenes:
            scene_path = output_dir / f"scene_{scene.scene_id:02d}.mp3"
            target_dur = scene.duration_target_seconds or 5.0
            duration = await self.synthesize_scene_audio(
                narration=scene.narration,
                output_path=scene_path,
                target_duration=target_dur,
            )
            results.append((scene_path, duration))

        return results
