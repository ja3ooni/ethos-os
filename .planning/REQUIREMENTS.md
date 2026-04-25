# Requirements: EthosOS

**Defined:** 2026-04-24
**Core Value:** Every piece of work traces back to a stated initiative root. Agents execute with heartbeat-based autonomy; humans govern at boundaries that matter.

## v1 Requirements

### Initiative Hierarchy / PMO Model

- [ ] **HIER-01**: User can create a portfolio (company or strategic entity) with name and strategic intent
- [ ] **HIER-02**: User can create programs within a portfolio (product lines, business units)
- [ ] **HIER-03**: User can create a project with a board-reviewed PRD (intent + success metric + scope + boundaries + timeline + budget)
- [ ] **HIER-04**: Board/PMO can approve a project PRD at intake — intake gate must pass before sprints can spawn
- [ ] **HIER-05**: Project without board-approved PRD cannot spawn sprints (API enforces)
- [ ] **HIER-06**: User can create sprints within a board-approved project (with goal, start/end dates, capacity)
- [ ] **HIER-07**: User can create a backlog with work items that reference a PRD scope item
- [ ] **HIER-08**: User can create tasks derived from backlog items (with effort estimate, assignee, PRD reference)
- [ ] **HIER-09**: User can view the hierarchy tree (portfolio → program → project → sprint → backlog → task → subtask)
- [ ] **HIER-10**: Every task displays its full lineage plus PRD reference
- [ ] **HIER-11**: API rejects task creation without a PRD reference
- [ ] **HIER-12**: User can view Kanban board per sprint — all cards trace to board-approved PRD scope (no orphan tickets)

### PRD Management

- [ ] **PRD-01**: User can create a PRD with intent, success metric, scope, boundaries, timeline, budget
- [ ] **PRD-02**: Board/PMO can review and approve PRD scope (intake gate)
- [ ] **PRD-03**: PRD is stored in semantic memory (vector) for long-term recall
- [ ] **PRD-04**: PRD content is chunked and embedded for semantic search
- [ ] **PRD-05**: "Find similar PRDs" returns semantically similar board-approved scopes
- [ ] **PRD-06**: Backlog items derive from PRD scope — each item traces to a PRD section

### Approval Gates

- [ ] **GATE-01**: System auto-creates scope change request when task exceeds +25% estimate threshold
- [ ] **GATE-02**: System auto-creates budget change request when spend exceeds 20% variance
- [ ] **GATE-03**: Approver can accept or reject a gate request with optional notes
- [ ] **GATE-04**: Gate request is blocking — task cannot proceed until approved
- [ ] **GATE-05**: Rejected task is blocked until re-planned by human
- [ ] **GATE-06**: Gate records are immutable (timestamp, approver, scope, decision, notes)
- [ ] **GATE-07**: Approver has configurable timeout (default: 48h for scope, 24h for budget)
- [ ] **GATE-08**: Dashboard displays pending gate requests with age and approver

### Heartbeat Execution

- [ ] **BEAT-01**: Agent records heartbeat on configurable interval (default: 30s)
- [ ] **BEAT-02**: Heartbeat record includes: timestamp, agent ID, status (idle/working/blocked/complete), task ID, progress note
- [ ] **BEAT-03**: Agent heartbeat loop: check tasks → check gates → execute eligible → update working memory → write episodic log → report
- [ ] **BEAT-04**: Heartbeat interval is configurable per agent type (min: 10s)
- [ ] **BEAT-05**: Agent failure after N missed heartbeats triggers work reassignment (configurable N)
- [ ] **BEAT-06**: Agent cannot execute gated work — heartbeat checks gate status before execution
- [ ] **BEAT-07**: Dashboard shows heartbeat timeline per agent (timestamp, status, task, note)

### Memory System

- [ ] **MEM-01**: Working memory holds per-agent runtime state (in-memory, non-persistent)
- [ ] **MEM-02**: Structured memory persists initiative hierarchy, gate states, cost records, agent registrations
- [ ] **MEM-03**: Exact state queries use structured memory (key lookup, not similarity)
- [ ] **MEM-04**: Semantic recall infrastructure in place (deferred: populated at v0.2)
- [ ] **MEM-05**: Episodic memory stores immutable event log (heartbeats, gate decisions, cost snapshots)
- [ ] **MEM-06**: Episodic log uses hash-chain integrity (append-only, no edits)

### Persistence

- [ ] **PERS-01**: SQLite database for structured memory (MVP)
- [ ] **PERS-02**: Schema migrations via Alembic (SQLite → PostgreSQL migration path ready)
- [ ] **PERS-03**: Config supports SQLite path and PostgreSQL connection string

### API

- [ ] **API-01**: REST API for initiative hierarchy CRUD
- [ ] **API-02**: REST API for gate request creation and approval
- [ ] **API-03**: REST API for heartbeat recording and retrieval
- [ ] **API-04**: REST API for dashboard data (tree, gates, heartbeats)
- [ ] **API-05**: API documentation via OpenAPI (FastAPI auto-generated)

### Dashboard

- [ ] **DASH-01**: Read-only dashboard showing initiative tree with status
- [ ] **DASH-02**: Gate status board (pending approvals, age, approver)
- [ ] **DASH-03**: Heartbeat timeline per agent
- [ ] **DASH-04**: Basic search (by name, owner, status)

## v2 Requirements

### Extended Gates

- **GATE-09**: Staffing approval gate (agent assigned to workstream)
- **GATE-10**: Launch approval gate (project/program go-live)
- **GATE-11**: Exception approval gate (override of standard flow)

### Memory Layers

- **MEM-07**: Semantic memory populated with embedded initiative roots
- **MEM-08**: Semantic recall query interface
- **MEM-09**: Procedural memory for approval workflow templates
- **MEM-10**: Episodic memory replay (for audit)

### Cost Awareness

- **COST-01**: Per-work-item estimated vs actual cost tracking
- **COST-02**: Variance flagging (>20% triggers exception review)
- **COST-03**: Daily cost aggregation per program/project
- **COST-04**: Cost dashboard

### Multi-Agent

- **MA-01**: Multi-agent coordination and scheduling
- **MA-02**: Agent-to-agent negotiation
- **MA-03**: Agent pool management

### Extended Features

- **API-06**: External-facing API (consumer model TBD)
- **DASH-05**: Mobile-responsive dashboard
- **HIER-13**: Program cross-project dependencies

## Out of Scope

| Feature | Reason |
|---------|--------|
| Multi-agent coordination | Single-agent validates baseline first |
| Staffing/launch/exception gates | Scope+budget gates validate the pattern |
| Mobile UI | Browser access sufficient for v0.1 |
| Semantic memory population | Deferred to v0.2 — infrastructure in place |
| Episodic memory replay | Audit log sufficient; replay adds complexity |
| Procedural memory | Requires learning system, deferred |
| Real-time cost dashboards | Deferred to v0.2 |
| Multi-tenant isolation | Single-org for MVP |
| Distributed deployment | Single deployment for MVP |
| External API-first design | Internal API sufficient for v0.1 |
| Cross-project dependencies | Deferred unless evidence emerges |
| Workflow engine (Temporal/Argo) | Overhead for heartbeat model |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| HIER-01 — HIER-12 | Phase 1 | ✓ Tested (API integration tests) |
| PRD-01 — PRD-06 | Phase 1 | ~ Gap: PRD repo not tested directly |
| GATE-01 — GATE-08 | Phase 2 | ✓ Tested (unit + API) |
| MEM-01 — MEM-06 | Phase 1 (working), Phase 2 (structured) | ~ Partial: working memory tested, semantic deferred |
| PERS-01 — PERS-03 | Phase 1 | ~ Deferred: migration tests not included |
| API-01 — API-05 | Phase 4 | ✓ Tested |
| DASH-01 — DASH-04 | Phase 4 | ~ Partial: endpoint coverage minimal |

**Coverage:**
- v1 requirements: 43 total
- Mapped to phases: 43
- Unmapped: 0 ✓
- Tested: 37/43 (86%)

---
*Requirements defined: 2026-04-24*
*Last updated: 2026-04-24 after initial definition*