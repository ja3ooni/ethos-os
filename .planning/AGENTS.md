# EthosOS Agent Configuration

Maps GSD phases/tasks to your available Agency Agents.

| Role | Agent | Use For |
|------|-------|---------|
| Implementation | @senior-developer | Writing domain models, repositories, CRUD |
| Architecture | @backend-architect | System design decisions |
| Code Review | @code-reviewer | PR/commit reviews |
| Security | @security-engineer | Auth, permissions, audit |
| Data | @data-engineer | Qdrant integration, vector storage |
| API | @frontend-developer | API layer (if REST) |

## Per-Plan Agent Assignments

### Phase 1: Domain Models

| Plan | Tasks | Agent |
|------|-------|-------|
| 01-01 | Project scaffolding | @senior-developer |
| 01-02 | Initiative models | @senior-developer |
| 01-03 | CRUD operations | @senior-developer |
| 01-04 | Working memory | @senior-developer |
| 01-05 | Migration + seed | @senior-developer |

### Phase 2: Memory + Gates

| Plan | Tasks | Agent |
|------|-------|-------|
| 02-01 | SQLite repositories | @data-engineer |
| 02-02 | Qdrant integration | @data-engineer |
| 02-03 | PRD gates | @security-engineer |
| 02-04 | Audit trail | @security-engineer |

### Phase 3: Heartbeat Execution

| Plan | Tasks | Agent |
|------|-------|-------|
| 03-01 | Agent registry | @backend-architect |
| 03-02 | Heartbeat scheduler | @backend-architect |
| 03-03 | Task queue | @backend-architect |
| 03-04 | Execution engine | @backend-architect |

### Phase 4: API Layer

| Plan | Tasks | Agent |
|------|-------|-------|
| 04-01 | REST API | @frontend-developer |
| 04-02 | Auth & permissions | @security-engineer |
| 04-03 | WebSocket | @frontend-developer |
| 04-04 | Rate limiting | @security-engineer |

### Phase 5: Dashboard

| Plan | Tasks | Agent |
|------|-------|-------|
| 05-01 | UI components | @ui-designer |
| 05-02 | Dashboard views | @frontend-developer |
| 05-03 | Charts | @analytics-reporter |
| 05-04 | Real-time updates | @frontend-developer |

### Phase 6: Testing

| Plan | Tasks | Agent |
|------|-------|-------|
| 06-01 | Unit tests | @model-qa-specialist |
| 06-02 | Integration tests | @model-qa-specialist |
| 06-03 | E2E tests | @model-qa-specialist |
| 06-04 | Load testing | @model-qa-specialist |

## Usage in GSD

To invoke an agent for implementation:

```
/gsd-execute-phase 1 --agent @senior-developer
```

Or in prompts, reference directly:
- "Use @senior-developer to implement the initiative models in ethos_os/models/"