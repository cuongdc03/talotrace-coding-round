"""Global test fixtures and configuration."""
import os
import tempfile
from pathlib import Path
import pytest
import pytest_asyncio
from app.core.config import Settings


@pytest.fixture
def tmp_settings(tmp_path: Path) -> Settings:
    """Fixture providing isolated temporary directories and database path."""
    artifacts = tmp_path / "artifacts"
    db_path = tmp_path / "test.sqlite3"
    s = Settings(
        BASE_DIR=tmp_path,
        ARTIFACTS_DIR=artifacts,
        VIDEOS_DIR=artifacts / "videos",
        AUDIO_DIR=artifacts / "audio",
        FRAMES_DIR=artifacts / "frames",
        DATABASE_PATH=db_path,
    )
    s.ensure_directories()
    return s
