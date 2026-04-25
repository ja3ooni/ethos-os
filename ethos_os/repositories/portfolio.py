"""Portfolio repository."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from ethos_os.models.portfolio import Portfolio
from ethos_os.repositories.base import BaseRepository


class PortfolioRepository(BaseRepository[Portfolio]):
    """Repository for Portfolio entity."""
    
    model_class = Portfolio
    
    def get_by_name(self, name: str) -> Portfolio | None:
        """Get portfolio by name."""
        stmt = select(Portfolio).where(Portfolio.name == name)
        return self.session.execute(stmt).scalar_one_or_none()
    
    def list_by_owner(self, owner_id: str) -> list[Portfolio]:
        """List portfolios by owner."""
        stmt = select(Portfolio).where(Portfolio.owner_id == owner_id)
        return list(self.session.execute(stmt).scalars().all())
    
    def create(self, data: dict[str, Any]) -> Portfolio:
        """Create a new portfolio.
        
        Sets path_depth=1 and computes path.
        """
        # Generate ID if not provided
        if "id" not in data:
            from uuid import uuid4
            data["id"] = str(uuid4())
        
        # Set path and depth for root entity
        data["path"] = f"/{data['id']}/"
        data["path_depth"] = 1
        data["parent_id"] = None
        
        return super().create(data)