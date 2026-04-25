# PRD: EthosOS — Initiative Operating System for Human-Agent Organizations

**Status**: Draft
**Author**: Alex (Product Manager)
**Version**: 0.1
**Last Updated**: 2026-04-24

---

## 1. Vision & Principles

### Vision
EthosOS is an open-source initiative OS that reclaims agency for human teams in an AI-augmented world. It inverts the prevailing ticket-first paradigm: work begins with intent, not task. Agents execute with heartbeat-based autonomy; humans govern through explicit approval gates at the boundaries that matter — scope, budget, staffing, launch, and exceptions. The system treats memory as a layered concern, distinguishing what agents need in the moment from what organizations need to remember.

### Principles

1. **Initiative-first, always.** Every piece of work traces back to a stated intent. Tickets are derived, not primitive. If you cannot articulate why, you have not earned the right to a ticket.

2. **Heartbeat over polling.** Agents operate on predictable intervals, not event-driven chaos. A heartbeat-based execution model ensures observability without instrumentation overhead.

3. **Govern at the edges.** Process overhead scales inversely with trust. Heavy process is a symptom of weak governance. Humans approve at boundaries; agents execute within them.

4. **Memory is a tiered concern.** Not all memory is equal. Working memory is runtime; structured memory is state; episodic memory is recall; semantic memory is learned meaning. Retrieval is optimized by layer.

5. **Exact state is not semantic.** Vector retrieval answers "what's related?" — not "what's the current status?" The database of record is structural; embeddings are a lookup layer, not a source of truth.

---

## 2. MVP Definition

EthosOS v0.1 delivers a functional core that demonstrates the initiative-first paradigm with basic governance. It is not a full product — it is a proof of concept that validates the hierarchy, approval gates, heartbeat execution, and layered memory model.

**v0.1 scope**: A single-organization, single-agent deployment that supports:
- Creating portfolios, programs, and projects with traceable initiative roots
- A two-layer approval gate (scope change, budget change) with human-in-the-loop
- Heartbeat-based agent polling with basic execution logging
- Working memory + structured memory with semantic vector lookup for recall
- A read-only dashboard showing initiative hierarchy and execution heartbeat

**What v0.1 is NOT**: Multi-tenant, multi-agent, production-grade security, full audit trails, mobile UI, API-first, or a replaceable storage layer.

---

## 3. Core Features

### Feature 1: Initiative Hierarchy

- **Description**: A nested structure where every work item traces to a portfolio → program → project relationship. Projects contain workstreams; workstreams contain sprints; sprints pull from a prioritized backlog; backlog items decompose into tasks.
- **Justification** : Without hierarchy, there is no governance. This is the foundational structure on which all approval gates depend. No hierarchy = noEthosOS.

### Feature 2: Initiative Root

- **Description**: Every project carries a stated initiative — a one-paragraph articulation of intent, success metric, and boundaries. Child items inherit or reference this root.
- **Justification** : The initiative-first principle cannot be enforced without a traceable root. This is the answer to "why are we doing this?" that lives with the work, not in a document that nobody reads.

### Feature 3: Approval Gates (Scope & Budget)

- **Description**: A configurable gate that halts execution when scope or budget exceeds a defined threshold. Requires human approval via a simple accept/reject action in the UI.
- **Justification** : This is the minimal governance layer. Agents must not expand scope or burn budget without human consent. This feature tests the gate model without implementing the full approval workflow.

### Feature 4: Heartbeat Execution Engine

- **Description**: A scheduled execution model where agents poll on a configurable interval (default: 30 seconds). Each poll records a heartbeat event with timestamp, agent ID, and a simple status (idle, working, blocked, complete). Logs are stored in structured memory.
- **Justification** : Event-driven execution with webhooks is fragile in agentic contexts. Heartbeats provide a predictable, debuggable execution model that requires no instrumentation. This is the execution backbone.

### Feature 5: Layered Memory — Working + Structured

- **Description**: Working memory holds active context per agent session (in-memory, non-persistent). Structured memory persists the hierarchy, approval states, and execution logs. Semantic layer provides vector-based recall (deferred to v0.2 — vector index is set up but not populated in v0.1 MVP).
- **Justification** : Full layered memory (episodic, semantic, procedural) is a v1+ feature. v0.1 validates the tiering model with the two layers that matter most: runtime working state and persistent structured state.

### Feature 6: Semantic Recall (Vector Lookup)

- **Description**: A vector index over structured memory that supports similarity search. "Show me similar scope change requests" returns ranked results by semantic similarity.
- **Justification** : This is the proof-of-concept for semantic recall. It demonstrates that vector retrieval complements (does not replace) structured query. Exact state queries remain SQL/structural; related-concept queries use vectors.

---

## 4. What is NOT in MVP

| Feature | Why Deferred | Revisit Condition |
|---------|-------------|-------------------|
| **Staffing approval gate** | Requires user/org modeling, role definitions, and team dynamics. Scope+budget gates validate the pattern first. | After v0.1 proves approval model works |
| **Launch approval gate** | Requires a defined "launch" state, notification system, and rollback handling. Not needed to validate core execution. | When feature rollout workflow is scoped |
| **Procedural memory layer** | Requires a learning system, habit formation, and feedback loops. Not needed to ship v0.1. | After episodic memory patterns stabilize |
| **Episodic memory (full)** | Full event sourcing with replay is architectural complexity. v0.1 stores heartbeat logs, not replayable events. | When audit/replay requirements are explicit |
| **Multi-agent coordination** | Adds concurrency, race condition, and orchestration complexity. Single-agent validates baseline. | When multi-agent scenarios are prioritized |
| **Mobile UI** | Dashboard access via browser is sufficient for v0.1. Mobile adds authentication and responsive complexity. | After core UX is validated |
| **API-first architecture** | Internal API is sufficient for v0.1. External API design requires a clearer consumer model. | When third-party integrations are requested |

---

## 5. User Stories

### Story 1: Creating a Portfolio
> As a **founder**, I want to create a portfolio with a stated strategic intent so that my team understands the "why" behind every program.

**Acceptance Criteria**:
- [ ] Given I am logged in, when I create a portfolio, then I must provide a name and a strategic intent paragraph (minimum 50 characters)
- [ ] Given the portfolio exists, when I view it, then I see the intent, created date, and list of programs contained

### Story 2: Requesting a Scope Change
> As an **agent**, I want to request scope approval when my task exceeds the original estimate so that my human overseer can consent before I proceed.

**Acceptance Criteria**:
- [ ] Given I am an agent with a task, when the estimated effort exceeds the threshold (+25% of original), then the system auto-creates a scope change request
- [ ] Given a scope change request exists, when my human views it, then they can accept or reject with an optional note
- [ ] Given rejection, when I receive it, then my task is blocked until re-planned

### Story 3: Agent Heartbeat
> As an **agent**, I want to record a heartbeat each cycle so that my overseer can see I am alive and making progress.

**Acceptance Criteria**:
- [ ] Given I am a registered agent, when my heartbeat interval passes, then the system records: timestamp, status, task ID (if any), and a one-line progress note
- [ ] Given multiple heartbeats exist, when my human views the timeline, then they see a chronological sequence with states

### Story 4: Semantic Recall
> As a **program lead**, I want to find similar scope change requests so that I can apply consistent precedent.

**Acceptance Criteria**:
- [ ] Given I am in the scope change list, when I click "find similar", then the system returns the top 5 semantically similar requests (ranked by vector similarity)
- [ ] Given results, when I select one, then I can view its full context, outcome, and human notes

### Story 5: Viewing Initiative Hierarchy
> As a **stakeholder**, I want to see the full initiative structure so that I understand where my decision fits.

**Acceptance Criteria**:
- [ ] Given I have view access, when I open the dashboard, then I see: portfolio → program → project → workstream → sprint → backlog as a nested tree
- [ ] Given any node, when I click it, then I see its initiative root, approval state, and key metrics (budget, progress)

---

## 6. Success Metrics

| Goal | Metric | Target | Measurement Window |
|------|--------|--------|-------------------|
| **Validate hierarchy adoption** | % of projects with a stated initiative root | ≥ 80% within 30 days | 30 days post-launch |
| **Validate approval gates** | Scope change requests processed within 24 hours | ≤ 24 hours | 30 days post-launch |
| **Validate heartbeat execution** | Agents recording heartbeats on schedule | ≥ 95% uptime | 14 days of runtime |
| **Validate semantic recall** | Semantic search returns relevant results (manual eval) | ≥ 70% relevance rating | 30 days post-launch |
| **Validate operational baseline** | System uptime | ≥ 99% | 90 days post-launch |
| **Validate user retention** | Dashboard sessions per user per week | ≥ 2 sessions/week | 30 days post-launch |

---

## 7. Open Questions

### Question 1: Approval Gate Thresholds
**What threshold values** for scope (+25%? +50%?) and budget (+$? %?) trigger the approval gate? Default patterns must be validated with early users.

**Owner**: Product — **Deadline**: Prior to development start

### Question 2: Heartbeat Intervals
**What is the optimal heartbeat interval** for agent execution? 60 seconds is an assumption. 10 seconds may be noisy; 5 minutes may miss failure detection.

**Owner**: Engineering spike — **Deadline**: Development Week 2

### Question 3: Vector Retrieval Scope
**What content should be vector-indexed in v0.1**? Full text of initiative roots? Scope change descriptions? All structured fields? Over-indexing degrades recall precision.

**Owner**: Engineering — **Deadline**: Development Week 1

### Question 4: Persistence Strategy
**What database/backend** stores structured memory in v0.1?** SQLite for simplicity? PostgreSQL for durability? This affects deployment model and onboarding.

**Owner**: Architecture — **Deadline**: Development Week 1

### Question 5: Deployment Model
**How is EthosOS v0.1 distributed?** Docker? Binary? Cloud-hosted SaaS? The open-source distribution model affects community adoption and contribution.

**Owner**: Product + Engineering — **Deadline**: Prior to alpha

---

## Appendix

- **v0.1 Engineering Estimate**: 6–8 weeks (2–3 engineers)
- **Target Users**: Early adopter teams running human-agent organizations, 10–100 person teams
- **Success Confidence**: Medium — hierarchy and heartbeat are validated patterns; layered memory and semantic recall carry higher uncertainty
- **Kill Criteria**: If approval gates show zero usage within 30 days OR heartbeat uptime drops below 80%, reassess the core hypothesis before continuing