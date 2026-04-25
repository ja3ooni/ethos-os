# Roadmap: EthosOS v0.2

**Phases:** 6
**Requirements:** 27 new | **Plans:** 18 total
**Granularity:** Fine
**Created:** 2026-04-25
**Base:** v0.1 (7 phases complete)

---

## Phase Map

| # | Phase | Goal | Requirements | Success Criteria |
|---|-------|------|--------------|------------------|
| 1 | Agent Registry | Import agents from agency-agents, complete registry | AGENT-01–07 | 4 |
| 2 | Agent Orchestration | Heartbeat-based task routing, CEO Agent integration | ORCH-01–06 | 4 |
| 3 | Chat UI | Paperclip-style interface, initiative context | CHAT-01–06 | 4 |
| 4 | Vector Memory | Qdrant integration, context injection pipeline | MEM-01–06 | 4 |
| 5 | Dashboard | Agent status overlay, gate board enhancement | DASH-01–04 | 3 |
| 6 | Integration + Testing | API endpoints, WebSocket, end-to-end tests | INT-01–04 | 4 |

---

## Phase 1: Agent Registry

**Goal:** Complete agent registry with agency-agents import and token-efficient architecture.

### Requirements
AGENT-01, AGENT-02, AGENT-03, AGENT-04, AGENT-05, AGENT-06, AGENT-07

### Plans

**Plan 1.1 — Complete agent registry schema**
- Verify existing Agent model covers all fields
- Add indexes for role, division, capabilities
- Add hiring info fields (is_hired, hired_at, salary, budget)
- Write tests for summary vs full config retrieval

**Plan 1.2 — Import from agency-agents**
- Parse YAML frontmatter only (NOT full prompts)
- Extract: name, description, color
- Infer: role from name patterns, division from path
- Extract capabilities from description keywords
- Truncate summary to 200 chars max
- Write import script with progress tracking
- Target: 147+ agents imported

**Plan 1.3 — Token-efficient query methods**
- `list_for_task()`: returns summary only, configurable filters
- `get_for_execution()`: returns full config including prompt_reference
- `search_by_capability()`: SQLite text search on summary
- Verify no full prompts leak in listings

**Plan 1.4 — Agent lifecycle**
- Hire agent: from agency-agents into company
- Fire agent: terminate employment
- Update budget, role, division
- Usage tracking: last_used_at

### Success Criteria
1. 147+ agents imported from agency-agents (summary only)
2. `list_for_task()` returns summaries without full prompts
3. `get_for_execution()` returns full config for execution
4. Agent hiring/firing lifecycle functional

---

## Phase 2: Agent Orchestration

**Goal:** Heartbeat-based task assignment with CEO Agent integration.

### Requirements
ORCH-01, ORCH-02, ORCH-03, ORCH-04, ORCH-05, ORCH-06

### Plans

**Plan 2.1 — Task → Agent routing**
- Match task requirements to agent capabilities
- Consider: role (ceo/lead/execution), division, specialization
- Avoid: token-heavy context injection
- Route to cheapest capable agent first

**Plan 2.2 — Heartbeat task loop**
- Per heartbeat: check for assigned tasks
- Check gate status before execution
- Update working memory with current task
- Write episodic log entry
- Return execution result

**Plan 2.3 — CEO Agent integration**
- Locate @chief-of-staff agent in agency-agents
- Integrate as strategic planning agent
- CEO Agent creates Programs from board directives
- CEO Agent creates Projects from approved programs
- CEO Agent proposes PRDs for board approval

**Plan 2.4 — Failure handling**
- Detect missed heartbeats (configurable threshold)
- Trigger task reassignment
- Notify human overseer
- Log reassignment event

### Success Criteria
1. Tasks route to capable agents based on capability matching
2. Heartbeat loop includes task assignment check
3. CEO Agent can create Programs/Projects
4. Failed agent triggers task reassignment

---

## Phase 3: Chat UI

**Goal:** Paperclip-style chat interface for natural agent interaction.

### Requirements
CHAT-01, CHAT-02, CHAT-03, CHAT-04, CHAT-05, CHAT-06

### Plans

**Plan 3.1 — React chat component**
- Single input field, conversation history
- Agent avatar and name per message
- Initiative context shown in sidebar
- Message types: user, agent, system
- Loading states for agent response

**Plan 3.2 — Initiative context injection**
- Selected initiative available in chat
- Inject initiative summary (not full PRD)
- Chunk references for deep dive
- Context updates on initiative selection change

**Plan 3.3 — Agent switching**
- Dropdown to select active agent
- CEO Agent for strategic queries
- Project Lead for project questions
- Execution Agents for task-specific help
- Clear conversation on agent switch

**Plan 3.4 — Conversation persistence**
- SQLite storage for messages
- Link conversation to initiative
- Conversation history per initiative
- Search within conversations

### Success Criteria
1. Chat UI renders and accepts input
2. Agent responses appear with agent attribution
3. Initiative context injected in messages
4. Conversation history persisted

---

## Phase 4: Vector Memory

**Goal:** Qdrant integration for semantic search and context injection.

### Requirements
MEM-01, MEM-02, MEM-03, MEM-04, MEM-05, MEM-06

### Plans

**Plan 4.1 — Qdrant setup**
- Docker Compose Qdrant container
- Collection schema for initiative chunks
- Embedding model selection (open-source)
- Async client integration

**Plan 4.2 — Initiative chunking**
- PRD chunking: intent, success_metric, scope, boundaries
- Architecture doc chunking: sections
- Meeting notes chunking: key decisions
- Chunk size target: 512 tokens
- Metadata: initiative_id, chunk_type, created_at

**Plan 4.3 — Context injection pipeline**
- Qdrant semantic search → relevant chunks
- Chunks → working memory (with TTL)
- Working memory → agent prompt (as references)
- Avoid full context injection (token limit)

**Plan 4.4 — Cache management**
- Working memory TTL: 3600s default
- Cache invalidation on initiative update
- Background prune of inactive agents
- Memory usage monitoring

### Success Criteria
1. Qdrant collection created with initiative chunks
2. Semantic search returns relevant chunks
3. Context injected as references (not full content)
4. Working memory respects TTL

---

## Phase 5: Dashboard

**Goal:** Initiative tree with agent status, enhanced gate board.

### Requirements
DASH-01, DASH-02, DASH-03, DASH-04

### Plans

**Plan 5.1 — Agent status overlay**
- Initiative tree nodes show assigned agent
- Color coding: idle (gray), working (green), blocked (red)
- Click agent → agent detail panel
- Filter by agent status

**Plan 5.2 — Agent status panel**
- List all active agents
- Current task and progress
- Last heartbeat timestamp
- Heartbeat status indicator
- Cost tracking (calls, tokens)

**Plan 5.3 — Gate board enhancement**
- Pending gates show assigned agents
- Agent workload visualization
- Gate aging with agent context
- Quick actions: reassign agent

**Plan 5.4 — Agent metrics**
- Tasks completed per agent
- Average response time
- Cost per agent
- Success rate (tasks completed vs blocked)

### Success Criteria
1. Initiative tree shows agent status per node
2. Agent panel lists all agents with current status
3. Gate board shows agent assignments
4. Basic metrics displayed

---

## Phase 6: Integration + Testing

**Goal:** API endpoints, WebSocket, end-to-end validation.

### Requirements
INT-01, INT-02, INT-03, INT-04

### Plans

**Plan 6.1 — Agent API endpoints**
- CRUD for agent registry
- List agents with filters
- Get agent full config
- Hire/fire agents
- Update agent budget

**Plan 6.2 — Chat API endpoints**
- Send message to agent
- Get conversation history
- List conversations by initiative
- WebSocket for real-time updates

**Plan 6.3 — WebSocket integration**
- Real-time agent status updates
- Chat message streaming
- Initiative tree live updates
- Gate status notifications

**Plan 6.4 — End-to-end tests**
- Agent import → registry → listing
- Task assignment → execution → completion
- Chat → context injection → response
- Initiative → Qdrant → context injection

### Success Criteria
1. All agent CRUD via REST API
2. Chat messages persisted and retrieved
3. WebSocket delivers real-time updates
4. End-to-end flow from import to execution works

---

## Phase Summary Table

| Phase | Focus | Plans | REQ-IDs | Success Criteria |
|-------|-------|-------|---------|------------------|
| 1 | Agent Registry | 4 | AGENT-01–07 | 4 |
| 2 | Orchestration | 4 | ORCH-01–06 | 4 |
| 3 | Chat UI | 4 | CHAT-01–06 | 4 |
| 4 | Vector Memory | 4 | MEM-01–06 | 4 |
| 5 | Dashboard | 4 | DASH-01–04 | 4 |
| 6 | Integration | 4 | INT-01–04 | 4 |

**Total:** 6 phases | 24 plans | 27 requirements | 24 success criteria

---

*Roadmap created: 2026-04-25 for v0.2*