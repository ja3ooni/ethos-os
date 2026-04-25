# Architecture Research: EthosOS

**Domain:** Initiative-based OS for human-agent organizations
**Date:** 2026-04-24
**Dimension:** Architecture

## Question

How are initiative-based OS / human-agent coordination systems typically structured? What are major components?

## Component Architecture

EthosOS follows a layered architecture: domain core (no dependencies) → memory → execution → governance → infrastructure.

### Layer Map

```
┌─────────────────────────────────────────────────────┐
│  INFRASTRUCTURE   (pluggable: DB, vector, messaging)│
├─────────────────────────────────────────────────────┤
│  GOVERNANCE      (depends: domain, memory)           │
├─────────────────────────────────────────────────────┤
│  EXECUTION       (depends: domain, memory, gov)     │
├─────────────────────────────────────────────────────┤
│  MEMORY          (interface-only: no direct DB)      │
├─────────────────────────────────────────────────────┤
│  DOMAIN          (no dependencies — the core)       │
└─────────────────────────────────────────────────────┘
```

### Component Breakdown

#### 1. Domain (No dependencies)

The core business logic — initiative hierarchy, work items, gate definitions. This layer knows nothing about persistence, scheduling, or infrastructure.

**Contains:**
- `hierarchy/` — Portfolio, program, project, workstream, sprint, backlog, task, subtask models
- `governance/` — Gate definitions (scope, budget, staffing, launch, exception)
- `workitems/` — Core work item types and relationships
- `memory/` — Memory layer interfaces (protocol, not implementation)

**Coupling rule:** Domain must have zero imports from other modules.

#### 2. Memory (Interface-only)

Abstraction layer over storage. Domain code talks to memory via interfaces; implementations are injected.

**Contains:**
- `working/` — In-memory state (dict-like, runtime-only)
- `structured/` — Persistence interface (SQLAlchemy or raw SQL)
- `episodic/` — Event log interface (append-only)
- `semantic/` — Vector store interface (deferred v0.2)
- `procedural/` — Rule engine interface (deferred v0.2)

**Key design:** Memory is accessed through interfaces. No direct database calls in domain logic. This allows swapping SQLite → PostgreSQL without touching domain.

#### 3. Execution (Heartbeat engine)

Agent runtime — heartbeat scheduling, work dispatch, completion reporting.

**Contains:**
- `heartbeat/` — Scheduler (asyncio-based, configurable interval)
- `executor/` — Work item execution (pulls from structured memory, writes to working memory)
- `gates/` — Gate checking before execution

**Execution loop (per heartbeat):**
1. Check assigned work items (structured memory)
2. Check gate status (governance layer)
3. Execute eligible items
4. Update working memory
5. Write episodic log
6. Report completion/failure

#### 4. Governance (Approval enforcement)

Gate logic, audit records, cost tracking. Depends on domain + memory.

**Contains:**
- `approvals/` — Gate workflow (pending → approved/rejected)
- `audit/` — Immutable record creation (hash-chain integrity)
- `cost/` — Cost tracking per work item

#### 5. Infrastructure (Pluggable)

Platform concerns — database, messaging, configuration.

**Contains:**
- `persistence/` — SQLite/PostgreSQL adapter
- `messaging/` — Redis Pub/Sub adapter (deferred)
- `config/` — YAML + environment variable loader

### Data Flow

```
Human creates initiative hierarchy
    ↓
Structured Memory (SQLite) persists entities
    ↓
Agent heartbeat → checks structured memory for assigned work
    ↓
Agent → checks gate status (governance)
    ↓
Agent → executes within bounds
    ↓
Working Memory (runtime) tracks in-flight context
    ↓
Heartbeat record → Episodic Memory (append-only log)
    ↓
Gate triggered → Human approves via REST API
    ↓
Gate record → Episodic Memory (immutable)
```

### State Management

**Operational state** (exact queries, SQLite):
- Initiative hierarchy entities
- Gate records and approval states
- Cost records
- Agent registrations

**Semantic state** (similarity queries, vector):
- Embedded initiative roots
- Embedded scope change descriptions
- Embedded gate decision notes

**Runtime state** (in-memory, not persisted):
- Current task context per agent
- Active reasoning state
- Subtask decomposition

**Audit state** (immutable log):
- Heartbeat records
- Gate decisions
- Cost snapshots
- Scope/budget changes

### Build Order

Dependencies between components:

```
Phase 1: Domain models (hierarchy + work items)
    ↓
Phase 2: Memory layers (structured + working)
    ↓
Phase 3: Execution engine (heartbeat)
    ↓
Phase 4: Governance (gates + audit)
    ↓
Phase 5: Infrastructure (SQLite, config)
    ↓
Phase 6: API + Dashboard
```

### Module Coupling Rules

| Module | Can import |
|--------|-----------|
| domain | Nothing (pure) |
| memory | domain (interfaces only) |
| execution | domain, memory, governance |
| governance | domain, memory |
| infrastructure | Everything (implements interfaces) |

### Key Architectural Tensions

**1. Heartbeat vs Event-driven**
Decision: Heartbeat. Event-driven systems (Kafka, webhooks) have ordering problems under load. Heartbeat is predictable and debuggable. Tradeoff: slightly higher latency (30s vs immediate), but guaranteed observability.

**2. Single module vs microservices**
Decision: Single module for MVP. Decompose only when team size demands it. Keep the codebase simple until there's evidence of scale pressure.

**3. SQLite vs PostgreSQL from day one**
Decision: SQLite for MVP, PostgreSQL for production. Don't add PostgreSQL overhead until the relational model is proven. Migration path is clear (SQLAlchemy makes it trivial).

**4. Vector store now vs later**
Decision: Defer vector store to v0.2. Semantic memory is not used in MVP (structured content is indexed but not semantically queried). Infrastructure can be in place without population.

## Confidence

- Layered architecture: **High** — standard pattern, validated by existing architecture doc
- Heartbeat over event-driven: **High** — deliberate tradeoff documented
- SQLite MVP → PG production: **High** — standard practice
- Single module for MVP: **High** — correct for open-source project with small team