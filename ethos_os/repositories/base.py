"""Base repository with common CRUD operations."""

from typing import Any, Generic, TypeVar
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from ethos_os.db import Base
from ethos_os.models.base import compute_path

# Generic model type
ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Base repository with common CRUD operations.
    
    Subclasses should define:
    - model_class: The SQLAlchemy model class
    """
    
    model_class: type[ModelType]
    
    def __init__(self, session: Session):
        self.session = session
    
    def _commit(self) -> None:
        """Commit the session."""
        self.session.commit()
    
    def _rollback(self) -> None:
        """Rollback the session."""
        self.session.rollback()
    
    def _refresh(self, instance: ModelType) -> None:
        """Refresh an instance from the database."""
        self.session.refresh(instance)
    
    def create(self, data: dict[str, Any]) -> ModelType:
        """Create a new instance."""
        instance = self.model_class(**data)
        self.session.add(instance)
        self.session.flush()
        self._refresh(instance)
        return instance
    
    def get(self, id: str) -> ModelType | None:
        """Get an instance by ID."""
        return self.session.get(self.model_class, id)
    
    def get_or_404(self, id: str) -> ModelType:
        """Get an instance by ID or raise 404."""
        instance = self.session.get(self.model_class, id)
        if instance is None:
            raise KeyError(f"{self.model_class.__name__} not found: {id}")
        return instance
    
    def exists(self, id: str) -> bool:
        """Check if an instance exists."""
        return self.get(id) is not None
    
    def list(
        self,
        filters: dict[str, Any] | None = None,
        order_by: str | None = None,
        limit: int | None = None,
    ) -> list[ModelType]:
        """List instances with optional filters."""
        stmt = select(self.model_class)
        
        if filters:
            for key, value in filters.items():
                if hasattr(self.model_class, key):
                    stmt = stmt.where(getattr(self.model_class, key) == value)
        
        if order_by and hasattr(self.model_class, order_by):
            stmt = stmt.order_by(getattr(self.model_class, order_by))
        
        if limit:
            stmt = stmt.limit(limit)
        
        return list(self.session.execute(stmt).scalars().all())
    
    def update(self, id: str, data: dict[str, Any]) -> ModelType:
        """Update an instance."""
        instance = self.get_or_404(id)
        for key, value in data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        self.session.flush()
        self._refresh(instance)
        return instance
    
    def delete(self, id: str) -> bool:
        """Delete an instance."""
        instance = self.get(id)
        if instance is None:
            return False
        self.session.delete(instance)
        self.session.flush()
        return True
    
    def count(self, filters: dict[str, Any] | None = None) -> int:
        """Count instances."""
        stmt = select(self.model_class)
        
        if filters:
            for key, value in filters.items():
                if hasattr(self.model_class, key):
                    stmt = stmt.where(getattr(self.model_class, key) == value)
        
        return len(list(self.session.execute(stmt).scalars().all()))