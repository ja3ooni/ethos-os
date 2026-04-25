"""API package for EthosOS REST API."""

from fastapi import APIRouter

from ethos_os.api.agents_registry import router as agents_registry_router
from ethos_os.api.agents import router as agents_router
from ethos_os.api.gates import router as gates_router
from ethos_os.api.hierarchy import router as hierarchy_router
from ethos_os.api.orchestration import router as orchestration_router
from ethos_os.api.chat import router as chat_router
from ethos_os.api.dashboard import router as dashboard_router
from ethos_os.api.sse import router as sse_router

api_router = APIRouter()
api_router.include_router(agents_registry_router)
api_router.include_router(agents_router)
api_router.include_router(gates_router)
api_router.include_router(hierarchy_router)
api_router.include_router(orchestration_router)
api_router.include_router(chat_router)
api_router.include_router(dashboard_router)
api_router.include_router(sse_router)

__all__ = [
    "api_router",
    "agents_registry_router",
    "agents_router",
    "gates_router",
    "hierarchy_router",
    "orchestration_router",
    "chat_router",
    "dashboard_router",
    "sse_router",
]