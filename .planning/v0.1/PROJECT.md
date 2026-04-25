# EthosOS v0.2 — Initiative-Based AI Company OS

## What This Is

v0.2 adds AI agent integration to EthosOS. The existing v0.1 provides initiative hierarchy (Portfolio→Project→PRD→Sprint→Task), approval gates, and heartbeat framework. v0.2 introduces paperclip-style agent orchestration using 147+ agents from agency-agents.

**Core principle:** Agents execute initiatives autonomously. Humans govern at gates. CEO Agent creates initiatives; Execution Agents do the work.

## Core Value

v0.2 transforms EthosOS from a human-run PMO tool into an AI-augmented company OS:
- CEO Agent (AI) creates Programs and Projects from board direction
- Execution Agents (AI from agency-agents) execute tasks autonomously
- Board (humans) approve at gates; agents execute between gates
- Chat UI enables natural language interaction with the agent workforce

## Requirements

### Active (v0.2)

- [ ] **AGENT-01**: Agent registry with SQLite-first storage, token-efficient summaries
- [ ] **AGENT-02**: Lazy loading: full config fetched only at execution time
- [ ] **AGENT-03**: Import 147+ agents from agency-agents repo (YAML frontmatter only)
- [ ] **ORCH-01**: Heartbeat-based task assignment to agents
- [ ] **ORCH-02**: Agent orchestration: task routing by capability matching
- [ ] **ORCH-03**: CEO Agent (@chief-of-staff) strategic planning integration
- [ ] **CHAT-01**: Paperclip-style chat UI for agent interaction
- [ ] **CHAT-02**: Initiative context injection in chat
- [ ] **MEM-01**: Qdrant vector search for initiative documents
- [ ] **MEM-02**: Working memory cache with TTL (3600s default)
- [ ] **MEM-03**: Context injection pipeline: Qdrant → working → agent prompt
- [ ] **DASH-01**: Initiative tree with agent status overlay
- [ ] **DASH-02**: Agent status panel (idle/working/blocked)
- [ ] **DASH-03**: Gate approval board with agent assignments

### Out of Scope

- MCP/Skills-style prompt bloat (explicitly prohibited)
- Full agent prompt storage in SQLite (summary-only, full config from source)
- Multi-agent negotiation protocols
- Real-time video/voice chat

## Context

Existing EthosOS v0.1 provides:
- Initiative hierarchy (Portfolio→Program→Project→Sprint→Backlog→Task)
- Approval gates (scope +25%, budget +20%)
- Heartbeat framework (30s interval)
- SQLite persistence with Alembic
- 71 tests, 72% coverage

v0.2 adds:
- Agent registry (SQLite-first, token-efficient)
- Agent orchestration (heartbeat-based execution)
- Chat UI (paperclip-style interface)
- Vector memory (Qdrant integration)
- Dashboard enhancement (agent status, chat)

## Constraints

**Token Efficiency (Critical):**
- **NO MCP/Skills-style prompt bloat** — agents use summary-only listings
- SQLite-first for metadata, Qdrant only for semantic search
- Lazy loading: fetch full agent config only at execution time
- Working memory cache with TTL (3600s default)
- Initiative context chunked for vector storage

**Technical:**
- SQLite primary (existing), Qdrant secondary (new)
- Python 3.11+, FastAPI (existing)
- React/Next.js for chat UI (new)
- agency-agents repo as agent source (existing)

**Architecture:**
- Agent registry: SQLite stores summaries, source_path references agency-agents files
- Execution: Heartbeat triggers, gate-aware, working memory context
- Chat: Initiative context injected per message, not full context
- Memory: Qdrant for semantic, working for runtime, SQLite for authoritative

## Key Decisions

| Decision | Rationale | Status |
|----------|-----------|--------|
| SQLite-first agent registry | Fast lookups, minimal context | Implemented (v0.1 scaffold) |
| Lazy loading full config | Token efficiency | Pending |
| Qdrant for semantic only | Initiative docs, not status | Pending |
| Working memory with TTL | Runtime context, not persistent | Implemented (v0.1) |
| No MCP prompt bloat | 147 agents × full prompts = too many tokens | Enforced constraint |
| Chat UI paperclip-style | Direct agent interaction, not menu-driven | Pending |

---

*Last updated: 2026-04-25 for v0.2 initialization*