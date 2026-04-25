"""Program model - cross-program coordination unit."""

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ethos_os.models.base import Base, UUIDMixin, TimestampMixin, OwnerMixin, PathMixin


class Program(Base, UUIDMixin, TimestampMixin, OwnerMixin, PathMixin):
    """Program - a cross-program coordination unit.
    
    Programs group related projects.
    - Contains: Projects
    - path_depth: 2
    - Parent: Portfolio
    """
    
    __tablename__ = "programs"

    # Name
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Alignment statement
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # FK to Portfolio
    portfolio_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("portfolios.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Override path depth
    path_depth: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    
    def __repr__(self) -> str:
        return f"<Program(id={self.id}, name={self.name})>"


# NOTE: Relationship to Portfolio is defined in portfolio.py to avoid circular imports