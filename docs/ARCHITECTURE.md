# EthosOS Architecture Brief

**Version:** 0.1 (MVP)  
**Date:** 2026-04-24  
**Author:** Software Architect

---

## 1. System Overview

EthosOS is an open-source operating system for human-agent organizations. It replaces ticket-based work management with project-first PMO-style coordination modeled after how companies actually run: a company is a portfolio, a product launch is a project, a hiring sprint comes from a project, backlog items come from PRDs — not tickets.

### What EthosOS Is

- **A PMO coordination layer** between human leadership and agent execution
- **A project hierarchy** from company down to subtask, modeled after real organizational structure
- **A governance engine** with human-in-the-loop approval gates that mirror board/PMO approval workflows
- **A memory system** with vector-based long-term recall for token efficiency and layered memory for short-term ops
- **An open-source project** with practical implementation over theoretical purity

### What EthosOS Is Not

- **Not a ticketing system** — tickets imply problems without SLA; EthosOS models work as projects with outcomes, PRDs with board approval, sprints derived from goals
- **Not a pure AI system** — humans approve scope, budget, staffing, launch; agents execute within bounds
- **Not a bloated PMO tool** — EthosOS runs lean, no overthinking, no checkbox theater
- **Not a compliance tool** — governance is structural, not procedural

### Design Philosophy

> Reject complexity unless scale requires it.

Every component must justify its existence. If it doesn't serve initiative coordination, human-agent handoff, or governance, it's deferred to v0.2+.

---

## 2. Core Domain Model

The hierarchy is intentional: portfolio → program → project → workstream → sprint → backlog → task → subtask.

### Why This Hierarchy

| Level | Purpose | Human Role | Agent Role |
|-------|--------|-----------|-----------|
| Portfolio | The company or strategic entity | Board-level approval | None |
| Program | Cross-project coordination unit | Approve resources | None |
| Project | A deliverable with a PRD and board-approved scope | Approve scope/budget/launch | Execute |
| Sprint | Time-boxed iteration within a project | Approve exceptions | Execute |
| Backlog | Prioritized work derived from the PRD | Prioritize | Recommend |
| Task | Atomic unit of work | Review | Execute |
| Subtask | Implementation detail | None | Execute autonomously |

**How work actually flows:**
1. A project is created with a PRD (Product Requirements Document)
2. Board/PMO approves the PRD scope at intake
3. Sprint planning derives tasks from the approved PRD
4. Backlog items are prioritized work from the PRD, not tickets
5. Kanban boards visualize sprint state — derived from project, not ticket chaos
6. No tickets exist unless they map to a PRD item with board-approved scope

### No Tickets

Tickets imply problems to be solved without SLA. EthosOS uses work derived from PRDs with board approval. Every task traces to a project with an approved PRD. No orphan tickets. No "create a ticket" as primitive.

### Deferred (v0.2+)

- Program-level dependencies and cross-project resource sharing
- Automated staffing optimization
- Portfolio-level forecasting

---

## 3. Memory Architecture

Five layers, each with distinct retrieval semantics. Vector-first for token efficiency — big chunks go to vector store, not context windows.

### Layer Model

| Layer | Type | Storage | Retrieval | Purpose |
|-------|------|---------|-----------|---------|
| Semantic | Long-term memory | Vector store (Qdrant/local) | Similarity search | Large context: PRD chunks, docs, meeting notes, decision rationale |
| Procedural | Instructions | Vector store + templates | Rule match | How to file variance, approval workflows, escalation paths |
| Episodic | Event log | Append-only log | Time-range query | What happened and when |
| Structured | Relational facts | SQLite/PostgreSQL | Exact key lookup | Entities, relationships, gate states |
| Working | Operational state | In-memory | Direct reference | Current sprint, active tasks, runtime context |

### Retrieval Semantics

**Key principle: Vector is primary for big context — PRD chunks, architecture docs, meeting notes never hit context limits.**

- Semantic memory is the **primary long-term memory** — large context chunks stored as embeddings. PRD content, architecture docs, meeting notes, decision rationale. Never bloat context windows.
- Structured memory holds **authoritative state only** — current sprint status, gate states, cost records. Small, exact, fast SQL queries.
- Episodic memory is **append-only audit** — immutable log of what happened.
- Procedural memory stores **instructional patterns** — how to file a variance request, approval workflows.
- Working memory is **runtime only** — per-agent in-flight context, not persisted.

### Deferred (v0.2+)

- Cross-instance episodic replay
- Semantic memory versioning and fact-checking
- Procedural memory learning from human corrections

---

## 4. Agent Execution Model

Agents run on heartbeat-based execution cycles. Not event-driven (fragile under load), not cron-based (insufficient responsiveness). Heartbeat is a middle ground.

### Heartbeat Mechanics

```
For each agent:
  Every N seconds:
    1. Check assigned work items (Structured memory)
    2. Check approval status (Governance layer)
    3. Execute eligible items
    4. Update working memory
    5. Write episodic log
    6. Report completion/failure
```

- **N = 30 seconds** (configurable per agent type)
- Heartbeat is a lease, not a lock — if agent dies, work reassigns after missed heartbeats

### Human Gates

Four gates, each must pass before work proceeds:

| Gate | Trigger | Approver | Timeout |
|------|---------|----------|---------|
| Scope | New/changed work item | Project lead | 48h |
| Budget | Resource commitment | Finance | 24h |
| Staffing | Agent assignment | Program lead | 24h |
| Launch | Project/program go-live | Portfolio lead | 72h |
| Exception | Override of standard | Varies | 24h |

Gate is **binary**: approved or not. No partial approval.

### Deferred (v0.2+)

- Parallel execution with dependency resolution
- Agent-to-agent negotiation
- Automated exception flagging based on cost/schedule delta

---

## 5. Governance Layer

Governance is structural, not procedural. The hierarchy itself enforces approval gates. No checkbox compliance — if the hierarchy exists, gates are applied.

### Auditability

Every approval gate creates an **immutable record**:

- Who approved
- When
- What was approved (exact scope/budget/resource)
- Conditions (if any)

Records are stored in **Episodic layer** with cryptographic integrity (append-only hash chain).

### Cost Awareness

Every work item carries:

- Estimated cost (at assignment)
- Actual cost (at completion)
- Variance flagging (>20% triggers exception review)

Costs are tracked at agent-hour level, not micro-transaction. Daily aggregation is sufficient for MVP.

### Deferred (v0.2+)

- Real-time cost dashboards
- Automated budget reallocation proposals
- Compliance reporting for external regulations (SOC 2, etc.)

---

## 6. Module Boundaries

```
ethos-os/
├── domain/              # Core business logic
│   ├── portfolio/      # Company/strategic entity model
│   ├── program/        # Cross-project coordination
│   ├── project/        # PRD-backed deliverable with board approval
│   ├── sprint/         # Time-boxed iteration
│   ├── backlog/        # Prioritized work from PRD
│   ├── task/           # Atomic work unit
│   └── prd/           # Product Requirements Document model
├── memory/             # All memory layers
│   ├── semantic/       # Vector store (primary long-term)
│   ├── procedural/     # Instruction patterns (vector-backed)
│   ├── episodic/       # Event log (append-only)
│   ├── structured/    # Database (exact state)
│   └── working/       # In-memory (runtime)
├── execution/          # Agent runtime
│   ├── heartbeat/     # Heartbeat scheduler
│   ├── executor/      # Work item execution
│   └── gates/         # Gate checking
├── governance/         # Governance enforcement
│   ├── approvals/     # Board/PMO approval workflow
│   ├── intake/        # PRD intake and scope approval
│   ├── audit/         # Immutable record
│   └── cost/          # Cost tracking
└── infrastructure/    # Platform concerns
    ├── persistence/   # DB abstraction
    ├── vector/        # Vector store adapter
    ├── messaging/     # Agent communication
    └── config/        # Configuration
```

### Intake Phase (PRD Workflow)

Before any project has sprints or backlog:

1. **PRD Created** — Product Requirements Document drafted (intent, success metric, scope, boundaries, timeline)
2. **Board/PMO Review** — Human board reviews PRD scope
3. **Scope Approved** — Board approves scope, budget, timeline → gate opens
4. **Project Activated** — With approved PRD, project can spawn sprints
5. **Sprint Planning** — Tasks derived from approved PRD, not orphan tickets

This mirrors real PMO workflows. No sprints without board-approved scope. No backlog without PRD.

### Coupling Rules

- **domain** has no dependencies on other modules
- **memory** is accessed through interfaces (no direct DB in domain)
- **execution** depends on domain + memory + governance
- **governance** depends on domain + memory
- **infrastructure** is swapped for deployment context

### Deferred (v0.2+)

- Distributed execution (multiple agent pools)
- Multi-tenant isolation
- Plugin system for custom work item types

---

## 7. Technology Choices

### Rationale: Open-Source, Minimal Dependency

| Component | Choice | Justification |
|-----------|--------|--------------|
| Core language | Python 3.11+ | Ecosystem, readability, agent-native |
| API layer | FastAPI | Open-source, minimal, async-native |
| Database | SQLite (MVP), PostgreSQL (scale) | No vendor lock-in, relational |
| **Vector store** | **Qdrant (primary memory)** | **Open-source, primary storage for big context chunks** |
| Message broker | Redis (Pub/Sub) or in-memory | Simple for MVP, scales |
| Config | YAML + environment | No proprietary config format |
| Logging | Structured JSON to stdout | Container-native, tool-agnostic |

**Vector store is primary, not optional.** Large PRD chunks, architecture docs, meeting notes, and decision rationale all go into Qdrant. This is the token-efficiency play — big context never hits the model context window.

### Why Not X

- **Why not event-driven?** Under load, event ordering becomes fragile. Heartbeat is simpler to debug and scales predictably.
- **Why not graph database?** Relational model matches hierarchy. Graph is deferred unless cross-project dependencies emerge.
- **Why not microservices?** MVP is a single deployment. Decompose only when team size demands it.
- **Why not blockchain for audit?** Append-only log with hash chain provides integrity without crypto overhead. Defer to v0.2+ if regulatory requirement.

### Infrastructure for Deployment

- **Development:** Docker Compose with local services
- **Production:** Any container orchestrator (Kubernetes, ECS, Fly.io)
- **Managed services:** PostgreSQL (Supabase, Neon, RDS), Redis (Upstash, Redis Cloud)

---

## Appendix: MVP Scope Summary

### Exists at v0.1

- [x] Portfolio → Project hierarchy with board approval
- [x] PRD model with intake phase and scope approval
- [x] Sprint + backlog derived from board-approved PRD
- [x] Semantic + structured + working memory (vector is primary)
- [x] Scope + budget approval gates
- [x] Heartbeat execution (single agent, 30s interval)
- [x] Immutable audit log (episodic)
- [x] SQLite + Qdrant persistence
- [x] REST API for hierarchy and PRD workflow

### Deferred to v0.2+

- [ ] Program cross-project dependencies
- [ ] Multi-agent execution
- [ ] Staffing + Launch + Exception gates
- [ ] Cost tracking with variance
- [ ] Distributed deployment
- [ ] Multi-tenant isolation

---

*Architecture is a living document. Revise at each milestone based on what deployment reveals.*