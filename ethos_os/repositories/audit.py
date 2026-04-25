"""Audit repository - append-only audit log operations."""

import json
from datetime import datetime
from typing import Any, List

from sqlalchemy import select
from sqlalchemy.orm import Session

from ethos_os.models.audit import AuditEventType, AuditLog


class AuditRepository:
    """Repository for AuditLog operations (append-only)."""

    model_class = AuditLog

    def __init__(self, session: Session):
        self.session = session

    def _get_last_hash(self) -> str | None:
        """Get the hash of the most recent audit record."""
        stmt = select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(1)
        last = self.session.execute(stmt).scalars().first()
        return last.hash if last else None

    def _get_last_record(self) -> AuditLog | None:
        """Get the most recent audit record."""
        stmt = select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(1)
        return self.session.execute(stmt).scalars().first()

    def create(
        self,
        event_type: str,
        entity_id: str,
        entity_type: str,
        payload: dict[str, Any],
    ) -> AuditLog:
        """Create a new audit log entry (append-only)."""
        # Get hash of previous record
        previous_hash = self._get_last_hash()

        # Serialize payload
        payload_json = json.dumps(payload, default=str)

        # Get current timestamp
        now = datetime.now()

        # Compute hash
        hash_value = AuditLog.compute_hash(previous_hash, payload_json, now)

        data = {
            "event_type": event_type,
            "entity_id": entity_id,
            "entity_type": entity_type,
            "payload": payload_json,
            "previous_hash": previous_hash,
            "hash": hash_value,
            "timestamp": now,
        }

        instance = AuditLog(**data)
        self.session.add(instance)
        self.session.flush()
        self.session.refresh(instance)
        return instance

    def get(self, id: str) -> AuditLog | None:
        """Get an audit log entry by ID."""
        return self.session.get(AuditLog, id)

    def list(
        self,
        event_type: str | None = None,
        entity_id: str | None = None,
        entity_type: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int | None = None,
    ) -> List[AuditLog]:
        """List audit log entries with filters."""
        stmt = select(AuditLog).order_by(AuditLog.timestamp.desc())

        if event_type:
            stmt = stmt.where(AuditLog.event_type == event_type)
        if entity_id:
            stmt = stmt.where(AuditLog.entity_id == entity_id)
        if entity_type:
            stmt = stmt.where(AuditLog.entity_type == entity_type)
        if start_time:
            stmt = stmt.where(AuditLog.timestamp >= start_time)
        if end_time:
            stmt = stmt.where(AuditLog.timestamp <= end_time)

        if limit:
            stmt = stmt.limit(limit)

        return list(self.session.execute(stmt).scalars().all())

    def verify_integrity(self) -> tuple[bool, AuditLog | None]:
        """Verify integrity of the entire hash chain.
        
        Returns (is_valid, failed_record):
        - is_valid: True if all hashes are correct
        - failed_record: First record that failed verification (or None if valid)
        """
        stmt = select(AuditLog).order_by(AuditLog.timestamp.asc())
        records = list(self.session.execute(stmt).scalars().all())

        for record in records:
            if not record.verify_integrity():
                return False, record

        return True, None

    def verify_chain_from(self, start_id: str) -> bool:
        """Verify integrity chain starting from a specific record."""
        stmt = (
            select(AuditLog)
            .where(AuditLog.id >= start_id)
            .order_by(AuditLog.timestamp.asc())
        )
        records = list(self.session.execute(stmt).scalars().all())

        for record in records:
            if not record.verify_integrity():
                return False

        return True

    def get_entity_history(
        self, entity_id: str, event_type: str | None = None
    ) -> List[AuditLog]:
        """Get full audit history for an entity."""
        stmt = (
            select(AuditLog)
            .where(AuditLog.entity_id == entity_id)
            .order_by(AuditLog.timestamp.asc())
        )

        if event_type:
            stmt = stmt.where(AuditLog.event_type == event_type)

        return list(self.session.execute(stmt).scalars().all())

    def count_events(
        self,
        event_type: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> int:
        """Count audit events matching filters."""
        stmt = select(AuditLog)

        if event_type:
            stmt = stmt.where(AuditLog.event_type == event_type)
        if start_time:
            stmt = stmt.where(AuditLog.timestamp >= start_time)
        if end_time:
            stmt = stmt.where(AuditLog.timestamp <= end_time)

        return len(list(self.session.execute(stmt).scalars().all()))