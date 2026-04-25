# Pitfalls Research: EthosOS

**Domain:** Initiative-based OS for human-agent organizations
**Date:** 2026-04-24
**Dimension:** Pitfalls

## Question

What do initiative-based OS projects commonly get wrong? Critical mistakes?

## Common Pitfalls

### 1. Ticket Creep

**What it is:** Starting with tasks instead of initiative roots. The hierarchy exists but tasks are created without tracing to an initiative.

**Warning signs:**
- Tasks created without a project parent
- "Why are we doing this?" not answered in task description
- Backlog grows faster than initiatives

**Prevention:**
- Enforce initiative root before task creation (API-level validation)
- Dashboard shows initiative trace on every work item
- Ontology explicitly defines this as anti-pattern

**Phase to address:** Phase 1 (domain models)

### 2. Gate Theater

**What it is:** Approval gates that exist but are never used. Humans approve anything to unblock work.

**Warning signs:**
- Gates show 100% approval rate
- Gate decisions take < 1 minute
- No variance in approval notes

**Prevention:**
- Track gate decision time (long decisions = real deliberation)
- Flag zero-variance gate patterns as process failure
- Keep gates binary (no "approved with modifications" ambiguity)

**Phase to address:** Phase 4 (governance) + monitoring in dashboard

### 3. Heartbeat Noise

**What it is:** 30s heartbeats producing so much data that signal is lost. Every agent heartbeat fills logs with noise.

**Warning signs:**
- 10,000+ heartbeat records per day with minimal status variance
- No meaningful progress notes
- Heartbeat storage grows unbounded

**Prevention:**
- Default to 30s but allow per-agent configuration
- Heartbeat record is minimal: timestamp, status, task_id, one-line note
- Prune heartbeat records after 30 days (configurable)
- Status variance required (don't log `idle` repeatedly)

**Phase to address:** Phase 3 (execution engine) + Phase 5 (episodic cleanup)

### 4. Vector as Truth

**What it is:** Using semantic search results as authoritative state rather than as suggestions or context augmentation.

**Warning signs:**
- "What is the status of Sprint 23?" answered via vector similarity
- Semantic search returns single result treated as canonical answer
- No exact-match fallback when semantic search fails

**Prevention:**
- Explicit separation: vector = semantic context, SQLite = authoritative state
- API-level documentation of retrieval semantics
- Ontology defines this as anti-pattern explicitly

**Phase to address:** Phase 6 (semantic layer) — design phase, not just implementation

### 5. Complexity Accumulation

**What it is:** Adding "nice to have" features in early phases because they seem small. 10 small decisions compound into unmaintainable complexity.

**Warning signs:**
- > 3 new files added per PR with no clear necessity
- Architecture doc mentions "deferred" features in current phase scope
- PR descriptions include "also fixed X while I was in there"

**Prevention:**
- MVP scope is explicit — each feature must justify inclusion
- Architecture doc has MVP/deferred separation
- PRD has "What is NOT in MVP" table
- Reject complexity unless scale requires it (architectural principle)

**Phase to address:** All phases — continuous discipline

### 6. Process Over Governance

**What it is:** Adding process documents, checklists, and procedures to enforce governance instead of building structural governance into the hierarchy.

**Warning signs:**
- Approval gate lives in a doc, not in the system
- "How to approve" documentation longer than the approval feature
- Governance requires training to understand

**Prevention:**
- Gates are API endpoints, not workflow documents
- Hierarchy enforces governance (if hierarchy exists, gates are applied)
- Dashboard shows gate status, not gate instructions
- Ontology: "governance is structural, not procedural"

**Phase to address:** Phase 4 (governance) — design with structural enforcement

### 7. Agent Autonomy Creep

**What it is:** Agents executing beyond their bounds because heartbeat loop runs faster than human review cycle.

**Warning signs:**
- Agents completing tasks faster than humans can review
- Scope expansions happening without gate triggers
- "Agent decided" in audit log without human approval

**Prevention:**
- Gates are blocking — agent cannot execute gated work
- Heartbeat interval is configurable but bounded (min: 10s)
- Audit log tracks agent actions separately from approvals
- Ontology: "agents execute within bounds"

**Phase to address:** Phase 3 (execution) + Phase 4 (governance)

### 8. Premature Multi-Agent

**What it is:** Adding multi-agent coordination before single-agent execution is validated.

**Warning signs:**
- Designing agent-to-agent messaging in Phase 1
- Planning multi-agent scheduling before heartbeat is working
- Dependencies on Temporal/Argo before single instance is proven

**Prevention:**
- MVP is explicitly single-agent
- Multi-agent is deferred to v0.2
- Single agent validates heartbeat model first

**Phase to address:** Phase 3 — resist temptation to add multi-agent early

### 9. Schema Drift

**What it is:** Initiative hierarchy levels added, removed, or modified mid-build. Portfolio becomes "Program," workstream disappears.

**Warning signs:**
- Multiple schema migrations in first 3 months
- "We don't really use the program level"
- Initiative root moves between levels

**Prevention:**
- Ontology is the contract — no drift without explicit update
- PRs must update ontology if they change the model
- Architecture doc has explicit level definitions with ownership

**Phase to address:** Phase 1 (domain) — lock hierarchy before implementation

### 10. Vector Over-Indexing

**What it is:** Indexing everything in vector store at v0.1, degrading recall precision.

**Warning signs:**
- > 10 content types in vector index
- "Just in case" embeddings
- Semantic search returns irrelevant but "similar" results

**Prevention:**
- Vector store deferred to v0.2 in MVP
- Only initiative roots are semantically indexed (explicit scope)
- Ontology: "vector retrieval answers 'what's related?' not 'what's current status?'"

**Phase to address:** Phase 6 — strict content type limit for v0.2

## Phase Mapping

| Pitfall | Phase | Warning Sign to Watch |
|---------|-------|---------------------|
| Ticket Creep | 1 | Tasks without initiative root |
| Gate Theater | 4 | 100% approval rate |
| Heartbeat Noise | 3 | >10k records/day, no variance |
| Vector as Truth | 6 | Semantic result as state |
| Complexity Accumulation | All | >3 files/PR, "while I was here" |
| Process Over Governance | 4 | Docs longer than feature |
| Agent Autonomy Creep | 3 | Tasks completed before review |
| Premature Multi-Agent | 3 | Messaging in single-agent phase |
| Schema Drift | 1 | Multiple migrations, unused levels |
| Vector Over-Indexing | 6 | >10 content types indexed |

## Confidence

- All pitfalls identified: **High** — drawn from EthosOS design process itself
- Phase mapping: **High** — derived from architecture decomposition
- Prevention strategies: **High** — built into design decisions