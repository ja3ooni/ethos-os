"""EthosOS FastAPI application - Initiative-based OS for human-agent organizations."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ethos_os.api import api_router
from ethos_os.config import get_settings
from ethos_os.dashboard.routes import router as dashboard_router
from ethos_os.dashboard.chat import router as chat_router

settings = get_settings()

app = FastAPI(
    title="EthosOS API",
    description="Initiative-based OS for human-agent organizations. "
    "Every piece of work traces back to a stated initiative root. "
    "Agents execute with heartbeat-based autonomy; humans govern at boundaries that matter.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")
app.include_router(dashboard_router)
app.include_router(chat_router)


@app.get("/health", tags=["health"])
def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy", "service": "ethos-os", "version": "0.1.0"}


@app.get("/", tags=["root"])
def root() -> dict:
    """Root endpoint with API info."""
    return {
        "name": "EthosOS API",
        "version": "0.1.0",
        "docs": "/docs",
        "redoc": "/redoc",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("ethos_os.main:app", host="0.0.0.0", port=8000, reload=True)