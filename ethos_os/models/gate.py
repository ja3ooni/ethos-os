"""Gate models - approval gate system."""

import enum
import json
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column

from ethos_os.models.base import Base, UUIDMixin, TimestampMixin


class GateType(enum.Enum):
    """Type of approval gate."""

    SCOPE = "scope"  # Triggered on effort/scope variance
    BUDGET = "budget"  # Triggered on cost/budget variance


class GateStatus(enum.Enum):
    """Gate request status."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class GateRequest(Base, UUIDMixin, TimestampMixin):
    """Gate request - approval gate for scope/budget changes.
    
    Requirements:
    - GATE-01: Auto-created when scope exceeds +25% threshold
    - GATE-02: Auto-created when budget exceeds +20% threshold
    - GATE-03: Approver can accept or reject with notes
    - GATE-04: Task cannot proceed while pending
    - GATE-05: Rejected task blocked until re-planned
    - GATE-06: Records immutable (timestamp, approver, decision, notes)
    - GATE-07: Configurable timeout (default: 48h scope, 24h budget)
    - GATE-08: Dashboard displays pending gates with age and approver
    """

    __tablename__ = "gate_requests"

    # Gate type
    gate_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        doc="Type of gate: scope | budget"
    )

    # Entity being gated
    entity_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        index=True,
        doc="ID of entity this gate is for (task, project, etc.)"
    )

    entity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Type of entity (task, project, program, etc.)"
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=GateStatus.PENDING.value,
        index=True,
    )

    # Trigger condition (JSON - what caused the gate to trigger)
    trigger_condition: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="JSON describing what triggered this gate"
    )

    # Approver
    approver: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
        doc="Assigned approver user ID"
    )

    # Decision
    decision_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Notes from approver when deciding"
    )

    decided_by: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
        doc="User ID who approved or rejected"
    )

    # Timestamps
    decided_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When the gate was decided"
    )

    # Timeout in hours
    timeout_hours: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=48,
        doc="Timeout in hours before gate auto-expires"
    )

    @property
    def trigger_data(self) -> dict | None:
        """Parse trigger_condition JSON."""
        if not self.trigger_condition:
            return None
        return json.loads(self.trigger_condition)

    @property
    def is_pending(self) -> bool:
        """Check if gate is still pending."""
        return self.status == GateStatus.PENDING.value

    @property
    def is_expired(self) -> bool:
        """Check if gate has timed out."""
        if not self.created_at:
            return False
        from datetime import timedelta

        return datetime.now(self.created_at.tzinfo) > self.created_at + timedelta(hours=self.timeout_hours)

    @property
    def age_hours(self) -> float:
        """Get gate age in hours."""
        if not self.created_at:
            return 0.0
        delta = datetime.now(self.created_at.tzinfo) - self.created_at
        return delta.total_seconds() / 3600

    def __repr__(self) -> str:
        return f"<GateRequest(id={self.id}, type={self.gate_type}, status={self.status})>"