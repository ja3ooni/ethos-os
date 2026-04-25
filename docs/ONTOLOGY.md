# EthosOS Ontology

**Version:** 0.1
**Purpose:** Single source of truth for terminology, concepts, and principles. Every future document, code artifact, and design decision traces back to this file.

---

## Core Philosophy

> **Project-first, board-approved.** Work begins with a PRD and board approval. Tickets are derived from PRDs, not the other way around.

EthosOS mirrors PMO workflows — how companies actually run:

| PMO Anti-Pattern | EthosOS Model |
|---|---|
| "File a ticket" as primitive | Create a project with board-approved PRD first |
| Orphan tickets with no context | Every task traces to a project with an approved scope |
| Status theater instead of outcomes | Outcome + initiative trace, not status |
| Volume of tickets as productivity | Coherence of projects with board-approved scope |
| Sprints without scope approval | No sprints without board-approved PRD |
| Backlog from nowhere | Backlog items derived from PRD scope |
| Kanban boards for ticket chaos | Kanban boards for project sprint state |

EthosOS rejects the IT helpdesk model. A company launching a SaaS product is a project. Hiring a founding engineer is a project. Every sprint, backlog item, and task traces back to a board-approved scope — not to a ticket filed in isolation.

---

## Primitive Entities

These are the primitive building blocks. Everything else is composed from them.

### Portfolio

The apex of the hierarchy. A portfolio represents the company or strategic entity.

- **Has:** Name, strategic intent, success metric, owner
- **Contains:** Programs (product lines, business units)
- **Human role:** Board-level approval; set strategic direction
- **Agent role:** None at this level
- **Gate:** Creation requires board approval

### Program

A cross-program coordination unit. Programs group related projects.

- **Has:** Name, alignment statement, owner
- **Contains:** Projects
- **Human role:** Approve resources; monitor cross-project health
- **Agent role:** None at this level
- **Gate:** Resource commitment requires PMO approval

### Project

A deliverable with a board-approved PRD. Projects are where work gets real — they must have a PRD before they have sprints.

- **Has:** PRD (intent + success metric + scope + boundaries + timeline), owner, budget
- **Contains:** Sprints
- **Human role:** PMO approves PRD scope at intake; approve scope/budget changes
- **Agent role:** Execute within board-approved bounds
- **Gate:** Scope and budget are board-controlled. No sprints without board-approved PRD.

### PRD (Product Requirements Document)

The primitive intake artifact. Before any project spawns sprints, it has a board-reviewed PRD.

- **Has:** Intent, success metric, scope, boundaries, timeline, budget, owner
- **Human role:** Board/PMO reviews and approves scope
- **Agent role:** Reads and decomposes PRD into backlog items
- **Gate:** Intake gate — must be board-approved before project activates sprints

### Sprint

A time-boxed iteration within a workstream. Sprints have a start, end, and goal.

- **Has:** Goal, start date, end date, capacity
- **Contains:** Backlog (pull model)
- **Human role:** Approve exceptions
- **Agent role:** Execute assigned work
- **Gate:** Exception triggers gate

### Backlog

A prioritized list of work items pulled into a sprint. Backlog items are derived from the board-approved PRD, not from orphan tickets.

- **Has:** Ordered list of tasks, prioritization rationale, PRD reference
- **Human role:** Prioritize; deprioritize
- **Agent role:** Recommend reorder based on effort/speed
- **No gate:** Backlog operations are collaborative, not gate-controlled
- **Rule:** No backlog item without a PRD reference. Orphan tickets don't exist.

### Task

An atomic unit of work derived from a board-approved PRD. A task is the smallest unit with a defined outcome and an assigned agent.

- **Has:** Description, effort estimate, assignee, status, outcome
- **Inherits:** Full lineage: sprint → project → program → portfolio (plus PRD reference)
- **Human role:** Review outcome
- **Agent role:** Execute autonomously within board-approved scope
- **Gate:** Scope expansion triggers approval

### Subtask

Implementation detail decomposed from a task by an agent. Subtasks are agent-tracked, not human-tracked.

- **Has:** Brief description, effort estimate
- **Human role:** None (informational only)
- **Agent role:** Execute autonomously; report to task-level

---

## Governance Primitives

### PRD (Governance Context)

The board-approved PRD is the governance artifact. It is the answer to "why does this project exist?"

The PRD is not just documentation — it is the gate artifact. The board reviews it. The board approves scope. Then sprints happen.

PRD approval → intake gate opens → sprints can spawn → backlog items derive from PRD scope.

### Approval Gate

A checkpoint where human sign-off is required before work continues. Gates are binary: approved or not.

| Gate | Trigger | Approver | Timeout |
|---|---|---|---|
| Scope | Task exceeds estimate by threshold | Project lead | 48h |
| Budget | Spend exceeds estimate by threshold | Finance | 24h |
| Staffing | Agent assigned to workstream | Program lead | 24h |
| Launch | Project/program goes live | Portfolio lead | 72h |
| Exception | Override of standard flow | Varies | 24h |

Gates are structural, not procedural. If the hierarchy exists, gates are applied.

### Gate Request

An artifact created when a gate is triggered. A gate request carries:
- What is being approved
- Who is requesting
- When it was requested
- Current state (pending / approved / rejected)
- Decision and notes (if decided)
- Decision timestamp and decider

### Cost Record

Every work item carries cost information:
- Estimated cost at assignment
- Actual cost at completion
- Variance percentage

Cost is tracked at agent-hour level. Daily aggregation is sufficient for MVP.

---

## Execution Primitives

### Heartbeat

A periodic signal from an agent indicating status. Heartbeats are the execution backbone — predictable, debuggable, observable.

A heartbeat record:
- Timestamp
- Agent ID
- Status: `idle` | `working` | `blocked` | `complete`
- Task ID (if working)
- Progress note (one line, optional)

Heartbeat interval is configurable per agent type. Default: 30 seconds.

### Executor

An agent that pulls from the backlog, executes eligible tasks, and reports via heartbeat. Executors operate within initiative bounds — they cannot expand scope or consume budget without gate approval.

Executor loop per heartbeat:
1. Check assigned tasks (structured memory)
2. Check gate status (governance layer)
3. Execute eligible items
4. Update working memory
5. Write episodic log
6. Report completion/failure

### Semantic Memory

**Primary long-term memory.** Vector embeddings of large context chunks — PRD content, architecture docs, meeting notes, decision rationale. This is the token-efficiency play: big chunks never hit context windows.

Contains:
- Embedded PRD content
- Embedded architecture docs
- Embedded meeting notes
- Embedded decision rationale

Semantic memory is vector-primary. Not optional — it's the main storage for everything that doesn't fit in a context window.

### Procedural Memory

Templates and rules for how things get done. Vector-backed for pattern matching against large instruction sets.

Contains:
- Approval workflow templates
- Variance request procedures
- Exception escalation paths

### Working Memory

Per-agent, in-flight context. Runtime-only — not persistent across restarts.

Contains:
- Current task context
- Active reasoning state
- Subtask decomposition
- Short-term references

### Structured Memory

Authoritative state only. Exact key lookup, not similarity. Small and fast.

Contains:
- Project hierarchy (portfolios, programs, projects, sprints, tasks)
- PRD records and approval states
- Gate records and approval states
- Cost records
- Agent registrations

### Episodic Memory

Immutable event log. What happened, when. Append-only with hash chain integrity.

Contains:
- Heartbeat records
- Gate decisions
- Cost snapshots
- Scope/budget changes

Not replayed in MVP (deferred to v0.2+).

---

## Anti-Patterns

These patterns are explicitly rejected by EthosOS:

### "Just create a ticket"

Rejected. Every task must derive from a board-approved PRD. No orphan tickets. No "create a ticket" as primitive operation.

### Ticket Creep

Rejected. Tasks without PRD references. Backlog items without scope. "File a ticket" as primitive. EthosOS tracks projects with board-approved scope — not orphan tickets with no context.

### Kanban for Ticket Chaos

Rejected. Kanban boards showing ticket chaos — hundreds of tickets from nowhere, no shared scope, no initiative trace. EthosOS Kanban shows sprint state for a project with a board-approved PRD. Same board, same columns, but every card traces to an approved scope.

### Bloat and Overthinking

Rejected. EthosOS runs lean. No bloated workflows. No overengineered process. No "just in case" features. Prompt engineering must be airtight, memory must be vector-based for token efficiency, but the system itself is minimal.

---

## Naming Conventions

For code and documents:

| Concept | Naming pattern | Example |
|---|---|---|
| Entity | `initiative` | `initiative_root`, `initiative_hierarchy` |
| Gates | `gate_` + noun | `gate_scope`, `gate_budget` |
| Memory layers | `memory_` + layer | `memory_working`, `memory_structured` |
| Records | `_record` | `heartbeat_record`, `gate_record` |
| Modules | `domain`, `governance`, `memory`, `execution`, `infrastructure` | |

---

*This ontology is the contract. If a design decision conflicts with it, the ontology wins — or the ontology is updated explicitly. No drift.*