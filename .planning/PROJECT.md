# EthosOS

## What This Is

An open-source initiative-based operating system for human-agent organizations. EthosOS replaces ticket-first project management with project-first PMO-style coordination modeled after how companies actually run: a company is a portfolio, a product launch is a project with a board-approved PRD, sprints and backlog derive from approved scope, not orphan tickets. Agents execute via heartbeat within board-approved bounds. Humans govern through PMO approval gates at intake, scope, budget, and launch. Memory is vector-first for token efficiency — big context (PRDs, architecture docs, meeting notes) never hits context windows.

**Core principle:** No sprints without board-approved PRD. No backlog without PRD reference. No orphan tickets.

## Core Value

Every piece of work traces back to a stated initiative root. Agents execute with heartbeat-based autonomy; humans govern at boundaries that matter. The hierarchy is a real-time map of what's happening and why — not organizational theater.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Portfolio → program → project → sprint → backlog → task → subtask hierarchy with board-approved PRD at intake
- [ ] Intake gate: PRD scope approved by board/PMO before sprints spawn
- [ ] No orphan tickets: every task traces to board-approved PRD scope
- [ ] Heartbeat execution engine (30s default interval)
- [ ] Vector-primary memory: PRD chunks, architecture docs, meeting notes in Qdrant
- [ ] Structured memory: exact state in SQLite (gate status, sprint data)
- [ ] Immutable audit log (episodic)
- [ ] Kanban board per sprint — all cards trace to board-approved PRD scope
- [ ] Semantic search on PRD content and architecture docs
- [ ] REST API for hierarchy, PRD workflow, and heartbeat

### Out of Scope

- Multi-agent coordination — single-agent validates baseline first
- Staffing, launch, exception approval gates — scope+budget gates validate the pattern
- Mobile UI — browser access sufficient for v0.1
- Real-time cost dashboards — deferred to v0.2
- Semantic memory population — deferred to v0.2
- Episodic memory replay — deferred to v0.2
- Procedural memory — deferred to v0.2
- Multi-tenant isolation — single-org for MVP
- Distributed deployment — single deployment for MVP
- API-first architecture for external consumers — internal API sufficient for v0.1
- Program cross-project dependencies — deferred to v0.2

## Context

Greenfield project. Open-source OS being built from scratch. Core design is initiative-first (not ticket-first), which is a deliberate inversion of the dominant PM paradigm. Heartbeat interval set to 30s (configurable). Approval thresholds for scope (+25%) and budget (20% variance) are assumptions — need validation with early users. Backend: Python 3.11+, FastAPI, SQLite (MVP). Vector store: Qdrant or local embeddings (open-source, optional cloud).

Existing EthosOS artifacts (docs/) define the ontology, architecture, and MVP scope — these are the living specification.

## Constraints

- **Tech stack**: Python 3.11+, FastAPI, SQLite (MVP) / PostgreSQL (scale) — open-source, no vendor lock-in
- **Vector store**: Qdrant — primary memory for big context chunks, not optional
- **Memory**: Semantic (Qdrant) is primary, structured (SQLite) is authoritative state — vector stores PRD chunks to save tokens
- **PRD gate**: Intake gate blocks sprints until board approves PRD scope — mirrors PMO workflows
- **No orphan tickets**: API enforces PRD reference before task creation

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Initiative-first over ticket-first | Tickets create adversarial dynamics, no outcome context | — Pending |
| Heartbeat over event-driven | Event ordering fragile under load; heartbeat is predictable and debuggable | — Pending |
| Vector retrieval semantic-only | Vector answers "what's related?" not "what's current status?" | — Pending |
| SQLite for MVP | Zero-dependency, no vendor lock-in, relational fits hierarchy | — Pending |
| Working + structured memory at v0.1 | Validate tiering before investing in episodic/semantic/procedural | — Pending |
| Scope + budget gates at v0.1 | Minimal governance; staffing/launch/exception deferred | — Pending |
| 30s heartbeat interval | 60s too slow for failure detection; 10s too noisy | — Pending spike |

---

*Last updated: 2026-04-24 after initialization*