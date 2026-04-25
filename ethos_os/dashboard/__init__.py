"""Dashboard package - Read-only UI for initiative tree, gate status, heartbeat timeline."""

from fastapi import APIRouter

router = APIRouter(tags=["dashboard"])