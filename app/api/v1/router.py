"""API v1 master router."""

from fastapi import APIRouter

from app.api.v1.endpoints import health, jobs

api_router = APIRouter()
api_router.include_router(jobs.router, prefix="/videos", tags=["Videos"])
api_router.include_router(health.router, tags=["System"])
