"""Sprint repository."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from ethos_os.models.base import compute_path
from ethos_os.models.project import Project, ProjectStatus
from ethos_os.models.sprint import Sprint, SprintStatus
from ethos_os.repositories.base import BaseRepository


class SprintRepository(BaseRepository[Sprint]):
    """Repository for Sprint entity."""
    
    model_class = Sprint
    
    def list_by_project(self, project_id: str) -> list[Sprint]:
        """List sprints by project."""
        stmt = select(Sprint).where(Sprint.project_id == project_id)
        return list(self.session.execute(stmt).scalars().all())
    
    def list_active(self) -> list[Sprint]:
        """List active sprints."""
        stmt = select(Sprint).where(Sprint.status == SprintStatus.ACTIVE.value)
        return list(self.session.execute(stmt).scalars().all())
    
    def list_by_date_range(
        self,
        start_date: str,
        end_date: str,
    ) -> list[Sprint]:
        """List sprints by date range."""
        stmt = select(Sprint).where(
            Sprint.start_date >= start_date,
            Sprint.end_date <= end_date,
        )
        return list(self.session.execute(stmt).scalars().all())
    
    def get_lineage(self, sprint_id: str) -> dict:
        """Get sprint with full lineage.
        
        Returns {sprint, project, program, portfolio}
        """
        sprint = self.get_or_404(sprint_id)
        
        # Parse path segments
        if not sprint.path:
            return {
                "sprint": sprint,
                "project": None,
                "program": None,
                "portfolio": None,
            }
        
        segments = sprint.path.strip("/").split("/")
        
        # segments: [portfolio_id, program_id, project_id, sprint_id]
        portfolio_uuid = segments[0] if len(segments) > 0 else None
        program_uuid = segments[1] if len(segments) > 1 else None
        project_uuid = segments[2] if len(segments) > 2 else None
        
        from ethos_os.models.portfolio import Portfolio
        from ethos_os.models.program import Program
        from ethos_os.models.project import Project
        
        portfolio = self.session.get(Portfolio, portfolio_uuid) if portfolio_uuid else None
        program = self.session.get(Program, program_uuid) if program_uuid else None
        project = self.session.get(Project, project_uuid) if project_uuid else None
        
        return {
            "sprint": sprint,
            "project": project,
            "program": program,
            "portfolio": portfolio,
        }
    
    def get_capacity_used(self, project_id: str) -> int:
        """Get total capacity used by active sprints in a project."""
        from sqlalchemy import func
        from ethos_os.models.task import Task
        
        active_sprints = self.list_by_project(project_id)
        active_sprint_ids = [s.id for s in active_sprints]
        
        if not active_sprint_ids:
            return 0
        
        stmt = select(func.sum(Task.effort_estimate_hours)).where(
            Task.sprint_id.in_(active_sprint_ids)
        )
        result = self.session.execute(stmt).scalar_one()
        return int(result or 0)
    
    def create(self, data: dict[str, Any]) -> Sprint:
        """Create a new sprint.
        
        D-45: Validates project.prd_status == 'approved'
        """
        from uuid import uuid4
        
        project_id = data.get("project_id")
        if not project_id:
            raise ValueError("project_id is required")
        
        # Verify project exists and is approved
        project = self.session.get(Project, project_id)
        if not project:
            raise KeyError(f"Project not found: {project_id}")
        
        if project.prd_status != ProjectStatus.APPROVED.value:
            raise ValueError(
                f"Cannot create sprint: project {project_id} PRD status is '{project.prd_status}', "
                f"must be '{ProjectStatus.APPROVED.value}'"
            )
        
        # Generate ID if not provided
        if "id" not in data:
            data["id"] = str(uuid4())
        
        # Compute path
        parent_path = project.path if project.path else ""
        data["path"] = compute_path(parent_path, data["id"])
        data["path_depth"] = 4
        data["parent_id"] = project_id
        
        # Set default status
        if "status" not in data:
            data["status"] = SprintStatus.PLANNING.value
        
        return super().create(data)