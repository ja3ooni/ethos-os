"""Program repository."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from ethos_os.models.base import compute_path
from ethos_os.models.program import Program
from ethos_os.models.portfolio import Portfolio
from ethos_os.repositories.base import BaseRepository


class ProgramRepository(BaseRepository[Program]):
    """Repository for Program entity."""
    
    model_class = Program
    
    def list_by_portfolio(self, portfolio_id: str) -> list[Program]:
        """List programs by portfolio."""
        stmt = select(Program).where(Program.portfolio_id == portfolio_id)
        return list(self.session.execute(stmt).scalars().all())
    
    def get_by_name_and_portfolio(self, name: str, portfolio_id: str) -> Program | None:
        """Get program by name within a portfolio."""
        stmt = select(Program).where(
            Program.name == name,
            Program.portfolio_id == portfolio_id
        )
        return self.session.execute(stmt).scalar_one_or_none()
    
    def get_lineage(self, program_id: str) -> list[Portfolio]:
        """Get lineage to portfolio (O(1) via path split.
        
        Returns [Portfolio]
        """
        program = self.get_or_404(program_id)
        
        # Split path to get segment IDs
        if not program.path:
            return []
        
        # Path format: /portfolio_id/program_id/
        segments = program.path.strip("/").split("/")
        portfolio_uuid = segments[0] if segments else None
        
        if portfolio_uuid:
            from ethos_os.models.portfolio import Portfolio
            portfolio = self.session.get(Portfolio, portfolio_uuid)
            return [portfolio] if portfolio else []
        return []
    
    def create(self, data: dict[str, Any]) -> Program:
        """Create a new program.
        
        Validates portfolio_id exists, sets path_depth=2, computes path.
        """
        from uuid import uuid4
        
        portfolio_id = data.get("portfolio_id")
        if not portfolio_id:
            raise ValueError("portfolio_id is required")
        
        # Verify portfolio exists
        from ethos_os.models.portfolio import Portfolio
        portfolio = self.session.get(Portfolio, portfolio_id)
        if not portfolio:
            raise KeyError(f"Portfolio not found: {portfolio_id}")
        
        # Generate ID if not provided
        if "id" not in data:
            data["id"] = str(uuid4())
        
        # Compute path: parent's path + this ID + /
        parent_path = portfolio.path if portfolio.path else ""
        data["path"] = compute_path(parent_path, data["id"])
        data["path_depth"] = 2
        data["parent_id"] = portfolio_id
        
        return super().create(data)