# Features Research: EthosOS

**Domain:** Initiative-based OS for human-agent organizations
**Date:** 2026-04-24
**Dimension:** Features

## Question

What features do initiative-based OS products have? What's table stakes vs differentiating?

## Feature Taxonomy

### Table Stakes (Must Have)

These are baseline expectations. Without them, users will not adopt.

#### Initiative Hierarchy
- Portfolio → program → project → workstream → sprint → backlog → task → subtask structure
- Each level has: name, owner, status, timeline, initiative root
- Initiative root: stated intent + success metric + boundaries
- Full lineage inheritance (task knows its portfolio)
- Nesting and reordering at any level

#### Approval Gates
- Human-in-the-loop checkpoints before work proceeds
- Scope gate: triggered when task exceeds estimate threshold
- Budget gate: triggered when spend exceeds estimate
- Binary approval: approve or reject (with notes)
- Gate records: immutable, timestamped, with approver identity

#### Heartbeat Execution
- Agents poll on configurable interval
- Heartbeat records: timestamp, agent ID, status, task ID, progress note
- Execution within initiative bounds (no unbounded autonomy)
- Human can view heartbeat timeline per agent

#### Memory System
- Working memory: runtime state per agent session
- Structured memory: persistent entities and relationships
- Query by exact key (not similarity) for state queries

#### Dashboard
- Initiative tree visualization (portfolio → subtask)
- Gate status board (pending approvals)
- Heartbeat timeline (agent activity)
- Basic search (by name, owner, status)

### Differentiators (Competitive Advantage)

These separate EthosOS from generic PM tools.

#### Semantic Recall
- Vector embeddings of initiative roots, scope change descriptions
- "Show me similar scope change requests" — ranked by semantic similarity
- Exact state queries remain SQL; related concepts use vector

#### Cost Awareness
- Per-work-item estimated vs actual cost
- Variance flagging (>20% auto-triggers exception review)
- Daily cost aggregation per program/project
- Cost context at every initiative level

#### Auditability
- Immutable episodic event log
- Hash-chain integrity (no edits or deletes)
- Full trace: who approved what, when, under what conditions
- Compliance-ready without being a compliance tool

#### Human Governance Without Process Overhead
- Gates are structural, not procedural
- Hierarchy enforces governance — no checkbox compliance
- Humans approve at boundaries, not micromanage execution
- Agents report via heartbeat; humans review, approve, course-correct

### Anti-Features (Deliberately NOT Built)

These are explicit no-gos for EthosOS.

- **Ticket-based work**: Tickets imply adversarial assignees and status theater
- **Event-driven execution**: Event ordering becomes fragile under load
- **Agent-first autonomy**: Unbounded agent execution is governance failure
- **Vector as source of truth**: Semantic recall ≠ exact state
- **Process as governance**: Governance lives in hierarchy, not process docs
- **Real-time everything**: 30s heartbeat is intentional — balance between responsiveness and noise

## Feature Dependencies

```
Initiative Hierarchy
    ├── Approval Gates (depends on hierarchy levels)
    │   ├── Scope Gate (depends on task estimates)
    │   └── Budget Gate (depends on cost tracking)
    ├── Heartbeat Execution (depends on task assignment)
    │   └── Memory System (depends on everything)
    │       ├── Working Memory (runtime only)
    │       ├── Structured Memory (persistent)
    │       │   └── Semantic Recall (vector, deferred v0.2)
    │       └── Episodic Memory (audit log, deferred v0.2)
    └── Dashboard (depends on all above)
```

## MVP Feature Scope

From EthosOS PRD v0.1:

**In MVP:**
- Initiative hierarchy (portfolio → workstream)
- Initiative root at project level
- Scope + budget approval gates
- Heartbeat execution (30s interval, single agent)
- Working + structured memory
- Immutable audit log (episodic foundation)
- SQLite persistence
- REST API for work items
- Read-only dashboard

**Not in MVP:**
- Staffing, launch, exception gates
- Semantic memory population
- Cost dashboards
- Multi-agent coordination
- Mobile UI
- External API-first design
- Distributed deployment

## Complexity Notes

- **Initiative hierarchy**: Medium complexity — recursive model, deep nesting, lineage inheritance
- **Approval gates**: Low complexity — state machine, human approval webhook
- **Heartbeat execution**: Low complexity — scheduled loop, stateless per-beat
- **Memory tiers**: Medium complexity — working (in-memory dict), structured (SQLAlchemy/SQLite)
- **Vector semantic**: Low complexity at v0.2 — pgvector or Qdrant integration

## Confidence

- Table stakes: **High** — well-established in PM tooling domain
- Semantic recall differentiator: **Medium** — novel combination, proven technologies
- Anti-features: **High** — deliberate design decisions rooted in philosophy