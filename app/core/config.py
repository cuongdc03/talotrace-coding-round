"""Application core configuration."""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Service settings and environment configurations."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Service Info
    PROJECT_NAME: str = "AI Chemistry Video Request Service"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False

    # Storage Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    ARTIFACTS_DIR: Path = BASE_DIR / "artifacts"
    VIDEOS_DIR: Path = ARTIFACTS_DIR / "videos"
    AUDIO_DIR: Path = ARTIFACTS_DIR / "audio"
    FRAMES_DIR: Path = ARTIFACTS_DIR / "frames"
    DATABASE_PATH: Path = BASE_DIR / "video_service.sqlite3"

    # Audio & Video Engine Defaults
    TTS_VOICE: str = "en-US-GuyNeural"
    VIDEO_FPS: int = 24
    VIDEO_WIDTH: int = 1920
    VIDEO_HEIGHT: int = 1080

    # Worker Settings
    MAX_CONCURRENT_JOBS: int = 2
    JOB_TIMEOUT_SECONDS: int = 180

    def ensure_directories(self) -> None:
        """Ensure all required artifact directories exist."""
        self.ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
        self.VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
        self.AUDIO_DIR.mkdir(parents=True, exist_ok=True)
        self.FRAMES_DIR.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_directories()
