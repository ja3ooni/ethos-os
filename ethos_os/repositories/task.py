"""Task repository."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from ethos_os.models.base import compute_path
from ethos_os.models.project import Project, ProjectStatus
from ethos_os.models.sprint import Sprint
from ethos_os.models.task import Task, TaskStatus
from ethos_os.repositories.base import BaseRepository


class TaskRepository(BaseRepository[Task]):
    """Repository for Task entity."""
    
    model_class = Task
    
    def list_by_sprint(self, sprint_id: str) -> list[Task]:
        """List tasks by sprint."""
        stmt = select(Task).where(Task.sprint_id == sprint_id)
        return list(self.session.execute(stmt).scalars().all())
    
    def list_by_assignee(self, assignee_id: str) -> list[Task]:
        """List tasks by assignee."""
        stmt = select(Task).where(Task.assignee_id == assignee_id)
        return list(self.session.execute(stmt).scalars().all())
    
    def list_by_status(self, status: str) -> list[Task]:
        """List tasks by status."""
        stmt = select(Task).where(Task.status == status)
        return list(self.session.execute(stmt).scalars().all())
    
    def get_by_prd_scope(self, prd_scope_item_id: str) -> list[Task]:
        """Get tasks by PRD scope item reference."""
        stmt = select(Task).where(Task.prd_scope_item_id == prd_scope_item_id)
        return list(self.session.execute(stmt).scalars().all())
    
    def get_lineage(self, task_id: str) -> dict:
        """Get task with full lineage.
        
        Returns {task, sprint, project, program, portfolio}
        """
        task = self.get_or_404(task_id)
        
        if not task.path:
            return {
                "task": task,
                "sprint": None,
                "project": None,
                "program": None,
                "portfolio": None,
            }
        
        segments = task.path.strip("/").split("/")
        
        # segments: [portfolio_id, program_id, project_id, sprint_id, task_id]
        portfolio_uuid = segments[0] if len(segments) > 0 else None
        program_uuid = segments[1] if len(segments) > 1 else None
        project_uuid = segments[2] if len(segments) > 2 else None
        sprint_uuid = segments[3] if len(segments) > 3 else None
        
        from ethos_os.models.portfolio import Portfolio
        from ethos_os.models.program import Program
        from ethos_os.models.project import Project
        from ethos_os.models.sprint import Sprint
        
        return {
            "task": task,
            "sprint": self.session.get(Sprint, sprint_uuid) if sprint_uuid else None,
            "project": self.session.get(Project, project_uuid) if project_uuid else None,
            "program": self.session.get(Program, program_uuid) if program_uuid else None,
            "portfolio": self.session.get(Portfolio, portfolio_uuid) if portfolio_uuid else None,
        }
    
    def create(self, data: dict[str, Any]) -> Task:
        """Create a new task.
        
        D-44: Validates prd_scope_item_id is not null
        """
        from uuid import uuid4
        
        sprint_id = data.get("sprint_id")
        if not sprint_id:
            raise ValueError("sprint_id is required")
        
        # Verify sprint exists
        sprint = self.session.get(Sprint, sprint_id)
        if not sprint:
            raise KeyError(f"Sprint not found: {sprint_id}")
        
        # D-44: Validate prd_scope_item_id is not null
        prd_scope_item_id = data.get("prd_scope_item_id")
        if not prd_scope_item_id:
            raise ValueError(
                "prd_scope_item_id is required - every task must trace to PRD scope"
            )
        
        # Generate ID if not provided
        if "id" not in data:
            data["id"] = str(uuid4())
        
        # Compute path
        parent_path = sprint.path if sprint.path else ""
        data["path"] = compute_path(parent_path, data["id"])
        data["path_depth"] = 5
        data["parent_id"] = sprint_id
        
        # Set default status
        if "status" not in data:
            data["status"] = TaskStatus.TODO.value
        
        return super().create(data)
    
    def move_to_sprint(
        self,
        task_id: str,
        new_sprint_id: str,
    ) -> Task:
        """Move task to a new sprint.
        
        D-07: Updates task + all subtask paths
        """
        from uuid import uuid4
        
        task = self.get_or_404(task_id)
        new_sprint = self.session.get(Sprint, new_sprint_id)
        
        if not new_sprint:
            raise KeyError(f"Sprint not found: {new_sprint_id}")
        
        # Generate new ID and path
        new_id = str(uuid4())
        new_path = compute_path(new_sprint.path, new_id)
        
        # Update task
        task.id = new_id
        task.path = new_path
        task.sprint_id = new_sprint_id
        task.parent_id = new_sprint_id
        
        self.session.flush()
        self._refresh(task)
        return task