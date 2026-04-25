# EthosOS v0.2 — Initiative-Based AI Company OS

**Paperclip meets PMO. Agents execute initiatives. Humans govern at gates.**

EthosOS is an orchestration platform where AI agents (from agency-agents) run a company based on business initiatives. Board (humans) approves direction, agents execute autonomously.

---

## What Paperclip Does

| Feature | What It Is |
|---------|-----------|
| **Org Chart** | Agents have roles, titles, reporting lines |
| **Heartbeats** | Agents wake on schedule, check work, execute |
| **Task System** | Every task traces to company goal |
| **Budgets** | Cost control per agent, hard stops |
| **Governance** | Board approval, pause/terminate agents |
| **Multi-Company** | One deployment, many companies |

---

## What EthosOS Does Differently

| Aspect | Paperclip | EthosOS |
|--------|-----------|---------|
| **Work primitive** | Ticket | Initiative (Portfolio→Project→Sprint→Task) |
| **PM model** | Task-based | PMO-style (no orphan tasks) |
| **Agent source** | Claude Code, OpenClaw, etc. | 147+ agents from agency-agents |
| **Gate system** | Budget hard-stops | Full approval gates (PRD, scope, budget, launch) |
| **Context** | Project context | Initiative hierarchy + vector memory |

---

## EthosOS Architecture

### Entity Hierarchy

```
Portfolio (Company)
├── Program (Business Unit)
│   ├── Project (Initiative)
│   │   ├── PRD (Board-approved scope)
│   │   ├── Sprint (Time box)
│   │   │   ├── Task (Work item)
│   │   │   └── Task → Agent assignment
│   └── Gate (Approval checkpoint)
```

### Agent Hierarchy (from agency-agents)

```
Board (Humans) ← Approves PRDs, gates
    ↑
CEO Agent (@chief-of-staff) ← Strategic planning
    ↓
Project Leads (@project-shepherd, @sprint-prioritizer)
    ↓
Execution Agents (specialized per task)
    ├── @senior-developer → coding tasks
    ├── @content-creator → content tasks
    ├── @sales-outreach → outreach tasks
    ├── @researcher → research tasks
    └── ... (any from 147+ agents)
```

### Workflow

| Step | Actor | Action |
|------|-------|--------|
| 1 | Board (Human) | Sets strategic direction |
| 2 | CEO Agent (@chief-of-staff) | Creates Program/Project from directive |
| 3 | Board (Human) | **PRD Gate** — Approves scope |
| 4 | Project Lead Agent | Breaks into sprints, assigns tasks |
| 5 | Execution Agents | Execute autonomously |
| 6 | **Scope Gate** | Triggers at +25% estimate variance |
| 7 | **Launch Gate** | Board approves completion |

---

## Agent Integration

### Available Agents (from agency-agents)

| Role | Agent | Use Case |
|------|-------|----------|
| **Leadership** | @chief-of-staff, @product-manager | Strategic planning, roadmapping |
| **Execution (Dev)** | @senior-developer, @backend-architect, @frontend-developer | Building features, APIs |
| **Execution (Content)** | @content-creator, @linkedin-content-creator, @twitter-engager | Marketing, docs, social |
| **Execution (Sales)** | @sales-outreach, @outbound-strategist, @discovery-coach | Lead gen, BD, sales |
| **Execution (Research)** | @trend-researcher, @growth-hacker, @analytics-reporter | Market research, analysis |
| **Operations** | @project-shepherd, @sprint-prioritizer, @hr-onboarding | Project management, ops |
| **Governance** | @security-engineer, @compliance-auditor | Security, compliance |
| **Support** | @customer-service, @support-responder | Customer support |
| **Specialized** | 130+ more | Industry-specific tasks |

### Agent Registration

Each agent from agency-agents can be "hired" into EthosOS:
1. Board reviews agent capabilities
2. Board assigns agent to role/team
3. Agent receives heartbeats and executes tasks
4. Board monitors via dashboard, approves at gates

---

## Key Features

### 1. Initiative Hierarchy (PMO-style)
- Every task traces to board-approved PRD
- No orphan tickets
- Clear ownership at each level

### 2. AI Agent Workforce
- CEO Agent orchestrates from agency-agents
- Specialized execution agents per task type
- Agents work autonomously between gates

### 3. Approval Gates
- **PRD Gate** — Board approves project scope
- **Scope Gate** — Triggers at +25% effort variance
- **Budget Gate** — Triggers at +20% cost variance
- **Launch Gate** — Board approves completion

### 4. Heartbeat Execution
- Agents check in every 30s
- Report progress, status, blockers
- Resume work from checkpoint

### 5. Persistent Memory
- **Vector (Qdrant)** — Initiative docs, meeting notes, context
- **SQLite** — Entity state, approvals, audit log
- **Working** — Current sprint runtime

### 6. Chat Interface
- Talk to CEO Agent to set direction
- Chat with any agent about their work
- Real-time updates on execution

### 7. Dashboard
- Initiative tree view
- Agent status panel
- Gate approval board
- Budget tracking

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | FastAPI (existing) + expand |
| **Database** | SQLite (existing) + PostgreSQL ready |
| **Vector** | Qdrant (scaffolded) |
| **Frontend** | React/Next.js (new) |
| **AI** | OpenAI/Anthropic (new) |
| **Agents** | agency-agents (existing) |
| **Orchestration** | Paperclip-style (new) |

---

## Roadmap to v0.2

### Phase A: Agent Integration
- [ ] Import agents from agency-agents
- [ ] Agent registry in EthosOS
- [ ] Agent ↔ Initiative linking

### Phase B: Heartbeat & Execution
- [ ] Agent heartbeat loop
- [ ] Task assignment to agents
- [ ] Progress reporting

### Phase C: Chat UI
- [ ] Paperclip-style chat interface
- [ ] Agent switching
- [ ] Initiative context in chat

### Phase D: Memory & Context
- [ ] Qdrant integration
- [ ] Initiative document chunking
- [ ] Context injection to agents

### Phase E: Dashboard
- [ ] Initiative tree
- [ ] Agent status
- [ ] Gate approvals

---

## Comparison

| Feature | Current v0.1 | v0.2 Target |
|---------|-------------|-------------|
| Initiative hierarchy | ✅ | ✅ |
| Approval gates | ✅ | ✅ |
| Heartbeat framework | ✅ | ✅ |
| AI agents | ❌ | ✅ |
| Chat UI | ❌ | ✅ |
| Agent orchestration | ❌ | ✅ |
| Vector memory | Scaffolded | ✅ |
| Dashboard | API routes only | Full UI |

---

## Philosophy

**Paperclip:** "If it can receive a heartbeat, it's hired."

**EthosOS:** "Every task traces to a board-approved initiative. Agents execute autonomously between gates. Humans govern at boundaries."

---

*EthosOS: Initiative-first AI company orchestration.*
*Built on agency-agents. Governed by humans.*