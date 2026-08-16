from fastapi import APIRouter

from app.api.routes import approvals, eval, metrics, workflows

api_router = APIRouter()
api_router.include_router(workflows.router)
api_router.include_router(approvals.router)
api_router.include_router(metrics.router)
api_router.include_router(eval.router)
