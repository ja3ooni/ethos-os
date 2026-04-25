"""Models package for EthosOS domain entities."""

# Re-export Base for table creation
from ethos_os.db import Base

# Base mixins
from ethos_os.models.base import (
    UUIDMixin,
    TimestampMixin,
    OwnerMixin,
    PathMixin,
    compute_path,
    get_lineage_from_path,
)

# Portfolio
from ethos_os.models.portfolio import Portfolio

# Program
from ethos_os.models.program import Program

# Project
from ethos_os.models.project import Project, ProjectStatus

# Sprint
from ethos_os.models.sprint import Sprint, SprintStatus

# Task
from ethos_os.models.task import Task, TaskStatus

# PRD
from ethos_os.models.prd import PRD, PRDStatus

# Gate
from ethos_os.models.gate import GateRequest, GateStatus, GateType

# Audit
from ethos_os.models.audit import AuditLog, AuditEventType


__all__ = [
    # Base
    "Base",
    "UUIDMixin",
    "TimestampMixin",
    "OwnerMixin",
    "PathMixin",
    "compute_path",
    "get_lineage_from_path",
    # Entities
    "Portfolio",
    "Program",
    "Project",
    "ProjectStatus",
    "Sprint",
    "SprintStatus",
    "Task",
    "TaskStatus",
    "PRD",
    "PRDStatus",
    # Gates
    "GateRequest",
    "GateStatus",
    "GateType",
    # Audit
    "AuditLog",
    "AuditEventType",
]