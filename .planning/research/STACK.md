# Stack Research: EthosOS

**Domain:** Initiative-based OS for human-agent organizations
**Date:** 2026-04-24
**Dimension:** Stack

## Question

What's the standard 2025/2026 stack for building initiative-based OS / human-agent coordination systems?

## Findings

### Core Language

**Python 3.11+** is the dominant choice for agentic systems:
- Rich ecosystem for AI/ML integration
- Readable, maintainable for open-source collaboration
- Native async (`asyncio`) for heartbeat scheduling
- FastAPI, LangChain, CrewAI, AutoGen all Python-based

**Go** is viable for high-performance agent runtimes but adds complexity for an open-source project where contributor pool matters. Python wins for ecosystem reach.

**Rust** is overbuilt for an OS that needs to be understood by contributors quickly. Not recommended unless performance profiling proves Python is insufficient.

### API Layer

**FastAPI** — the standard for 2025 agentic backends:
- Open-source (MIT)
- Async-native, matches heartbeat model
- Auto-generated OpenAPI docs (useful for open-source)
- Pydantic for request/response validation
- Starlette foundations, battle-tested at scale

** alternatives:
- Flask: synchronous only, more boilerplate for async
- Django: too heavy for this domain
- gRPC: overkill for MVP, adds consumer complexity

### Persistence

**SQLite (MVP) / PostgreSQL (production)**:
- SQLite: zero-dependency, no setup, relational model matches initiative hierarchy
- PostgreSQL: Supabase, Neon, RDS, Render — all managed options, zero vendor lock-in
- Both open-source, both relational

**Alternatives to avoid:**
- MongoDB: schema-less doesn't fit initiative hierarchy (needs strong relational)
- Redis-only: insufficient for complex queries
- Graph DB (Neo4j): premature unless cross-project dependencies emerge

### Vector Store

**Qdrant** (open-source, self-hosted or cloud):
- Rust-based, high performance
- Rich filtering on metadata
- Active community, strong docs

**Chroma** (Python-native):
- Simpler to embed in MVP
- Single-node only at v0.1

**LanceDB** (emerging, Rust-based):
- Better for time-series/iterative data
- Interesting for episodic memory later

**pgvector** (PostgreSQL extension):
- Eliminates separate vector store dependency
- Ideal if PostgreSQL is already chosen
- Recommend: defer vector store decision to v0.2, use pgvector if Postgres is chosen

### Heartbeat / Scheduling

**asyncio + aioschedule** (Python native):
- No external dependencies
- Full control over heartbeat implementation
- Good for open-source (no lock-in)

**Celery** (overkill for MVP):
- Adds Redis dependency
- Overengineered for simple heartbeat polling
- Useful at v0.2+ for distributed execution

**Temporal** (interesting but complex):
- Workflow engine, not just scheduler
- Adds significant operational overhead
- Consider if multi-agent coordination requires it

### Message Broker

**Redis Pub/Sub** (optional, production):
- Simple, well-understood
- Supabase/Upstash managed options

**In-memory** (MVP):
- Sufficient for single-instance heartbeat
- No dependency overhead
- Scales to distributed later without code changes

### Agent Framework (Optional)

**Do not couple EthosOS to a specific agent framework:**
- Agents are external consumers of EthosOS APIs
- Framework choice is agent-specific, not OS-specific
- EthosOS should work with any agent that speaks REST

If coupling is needed: LangChain or CrewAI as reference implementation only.

### Deployment

**Docker Compose** (MVP):
- Single `docker-compose.yml`
- SQLite + app container
- Easiest path for contributors to run locally

**Fly.io / Railway** (production-ready free tier):
- Both support Docker
- Low friction for open-source projects

**Kubernetes** (deferred):
- Overhead for v0.1/v0.2
- Add when multi-tenant or multi-region needed

## Stack Recommendation

| Component | MVP Choice | Rationale |
|-----------|-----------|-----------|
| Language | Python 3.11+ | Ecosystem, readability, agent-native |
| API | FastAPI | Open-source, async, minimal |
| Database | SQLite (MVP) / PostgreSQL (production) | Relational fits hierarchy, no lock-in |
| Vector | Defer to v0.2 | Not used in MVP semantic layer |
| Scheduling | asyncio | No external dependencies |
| Message | In-memory (MVP) | Simple, defer Redis to scale |
| Auth | JWT (simple) | Sufficient for v0.1 |
| Deployment | Docker Compose | Easiest contributor onboarding |

## Confidence

- Core stack: **High** — standard Python web stack
- Vector store deferral: **High** — correct MVP decision
- asyncio heartbeat: **High** — proven approach

## What NOT to Use

- **Not a graph DB** — premature unless cross-project deps emerge
- **Not a workflow engine (Temporal/Argo)** — complexity cost at v0.1
- **Not a managed platform (Vercel/Netlify)** — open-source projects need self-hosting path
- **Not a NoSQL store** — schema-less doesn't fit initiative hierarchy
- **Not an event-driven broker (Kafka)** — heartbeat model doesn't need it