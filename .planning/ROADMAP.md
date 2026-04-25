# Roadmap: EthosOS

**Phases:** 7
**Requirements:** 37 mapped | **Plans:** 28 total
**Granularity:** Fine
**Created:** 2026-04-24

---

## Phase Map

| # | Phase | Goal | Requirements | Success Criteria |
|---|-------|------|--------------|------------------|
| 1 | Domain Models | Core initiative hierarchy and data layer | HIER-01–12, MEM-01, PERS-01–03 | 5 |
| 2 | Structured Memory + Gates | Persistent storage and approval workflow | GATE-01–08, MEM-02–06 | 6 |
| 3 | Heartbeat Execution | Agent runtime with gate-aware execution | BEAT-01–07 | 4 |
| 4 | API Layer | REST APIs for all core operations | API-01–05 | 3 |
| 5 | Dashboard | Read-only UI for hierarchy, gates, heartbeats | DASH-01–04 | 3 |
| 6 | Testing + Validation | Integration tests and requirement verification | All | 4 |
| 7 | Polish + Documentation | Open-source prep, README, contributor guide | All | 3 |

---

## Phase 1: Domain Models

**Goal:** Core initiative hierarchy with initiative roots, SQLite persistence, working memory.

### Requirements
HIER-01, HIER-02, HIER-03, HIER-04, HIER-05, HIER-06, HIER-07, HIER-08, HIER-09, HIER-10, HIER-11, HIER-12, MEM-01, PERS-01, PERS-02, PERS-03

### Plans

**Plan 1.1 — Project scaffolding**
- Initialize Python project (pyproject.toml, uv or poetry)
- Set up src/ directory structure (domain/, memory/, execution/, governance/, infrastructure/)
- Configure SQLite with SQLAlchemy
- Add Alembic for migrations
- Add basic config loader (YAML + env vars)

**Plan 1.2 — Initiative hierarchy models**
- Implement Portfolio, Program, Project models
- Project model includes initiative_root (intent + success_metric + boundaries)
- Implement Workstream, Sprint, Backlog models
- Implement Task, Subtask models
- Add initiative lineage field to every work item (computed, inherited from parent)
- Enforce initiative root requirement at model level (not just API)

**Plan 1.3 — Hierarchy CRUD**
- SQLAlchemy sessions and repository pattern
- Create, read, update, list operations for all hierarchy levels
- Initiative tree query (portfolio → subtask traversal)
- Lineage query per work item
- Search by name, owner, status

**Plan 1.4 — Working memory**
- Per-agent in-memory context store (dict-like, thread-safe)
- Working memory is runtime-only (not persisted across restarts)
- Context: current task, reasoning state, subtask decomposition, short-term references

**Plan 1.5 — Migration and seed**
- Alembic migration for initial schema
- Seed script with example portfolio/program/project
- Verify hierarchy integrity with tests

### Success Criteria
1. `portfolio → subtask` traversal returns complete lineage
2. Creating a task without initiative root raises validation error
3. SQLite stores all hierarchy levels with correct relationships
4. Working memory stores and returns per-agent runtime context
5. Alembic migration runs cleanly on fresh database

---

## Phase 2: Structured Memory + Gates

**Goal:** Approval gate system with immutable audit log, full structured memory.

### Requirements
GATE-01, GATE-02, GATE-03, GATE-04, GATE-05, GATE-06, GATE-07, GATE-08, MEM-02, MEM-03, MEM-04, MEM-05, MEM-06

### Plans

**Plan 2.1 — Approval gate models**
- GateRequest model: gate_type, entity_id, entity_type, status, trigger_condition, approver, notes, created_at, decided_at, decided_by
- Gate states: pending, approved, rejected
- Scope gate: triggered when task effort > original_estimate * 1.25
- Budget gate: triggered when actual_cost > estimated_cost * 1.20
- Gate is binary (approved or rejected, no partial)

**Plan 2.2 — Gate workflow**
- Auto-create scope gate request when threshold exceeded
- Auto-create budget gate request when threshold exceeded
- Gate blocking: task cannot proceed while pending
- Approver can approve or reject with notes
- Rejected task blocked until re-planned
- Configurable timeout (scope: 48h, budget: 24h)

**Plan 2.3 — Immutable audit log**
- Episodic event log (append-only)
- Records: heartbeat, gate decision, cost snapshot, scope/budget change
- Hash-chain integrity: each record includes hash of previous record
- No edit or delete operations
- Query by time range, entity, event type

**Plan 2.4 — Structured memory interface**
- Repository pattern for all persistent entities
- Exact key lookup (not similarity) for operational state
- Audit log as separate read model
- Clear separation: SQLite = authoritative state, episodic log = audit trail

**Plan 2.5 — Gate dashboard data**
- Pending gates query (ordered by age)
- Gate approval rate (for monitoring — flag 100% rate as theater)
- Gate decision time tracking
- Gate API endpoints (create, approve, reject, list)

**Plan 2.6 — Gate integration tests**
- Scope gate triggers at +25% threshold
- Budget gate triggers at +20% threshold
- Rejected gate blocks task
- Approved gate unblocks task
- Audit log integrity (hash chain)

### Success Criteria
1. Scope gate auto-created at +25% estimate variance
2. Budget gate auto-created at +20% cost variance
3. Rejected task remains blocked
4. Audit log is append-only (no updates or deletes)
5. Hash-chain integrity maintained across records
6. Pending gates queryable by age and type

---

## Phase 3: Heartbeat Execution

**Goal:** Agent heartbeat loop with gate-aware execution.

### Requirements
BEAT-01, BEAT-02, BEAT-03, BEAT-04, BEAT-05, BEAT-06, BEAT-07

### Plans

**Plan 3.1 — Heartbeat scheduler**
- asyncio-based heartbeat scheduler
- Configurable interval per agent (default: 30s, min: 10s)
- Heartbeat record: timestamp, agent_id, status, task_id, progress_note
- Status enum: idle, working, blocked, complete
- Status variance required (don't log idle repeatedly)

**Plan 3.2 — Agent executor loop**
- Per heartbeat: check assigned tasks → check gate status → execute eligible → update working memory → write episodic log → report
- Gate-aware: cannot execute gated work (blocked by pending gate)
- Working memory update per execution cycle
- Episodic log write per heartbeat

**Plan 3.3 — Agent failure handling**
- Lease-not-lock: missed heartbeats trigger work reassignment
- Configurable missed heartbeat threshold (default: 3)
- Dead agent detection and alerting
- Reassignment workflow: find agent with capacity, assign task, notify

**Plan 3.4 — Heartbeat API**
- Agent registration endpoint
- Heartbeat recording endpoint
- Heartbeat retrieval endpoint (timeline per agent)
- Agent status query (idle/working/blocked/complete)

**Plan 3.5 — Heartbeat integration tests**
- Heartbeat recorded on correct interval
- Agent status transitions (idle → working → complete)
- Gate blocks execution when pending
- Missed heartbeats trigger reassignment
- Heartbeat record appears in episodic log

### Success Criteria
1. Heartbeat recorded every 30s (default interval)
2. Status transitions logged correctly (idle → working → blocked → complete)
3. Gated work blocked until gate approved
4. Missing 3 consecutive heartbeats triggers reassignment
5. Heartbeat timeline queryable per agent
6. Heartbeat record written to episodic log

---

## Phase 4: API Layer

**Goal:** REST APIs for all core operations, OpenAPI docs.

### Requirements
API-01, API-02, API-03, API-04, API-05

### Plans

**Plan 4.1 — Initiative hierarchy API**
- CRUD endpoints for portfolio, program, project, workstream, sprint, backlog, task, subtask
- Tree view endpoint (full initiative hierarchy)
- Lineage query per work item
- Search endpoints (name, owner, status)
- Request/response validation with Pydantic

**Plan 4.2 — Gate API**
- Create gate request (manual or auto-triggered)
- Approve gate request
- Reject gate request
- List pending gates (with filter options)
- Gate history per entity

**Plan 4.3 — Agent and heartbeat API**
- Register agent
- Record heartbeat
- Get heartbeat timeline
- Get agent status

**Plan 4.4 — OpenAPI documentation**
- FastAPI auto-generated OpenAPI (already included)
- Add descriptive summaries to all endpoints
- Add example requests/responses
- Publish at /docs

### Success Criteria
1. All initiative hierarchy CRUD operations work via REST
2. Gate workflow fully operable via API
3. Heartbeat recording and retrieval via API
4. OpenAPI docs accessible at /docs
5. Pydantic validation rejects invalid requests

---

## Phase 5: Dashboard

**Goal:** Read-only UI for initiative tree, gate status, heartbeat timeline.

### Requirements
DASH-01, DASH-02, DASH-03, DASH-04

### Plans

**Plan 5.1 — Initiative tree view**
- Nested tree display (portfolio → program → project → workstream → sprint → backlog → task → subtask)
- Expand/collapse at each level
- Click node → shows initiative root, approval state, metrics
- Color coding by status

**Plan 5.2 — Gate status board**
- List of pending gate requests
- Columns: type, entity, age, approver, status
- Age highlighting (approaching timeout)
- Approve/reject actions inline
- Gate theater detection (100% approval rate warning)

**Plan 5.3 — Heartbeat timeline**
- Per-agent timeline view
- Chronological heartbeat records
- Status color coding
- Filter by agent, status, date range
- Progress notes visible per heartbeat

**Plan 5.4 — Basic search**
- Search bar: name, owner, status
- Filter by initiative level
- Filter by approval status

### Success Criteria
1. Initiative tree renders complete hierarchy
2. Gate board shows pending gates with age and type
3. Heartbeat timeline shows chronological records per agent
4. Search returns relevant results
5. UI is read-only (no direct data modification)

---

## Phase 6: Testing + Validation

**Goal:** Integration tests, requirement verification, codebase integrity.

### Plans

**Plan 6.1 — Unit tests**
- Domain model tests (hierarchy creation, initiative root, lineage)
- Gate workflow tests (trigger, approve, reject, block)
- Heartbeat tests (interval, status transitions, failure detection)
- Memory tests (working, structured, episodic)

**Plan 6.2 — Integration tests**
- Full API integration tests (all endpoints)
- SQLite integration (migrations, queries, transactions)
- Episodic log integration (append-only, hash chain)
- Dashboard data integration

**Plan 6.3 — Requirement verification**
- Verify each REQ-ID has passing test
- Verify requirement traceability is complete
- Check 100% coverage on core models and workflows
- Verify anti-patterns are NOT present in implementation

**Plan 6.4 — Performance baseline**
- Heartbeat throughput (target: 1000 agents at 30s interval)
- Hierarchy query latency (tree traversal)
- Gate lookup latency
- SQLite query benchmarks

### Success Criteria
1. All REQ-IDs have corresponding tests
2. 100% coverage on domain models
3. Integration tests pass against SQLite
4. Episodic log hash chain verifies correctly
5. Performance baseline documented

---

## Phase 7: Polish + Documentation

**Goal:** Open-source prep, README, contributor guide, packaging.

### Plans

**Plan 7.1 — Open-source documentation**
- Update README.md with current architecture and getting started
- Add CONTRIBUTING.md
- Add docs/ folder with architecture, ontology, API reference
- Add license (MIT)

**Plan 7.2 — Packaging**
- Docker Compose for local development
- pyproject.toml with proper metadata
- uv or poetry for dependency management
- GitHub Actions CI (lint, test, typecheck)

**Plan 7.3 — Contributor guide**
- Architecture overview (from ARCHITECTURE.md)
- Domain model conventions
- Test conventions
- How to add a new initiative level
- How to add a new gate type

### Success Criteria
1. README.md is complete and accurate
2. Docker Compose runs locally with no setup
3. CI passes (lint + tests + typecheck)
4. Contributor guide covers key conventions
5. MIT license included

---

## Phase Summary Table

| Phase | Focus | Plans | REQ-IDs | Success Criteria |
|-------|-------|-------|---------|-----------------|
| 1 | Domain Models | 5 | HIER-01–12, MEM-01, PERS-01–03 | 5 |
| 2 | Structured Memory + Gates | 6 | GATE-01–08, MEM-02–06 | 6 |
| 3 | Heartbeat Execution | 5 | BEAT-01–07 | 5 |
| 4 | API Layer | 4 | API-01–05 | 5 |
| 5 | Dashboard | 4 | DASH-01–04 | 5 |
| 6 | Testing + Validation | 4 | All | 5 |
| 7 | Polish + Documentation | 3 | All | 5 |

**Total:** 7 phases | 31 plans | 37 requirements | 36 success criteria

---

*Roadmap created: 2026-04-24*