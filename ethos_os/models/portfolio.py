"""Portfolio model - apex of initiative hierarchy."""

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ethos_os.models.base import Base, UUIDMixin, TimestampMixin, OwnerMixin, PathMixin


class Portfolio(Base, UUIDMixin, TimestampMixin, OwnerMixin, PathMixin):
    """Portfolio - the apex of initiative hierarchy.
    
    A portfolio represents the company or strategic entity.
    - Contains: Programs (product lines, business units)
    - path_depth: 1
    - No parent (root entity)
    """
    
    __tablename__ = "portfolios"

    # Name
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Strategic intent - why this portfolio exists
    strategic_intent: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Override path to set default
    path: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    path_depth: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    
    def __repr__(self) -> str:
        return f"<Portfolio(id={self.id}, name={self.name})>"