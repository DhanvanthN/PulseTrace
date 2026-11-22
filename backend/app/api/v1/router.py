from fastapi import APIRouter

from app.api.v1.endpoints import analysis, auth, health, incidents, logs, projects, services

api_v1_router = APIRouter()
api_v1_router.include_router(health.router)
api_v1_router.include_router(auth.router)
api_v1_router.include_router(projects.router)
api_v1_router.include_router(logs.router)
api_v1_router.include_router(services.router)
api_v1_router.include_router(analysis.router)
api_v1_router.include_router(incidents.router)