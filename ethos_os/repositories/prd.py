"""PRD repository."""

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from ethos_os.models.prd import PRD, PRDStatus
from ethos_os.repositories.base import BaseRepository


class PRDRepository(BaseRepository[PRD]):
    """Repository for PRD entity."""
    
    model_class = PRD
    
    def list_by_project(self, project_id: str) -> list[PRD]:
        """List PRDs by project."""
        stmt = select(PRD).where(PRD.project_id == project_id)
        return list(self.session.execute(stmt).scalars().all())
    
    def get_latest_by_project(self, project_id: str) -> PRD | None:
        """Get the latest PRD for a project."""
        stmt = select(PRD).where(
            PRD.project_id == project_id
        ).order_by(PRD.created_at.desc())
        return self.session.execute(stmt).scalar_one_or_none()
    
    def get_by_project(self, project_id: str) -> PRD | None:
        """Get PRD for a project (one-to-one)."""
        stmt = select(PRD).where(PRD.project_id == project_id)
        return self.session.execute(stmt).scalar_one_or_none()
    
    def search_by_intent(self, query: str) -> list[PRD]:
        """Search PRDs by intent (LIKE).
        
        Note: For semantic search, use Qdrant (Phase 2).
        """
        stmt = select(PRD).where(PRD.intent.like(f"%{query}%"))
        return list(self.session.execute(stmt).scalars().all())
    
    def create(self, data: dict[str, Any]) -> PRD:
        """Create a new PRD.
        
        Sets default status = 'draft'.
        One PRD per project (enforced at model level).
        """
        project_id = data.get("project_id")
        if not project_id:
            raise ValueError("project_id is required")
        
        # Check for existing PRD
        existing = self.get_by_project(project_id)
        if existing:
            raise ValueError(f"PRD already exists for project {project_id}")
        
        # Validate required fields
        if not data.get("intent"):
            raise ValueError("intent is required")
        if not data.get("success_metric"):
            raise ValueError("success_metric is required")
        
        # Set default status
        if "status" not in data:
            data["status"] = PRDStatus.DRAFT.value
        
        return super().create(data)
    
    def submit_for_review(self, prd_id: str) -> PRD:
        """Submit PRD for review."""
        return self.update(prd_id, {"status": PRDStatus.PENDING_REVIEW.value})
    
    def approve(self, prd_id: str, reviewer_id: str) -> PRD:
        """Approve a PRD."""
        return self.update(prd_id, {
            "status": PRDStatus.APPROVED.value,
            "reviewed_by": reviewer_id,
            "reviewed_at": datetime.utcnow(),
        })
    
    def reject(self, prd_id: str, reviewer_id: str) -> PRD:
        """Reject a PRD."""
        return self.update(prd_id, {
            "status": PRDStatus.REJECTED.value,
            "reviewed_by": reviewer_id,
            "reviewed_at": datetime.utcnow(),
        })