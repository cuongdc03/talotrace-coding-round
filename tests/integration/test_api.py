"""Integration tests for FastAPI endpoints and video streaming."""

from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.v1.endpoints.jobs import get_video_service
from app.core.config import settings
from app.main import app
from app.models.job import JobStatus


@pytest.fixture(autouse=True)
async def setup_test_environment(tmp_path: Path, monkeypatch):
    """Point database and artifacts to temporary directory for API tests."""
    import app.main as main_mod

    db_path = tmp_path / "api_test.db"
    artifacts_dir = tmp_path / "artifacts"
    videos_dir = artifacts_dir / "videos"
    audio_dir = artifacts_dir / "audio"
    frames_dir = artifacts_dir / "frames"

    monkeypatch.setattr(settings, "DATABASE_PATH", db_path)
    monkeypatch.setattr(settings, "ARTIFACTS_DIR", artifacts_dir)
    monkeypatch.setattr(settings, "VIDEOS_DIR", videos_dir)
    monkeypatch.setattr(settings, "AUDIO_DIR", audio_dir)
    monkeypatch.setattr(settings, "FRAMES_DIR", frames_dir)
    settings.ensure_directories()

    # Reset globals
    main_mod.job_repository_instance = None
    main_mod.job_worker_instance = None
    main_mod.video_service_instance = None

    service = get_video_service()
    await service.repo.initialize()
    yield
    if service.worker._running:
        await service.worker.stop()


@pytest.mark.asyncio
async def test_health_check_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data


@pytest.mark.asyncio
async def test_create_and_get_job_lifecycle():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Submit Job
        create_res = await client.post(
            "/api/v1/videos/jobs",
            json={"query": "How does the pH scale work?"},
        )
        assert create_res.status_code == 202
        job_data = create_res.json()
        assert "id" in job_data
        assert job_data["query"] == "How does the pH scale work?"
        assert job_data["topic"] == "PH_SCALE"
        assert job_data["status"] == JobStatus.PENDING.value

        job_id = job_data["id"]

        # 2. Get Job
        get_res = await client.get(f"/api/v1/videos/jobs/{job_id}")
        assert get_res.status_code == 200
        retrieved_data = get_res.json()
        assert retrieved_data["id"] == job_id
        assert retrieved_data["query"] == "How does the pH scale work?"

        # 3. List Jobs
        list_res = await client.get("/api/v1/videos/jobs")
        assert list_res.status_code == 200
        list_data = list_res.json()
        assert list_data["total"] >= 1
        assert any(j["id"] == job_id for j in list_data["jobs"])


@pytest.mark.asyncio
async def test_get_nonexistent_job():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/videos/jobs/nonexistent_id")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_video_not_ready():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_res = await client.post(
            "/api/v1/videos/jobs",
            json={"query": "Why do atoms form covalent bonds?"},
        )
        job_id = create_res.json()["id"]

        # Request video before it's finished
        video_res = await client.get(f"/api/v1/videos/jobs/{job_id}/video")
        assert video_res.status_code in [404, 409]
