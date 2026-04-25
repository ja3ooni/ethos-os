"""API package for EthosOS REST API."""

from fastapi import APIRouter

from ethos_os.api.agents import router as agents_router
from ethos_os.api.gates import router as gates_router
from ethos_os.api.hierarchy import router as hierarchy_router

api_router = APIRouter()
api_router.include_router(agents_router)
api_router.include_router(gates_router)
api_router.include_router(hierarchy_router)

__all__ = ["api_router", "agents_router", "gates_router", "hierarchy_router"]