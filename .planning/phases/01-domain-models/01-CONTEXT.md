# Phase 1: Domain Models - Context

**Gathered:** 2026-04-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Core initiative hierarchy (portfolio → task) with board-approved PRD model, SQLite persistence, working memory, and project scaffolding. This phase delivers the data models other phases build on. No user-facing code, no API, no agent execution — pure domain + persistence.

</domain>

<decisions>
## Implementation Decisions

### PRD storage model
- **D-01:** Split storage — PRD metadata (intent, success_metric, scope, boundaries, timeline, budget) in SQLite for exact queries; PRD content body chunked and embedded in Qdrant for semantic recall
- **D-02:** PRD chunks stored in Qdrant at creation time — not deferred to v0.2 for this data type (PRD content is the primary use case for semantic memory)
- **D-03:** SQLite record has: id, project_id, intent, success_metric, scope, boundaries, timeline, budget, status, qdrant_collection_name, qdrant_point_id, created_at, updated_at

### Hierarchy schema design
- **D-04:** Materialized path — each entity stores both `parent_id` (UUID, nullable for root) and `path` (materialized path string, e.g., `/port-uuid/proj-uuid/`)
- **D-05:** Path format: `/{portfolio_id}/{program_id}/{project_id}/{sprint_id}/{task_id}` — each segment is UUID, leading slash, no trailing slash
- **D-06:** Lineage query (sprint → portfolio) is O(1) — split path and resolve segments. No recursive CTE needed
- **D-07:** Moving an entity to a new parent requires path migration for all descendants — update path prefix for all children in one transaction
- **D-08:** `path_depth` field on each entity enables filtering by level (portfolio=1, program=2, project=3, sprint=4, task=5, subtask=6)

### ORM approach
- **D-09:** SQLAlchemy 2.x with explicit session management — one session per request, commit on success, rollback on failure
- **D-10:** Alembic for schema migrations — SQLite for MVP, PostgreSQL migration path in config (deferred to production)
- **D-11:** Repository pattern — domain layer talks to repositories via interfaces, not SQLAlchemy directly
- **D-12:** Pydantic models for API schemas — separate from SQLAlchemy models (no SQLModel mixing)

### Working memory structure
- **D-13:** Dict keyed by `agent_id` (UUID string) — one dict entry per registered agent
- **D-14:** `threading.Lock` protects the dict during read/write — heartbeat runs in async but worker threads need synchronization
- **D-15:** Each agent entry: `{task_context, reasoning_state, subtask_decomposition, short_term_refs, last_updated}`
- **D-16:** Working memory is ephemeral — not persisted across restarts. Agent re-registers on restart with empty context
- **D-17:** `WorkingMemory` class wraps the dict with `get()`, `set()`, `clear()` methods

### Domain model completeness
- **D-18:** Entities in scope: Portfolio, Program, Project, PRD, Sprint, Backlog, Task, Subtask
- **D-19:** Entity must have: id (UUID), name, created_at, updated_at, owner_id
- **D-20:** Project has `prd_status`: draft → pending_approval → approved → archived
- **D-21:** Sprint has `goal`, `start_date`, `end_date`, `capacity_hours`
- **D-22:** Task has `prd_scope_item_id` (foreign key to PRD scope section) — this enforces "no task without PRD reference" at model level
- **D-23:** Subtask has `parent_task_id` and is agent-tracked only — not exposed in API for v0.1

### Validation rules
- **D-24:** Task creation validates `prd_scope_item_id` is not null — raises ValidationError if missing
- **D-25:** Sprint creation validates `project.prd_status == approved` — raises ValidationError if not
- **D-26:** Lineage fields are computed (not stored) — derived from parent_id traversal at read time for display only

### the agent's Discretion
- Exact Pydantic schema field definitions and validation rules
- Alembic migration naming conventions and migration file structure
- Seed data: what sample portfolio/program/project looks like
- Repository interface definitions (method signatures)
- Working memory TTL — how long before inactive agent context is pruned (default: 1 hour)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project specification
- `ethos-os/.planning/PROJECT.md` — Project context, constraints, core principles
- `ethos-os/.planning/REQUIREMENTS.md` — Phase 1 requirements: HIER-01–12, PRD-01–06, MEM-01, PERS-01–03
- `ethos-os/docs/ARCHITECTURE.md` — Module boundaries, memory architecture, technology choices
- `ethos-os/docs/ONTOLOGY.md` — Entity definitions, primitive entities, anti-patterns
- `ethos-os/plans/PRD.md` — Original EthosOS PRD (product vision reference)

### Stack decisions
- `ethos-os/.planning/research/STACK.md` §Technology Choices — Python 3.11+, FastAPI, SQLite, Qdrant, asyncio

### Design constraints
- `ethos-os/docs/ONTOLOGY.md` §Anti-Patterns — Rejects: "Just create a ticket", orphan tickets, ticket creep, Kanban for ticket chaos, bloat/overthinking
- `ethos-os/docs/ARCHITECTURE.md` §Intake Phase — No sprints without board-approved PRD; PRD gate blocks sprint creation

</canonical_refs>

<specifics>
## Specific Ideas

- "No orphan tickets" is a core principle — API and model layers both enforce PRD reference
- PRD content goes to Qdrant immediately (not deferred) because it's the primary use case for semantic memory
- Hierarchy path updates use batch transaction — all descendant paths updated atomically
- No workstream level in Phase 1 — removed in favor of simpler portfolio → program → project → sprint

</specifics>

<deferred>
## Deferred Ideas

- Workstream level — removed from Phase 1; revisit if projects need logical work groupings
- Closure table for hierarchy — not selected; materialized path is sufficient
- SQLModel — not selected; SQLAlchemy + separate Pydantic schemas
- Context manager class for working memory — not selected; dict + lock is simpler

</deferred>

---

*Phase: 01-domain-models*
*Context gathered: 2026-04-24*