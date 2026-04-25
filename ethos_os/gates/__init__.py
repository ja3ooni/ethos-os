"""Gates package for EthosOS approval gates."""

# Gate models
from ethos_os.models.gate import GateRequest, GateStatus, GateType

# Gate repositories
from ethos_os.repositories.gate import GateRepository

# Gate services
from ethos_os.gates.trigger import GateTriggerService, SCOPE_THRESHOLD, BUDGET_THRESHOLD
from ethos_os.gates.dashboard import GateDashboardService

# Audit
from ethos_os.models.audit import AuditLog, AuditEventType
from ethos_os.repositories.audit import AuditRepository


__all__ = [
    # Models
    "GateRequest",
    "GateStatus",
    "GateType",
    "AuditLog",
    "AuditEventType",
    # Repositories
    "GateRepository",
    "AuditRepository",
    # Services
    "GateTriggerService",
    "GateDashboardService",
    # Constants
    "SCOPE_THRESHOLD",
    "BUDGET_THRESHOLD",
]