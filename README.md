# EthosOS

**An initiative-based operating system for human-agent organizations.**

Stop managing tickets. Start leading initiatives.

---

## The Problem

Ticket-based systems are built for IT problem tracking. They create a culture of "file a ticket" — tasks without context, status theater instead of outcomes, and work that exists in isolation from strategy.

When a company launches a SaaS product, that's a project. When it hires a founding engineer, that's a project. When it builds the product, sprints and backlog come from the PRD — not from tickets floating in from nowhere.

**The hierarchy should mirror how companies actually run, not how IT helpdesks operate.**

## The Solution

EthosOS is project-first, PMO-style. Everything traces upward from a board-approved PRD.

```
Company (Portfolio)
  └── Product (Program)
        └── SaaS Launch (Project + PRD)
              └── Sprint 1
                    └── Backlog (from PRD, not tickets)
                          └── Task → Subtask
```

No orphan tickets. No "create a ticket" as primitive. Every task derives from a board-approved scope.

## Key Concepts

### Board-Approved PRD

Before a project has sprints, it has a PRD. The board reviews scope. Scope gets approved. Then sprints happen. This mirrors real PMO intake — no sprints without board-approved scope.

## Key Concepts

### Initiative Hierarchy

Purpose flows down, context flows up. A portfolio contains programs. A program contains projects. A project contains workstreams. Each level is a container for the next, with clear ownership and approval gates.

### Approval Gates

Human judgment is expensive. Make it deliberate. Gates are explicit checkpoints where human sign-off is required before work continues. Agents can execute freely between gates. No surprises, no runaway autonomy.

### Heartbeat Execution

Agents don't wait to be assigned. They run on a heartbeat — a loop that pulls from the current sprint, executes what's ready, and reports back. Humans don't micromanage. They review. They approve. They course-correct.

### Memory Layers

Five layers, each with a purpose. Vector-first for token efficiency:

| Layer | Purpose | Storage |
|---|---|---|
| **Semantic** | Long-term memory, big context | Vector store (Qdrant) |
| **Procedural** | How things get done | Vector-backed templates |
| **Episodic** | What happened and when | Append-only log |
| **Structured** | Entities, state, approvals | SQLite/PostgreSQL |
| **Working** | Current sprint, runtime | In-memory |

PRD chunks, architecture docs, meeting notes go into vector store — they never hit context limits. Exact state (gate status, sprint data) stays in SQLite.

## Architecture

EthosOS is built as a lightweight, open-source core with a minimal dependency footprint. The system organizes work through the initiative hierarchy, routes execution through agent heartbeats, and enforces governance through approval gates. Memory layers operate independently but share a common query interface.

```
src/
  core/           Initiative tree, hierarchy management, gate logic
  memory/         Five-layer memory system
  heartbeat/      Agent execution loop, task dispatch
  storage/        Persistent state, structured + episodic
  vector/         Semantic search layer (semantic memory only)
  api/            Control plane for humans and agents
```

## Getting Started

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (package manager)

### Local Development

```bash
# Install dependencies
uv sync

# Copy environment config
cp .env.example .env

# Run migrations
alembic upgrade head

# Seed sample data (optional)
python seed.py

# Start the server
python -m ethos_os.main
```

The API will be available at `http://localhost:8000`. OpenAPI docs at `http://localhost:8000/docs`.

### Docker

```bash
# Using Docker Compose
docker-compose up --build
```

### Running Tests

```bash
pytest
```

### Code Quality

```bash
# Lint
ruff check ethos_os tests

# Format
ruff format ethos_os tests
```

## Ontology

All terminology, principles, and entity definitions live in [`docs/ONTOLOGY.md`](./docs/ONTOLOGY.md). This is the single source of truth — all design decisions and code artifacts trace back to it.

Watch this space — or better yet, help build it.

## Contributing

Roadmap and contribution guidelines live in [`plans/`](./plans/). If you're interested in shaping what this becomes, that's where to look.

## License

MIT