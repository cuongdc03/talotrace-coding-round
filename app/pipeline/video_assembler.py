"""FFmpeg video assembler and artifact verification engine."""

import asyncio
import json
import logging
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


@dataclass
class SceneMedia:
    """Media assets corresponding to a single scene."""

    image_path: Path
    audio_path: Path
    duration_seconds: float


class VideoAssembler:
    """Assembles synced 1080p MP4 videos from scene visuals and narration using FFmpeg."""

    def __init__(self, fps: int = 24) -> None:
        self.fps = fps
        self.ffmpeg_bin = shutil.which("ffmpeg") or "ffmpeg"
        self.ffprobe_bin = shutil.which("ffprobe") or "ffprobe"

    async def assemble(
        self,
        scenes: List[SceneMedia],
        output_path: Path,
    ) -> Path:
        """
        Assemble a list of scene images and audio tracks into a final synced MP4 video.
        Uses two-pass rendering: encodes each scene segment, then concatenates using concat demuxer.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if not scenes:
            raise ValueError("Cannot assemble video without scenes")

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            segment_paths: List[Path] = []

            for idx, scene in enumerate(scenes):
                segment_path = tmp_path / f"segment_{idx:03d}.mp4"
                segment_paths.append(segment_path)

                # Ensure non-zero positive duration
                duration = max(1.0, round(scene.duration_seconds, 2))

                # Render scene video segment
                cmd = [
                    self.ffmpeg_bin,
                    "-y",
                    "-loop",
                    "1",
                    "-t",
                    str(duration),
                    "-i",
                    str(scene.image_path),
                    "-i",
                    str(scene.audio_path),
                    "-c:v",
                    "libx264",
                    "-tune",
                    "stillimage",
                    "-preset",
                    "fast",
                    "-c:a",
                    "aac",
                    "-b:a",
                    "192k",
                    "-pix_fmt",
                    "yuv420p",
                    "-shortest",
                    str(segment_path),
                ]

                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                _, stderr = await proc.communicate()
                if proc.returncode != 0:
                    logger.error("FFmpeg segment error for scene %d: %s", idx, stderr.decode())
                    raise RuntimeError(f"FFmpeg failed encoding scene segment {idx}")

            # Create concat manifest
            concat_list_file = tmp_path / "concat.txt"
            with open(concat_list_file, "w", encoding="utf-8") as f:
                for seg in segment_paths:
                    f.write(f"file '{seg.resolve()}'\n")

            # Concatenate all segments into output_path with faststart flag for web streaming
            concat_cmd = [
                self.ffmpeg_bin,
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_list_file),
                "-c",
                "copy",
                "-movflags",
                "+faststart",
                str(output_path),
            ]

            proc = await asyncio.create_subprocess_exec(
                *concat_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await proc.communicate()
            if proc.returncode != 0:
                logger.error("FFmpeg concat error: %s", stderr.decode())
                raise RuntimeError("FFmpeg failed concatenating video segments")

        return output_path

    async def verify_video_artifact(self, video_path: Path) -> Dict[str, Any]:
        """
        Validate that the video artifact is non-corrupt, has non-zero size,
        contains valid video/audio streams, and has valid duration.
        """
        if not video_path.exists():
            return {"is_valid": False, "error": "File does not exist"}

        size_bytes = video_path.stat().st_size
        if size_bytes < 1000:
            return {"is_valid": False, "error": f"File too small ({size_bytes} bytes)"}

        cmd = [
            self.ffprobe_bin,
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(video_path),
        ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        if proc.returncode != 0:
            return {"is_valid": False, "error": "ffprobe probe failed"}

        try:
            probe_data = json.loads(stdout.decode())
            streams = probe_data.get("streams", [])
            has_video = any(s.get("codec_type") == "video" for s in streams)
            has_audio = any(s.get("codec_type") == "audio" for s in streams)
            duration = float(probe_data.get("format", {}).get("duration", 0.0))

            is_valid = has_video and has_audio and duration > 0.5
            return {
                "is_valid": is_valid,
                "duration": duration,
                "size_bytes": size_bytes,
                "has_video": has_video,
                "has_audio": has_audio,
                "format": probe_data.get("format", {}).get("format_name"),
            }
        except Exception as exc:
            return {"is_valid": False, "error": f"Failed parsing probe output: {exc}"}
