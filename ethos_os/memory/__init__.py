"""Memory package for EthosOS working memory."""

# Working memory
from ethos_os.memory.working import WorkingMemory, AgentContext


# Singleton accessor
_working_memory: WorkingMemory | None = None


def get_working_memory() -> WorkingMemory:
    """Get the singleton WorkingMemory instance."""
    global _working_memory
    if _working_memory is None:
        _working_memory = WorkingMemory()
    return _working_memory


__all__ = [
    "WorkingMemory",
    "AgentContext",
    "get_working_memory",
]