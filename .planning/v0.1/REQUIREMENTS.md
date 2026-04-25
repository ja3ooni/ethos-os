# Requirements: EthosOS v0.2

**Defined:** 2026-04-25
**Base:** v0.1 (37 requirements, all complete)
**Goal:** AI agent integration with token-efficient orchestration

## v0.2 Requirements

### Agent Registry

- [ ] **AGENT-01**: Agent registry with SQLite-first storage (name, role, division, skills_summary, capabilities, cost)
- [ ] **AGENT-02**: Summary-only listings: never inject full prompts in directory views
- [ ] **AGENT-03**: Lazy loading: `get_for_execution()` fetches full config only at execution time
- [ ] **AGENT-04**: Import 147+ agents from agency-agents repo (parse YAML frontmatter only, not full prompts)
- [ ] **AGENT-05**: Agent capabilities stored as JSON array for filtering
- [ ] **AGENT-06**: Agent cost tracking (avg_response_tokens, cost_per_call_usd)
- [ ] **AGENT-07**: Agent status: is_active, is_hired, hired_at, max_monthly_budget_usd

### Agent Orchestration

- [ ] **ORCH-01**: Heartbeat-based task assignment: agents check for eligible tasks on each heartbeat
- [ ] **ORCH-02**: Capability matching: route tasks to agents with matching capabilities
- [ ] **ORCH-03**: CEO Agent integration: @chief-of-staff can create Programs/Projects from directives
- [ ] **ORCH-04**: Execution Agents execute autonomously within approved scope
- [ ] **ORCH-05**: Agent failure detection: missed heartbeats trigger task reassignment
- [ ] **ORCH-06**: Task assignment respects initiative hierarchy (PRD gate must pass)

### Chat UI

- [ ] **CHAT-01**: Paperclip-style chat interface: single input, agent switching, conversation history
- [ ] **CHAT-02**: Initiative context injection: selected initiative passed to agent
- [ ] **CHAT-03**: Agent switching: talk to CEO Agent, Project Lead, or Execution Agent
- [ ] **CHAT-04**: Real-time updates: agent progress in chat thread
- [ ] **CHAT-05**: Message persistence: SQLite storage for conversation history
- [ ] **CHAT-06**: Chat → Initiative linking: each conversation traces to initiative

### Vector Memory

- [ ] **MEM-01**: Qdrant integration for initiative document chunking
- [ ] **MEM-02**: Working memory cache with TTL (default 3600s, configurable)
- [ ] **MEM-03**: Context injection pipeline: Qdrant semantic search → working memory → agent prompt
- [ ] **MEM-04**: Initiative docs chunked and embedded (PRD, architecture docs, meeting notes)
- [ ] **MEM-05**: Semantic search on initiative content (not status queries)
- [ ] **MEM-06**: Cache invalidation on initiative updates

### Dashboard (Enhancements)

- [ ] **DASH-01**: Initiative tree with agent status overlay (idle/working/blocked per node)
- [ ] **DASH-02**: Agent status panel: list of agents with current status and task
- [ ] **DASH-03**: Gate approval board with agent assignments
- [ ] **DASH-04**: Agent performance metrics: tasks completed, avg response time, cost

### Integration

- [ ] **INT-01**: FastAPI endpoints for agent registry CRUD
- [ ] **INT-02**: FastAPI endpoints for chat messages
- [ ] **INT-03**: WebSocket support for real-time agent updates
- [ ] **INT-04**: Qdrant client integration (async)

## v0.2 Architecture Requirements

### Token Efficiency (Enforced)

| Pattern | Allowed | Prohibited |
|---------|---------|------------|
| Agent listings | Summary (name, role, summary) | Full prompts |
| Task assignment | Capability matching | Full agent context injection |
| Chat context | Initiative chunk references | Full PRD injection |
| Working memory | Runtime state only | Persistent context |

### Data Flow

```
agency-agents repo → YAML frontmatter only → SQLite registry (summaries)
                                              ↓
User request → Chat UI → Initiative context (Qdrant chunks) → Working memory
                                              ↓
Agent execution → Full config (lazy load) → Task execution → Heartbeat
```

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| AGENT-01 — AGENT-07 | Phase 1 | Pending |
| ORCH-01 — ORCH-06 | Phase 2 | Pending |
| CHAT-01 — CHAT-06 | Phase 3 | Pending |
| MEM-01 — MEM-06 | Phase 4 | Pending |
| DASH-01 — DASH-04 | Phase 5 | Pending |
| INT-01 — INT-04 | Phase 6 | Pending |

**Coverage:**
- v0.2 requirements: 27 new
- Total (v0.1 + v0.2): 64

---

*Requirements defined: 2026-04-25 for v0.2*