"""Project repository."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from ethos_os.models.base import compute_path
from ethos_os.models.project import Project, ProjectStatus
from ethos_os.repositories.base import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    """Repository for Project entity."""
    
    model_class = Project
    
    def list_by_program(self, program_id: str) -> list[Project]:
        """List projects by program."""
        stmt = select(Project).where(Project.program_id == program_id)
        return list(self.session.execute(stmt).scalars().all())
    
    def list_by_status(self, status: str) -> list[Project]:
        """List projects by status."""
        stmt = select(Project).where(Project.prd_status == status)
        return list(self.session.execute(stmt).scalars().all())
    
    def list_approved(self) -> list[Project]:
        """List projects with approved PRD."""
        return self.list_by_status(ProjectStatus.APPROVED.value)
    
    def search_by_name(self, query: str) -> list[Project]:
        """Search projects by name (LIKE)."""
        stmt = select(Project).where(Project.name.like(f"%{query}%"))
        return list(self.session.execute(stmt).scalars().all())
    
    def get_with_lineage(self, project_id: str) -> dict:
        """Get project with full lineage.
        
        Returns {project, program, portfolio}
        """
        project = self.get_or_404(project_id)
        
        # Parse path segments
        if not project.path:
            return {"project": project, "program": None, "portfolio": None}
        
        segments = project.path.strip("/").split("/")
        
        # segments: [portfolio_id, program_id, project_id]
        portfolio_uuid = segments[0] if len(segments) > 0 else None
        program_uuid = segments[1] if len(segments) > 1 else None
        
        from ethos_os.models.portfolio import Portfolio
        from ethos_os.models.program import Program
        
        portfolio = (
            self.session.get(Portfolio, portfolio_uuid) 
            if portfolio_uuid else None
        )
        program = (
            self.session.get(Program, program_uuid) 
            if program_uuid else None
        )
        
        return {
            "project": project,
            "program": program,
            "portfolio": portfolio,
        }
    
    def create(self, data: dict[str, Any]) -> Project:
        """Create a new project.
        
        Validates program_id exists, sets path_depth=3, computes path.
        """
        from uuid import uuid4
        
        program_id = data.get("program_id")
        if not program_id:
            raise ValueError("program_id is required")
        
        # Verify program exists
        from ethos_os.models.program import Program
        program = self.session.get(Program, program_id)
        if not program:
            raise KeyError(f"Program not found: {program_id}")
        
        # Generate ID if not provided
        if "id" not in data:
            data["id"] = str(uuid4())
        
        # Compute path
        parent_path = program.path if program.path else ""
        data["path"] = compute_path(parent_path, data["id"])
        data["path_depth"] = 3
        data["parent_id"] = program_id
        
        # Set default status if not provided
        if "prd_status" not in data:
            data["prd_status"] = ProjectStatus.DRAFT.value
        
        return super().create(data)
    
    def approve(self, project_id: str) -> Project:
        """Approve a project's PRD."""
        return self.update(project_id, {"prd_status": ProjectStatus.APPROVED.value})
    
    def update_path(
        self,
        entity: Project,
        new_parent_id: str,
    ) -> Project:
        """Update entity path and all descendant paths.
        
        D-07: Moving an entity requires path migration for all descendants.
        """
        from uuid import uuid4
        
        # Get new parent path
        from ethos_os.models.program import Program
        new_parent = self.session.get(Program, new_parent_id)
        if not new_parent:
            raise KeyError(f"Program not found: {new_parent_id}")
        
        # Generate new ID and path
        new_id = str(uuid4())
        new_path = compute_path(new_parent.path, new_id)
        
        # Update this entity
        entity.id = new_id
        entity.path = new_path
        entity.parent_id = new_parent_id
        entity.program_id = new_parent_id
        
        self.session.flush()
        
        # Update all descendants (child projects)
        child_projects = self.list_by_program(entity.program_id)
        for child in child_projects:
            if child.path.startswith(new_path):
                # Recursively update path prefix
                old_prefix = f"/{entity.id}/{child.id}/" if entity.id == child.parent_id else ""
                if old_prefix:
                    child.path = child.path.replace(old_prefix, "", 1)
                child.path = f"{new_path}{child.id}/"
        
        self.session.flush()
        self._refresh(entity)
        return entity