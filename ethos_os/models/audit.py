"""Audit log model - immutable episodic event log."""

import enum
import hashlib
import json
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Index, Integer, String, Text
from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column

from ethos_os.models.base import Base, UUIDMixin


class AuditEventType(enum.Enum):
    """Types of audit events."""

    HEARTBEAT = "heartbeat"
    GATE_DECISION = "gate_decision"
    COST_SNAPSHOT = "cost_snapshot"
    SCOPE_CHANGE = "scope_change"
    BUDGET_CHANGE = "budget_change"
    TASK_CREATED = "task_created"
    TASK_COMPLETED = "task_completed"
    TASK_BLOCKED = "task_blocked"
    TASK_UNBLOCKED = "task_unblocked"


class AuditLog(Base, UUIDMixin):
    """Audit log - immutable episodic event log.
    
    Requirements:
    - MEM-05: Episodic memory stores immutable event log
    - MEM-06: Episodic log uses hash-chain integrity
    - GATE-06: Gate records are immutable
    
    Hash chain:
    - Each record contains hash of (previous_hash + payload + timestamp)
    - First record has null previous_hash
    - Enables tamper detection
    """

    __tablename__ = "audit_log"

    # Event type
    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    # Entity
    entity_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        index=True,
    )

    entity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    # Payload (JSON)
    payload: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="JSON payload for the event"
    )

    # Hash chain
    previous_hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        doc="Hash of previous record"
    )

    hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        doc="SHA-256 hash of this record"
    )

    # Timestamp
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    @property
    def payload_data(self) -> dict[str, Any]:
        """Parse payload JSON."""
        return json.loads(self.payload)

    @staticmethod
    def compute_hash(previous_hash: str | None, payload: str, timestamp: datetime) -> str:
        """Compute SHA-256 hash for a record."""
        data = f"{previous_hash or ''}{payload}{timestamp.isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()

    def verify_integrity(self) -> bool:
        """Verify this record's hash is correct."""
        expected = self.compute_hash(
            self.previous_hash,
            self.payload,
            self.timestamp,
        )
        return self.hash == expected

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, type={self.event_type}, entity_id={self.entity_id})>"