# Contributing to EthosOS

Welcome! EthosOS is an open-source project for human-agent organization coordination. This guide covers how to set up your development environment and contribute effectively.

## Getting Started

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (package manager)

### Development Setup

```bash
# Clone the repository
git clone https://github.com/voiquyr/ethos-os.git
cd ethos-os

# Install dependencies
uv sync

# Copy environment config
cp .env.example .env

# Run database migrations
alembic upgrade head

# Seed sample data (optional)
python seed.py

# Start the server
python -m ethos_os.main
```

The API will be available at `http://localhost:8000`. OpenAPI docs at `http://localhost:8000/docs`.

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=ethos_os --cov-report=html

# Specific test file
pytest tests/test_api.py
```

### Code Quality

```bash
# Lint
ruff check ethos_os tests

# Format
ruff format ethos_os tests
```

## Project Structure

```
ethos_os/
├── ethos_os/           # Main package
│   ├── api/           # REST API endpoints
│   ├── config.py      # Configuration
│   ├── db.py         # Database setup
│   ├── execution/    # Heartbeat/executor
│   ├── gates/        # Approval gates
│   ├── memory/       # Working memory
│   └── repositories/  # Data access layer
├── docs/              # Architecture & ontology
├── tests/             # Test suite
└── alembic/           # Database migrations
```

## Key Conventions

### Domain Models

- All models in `ethos_os/` use SQLAlchemy 2.0 style (declarative with Mapped column annotations)
- Models must have explicit `__init__` that accepts all fields
- Always include `id`, `created_at`, `updated_at` base fields

### Repository Pattern

- Each domain entity has a corresponding repository in `repositories/`
- Repositories handle all DB access
- No raw SQL in API routes

### API Design

- Use Pydantic for request/response validation
- Return structured error responses (not exceptions)
- All endpoints documented with OpenAPI

### Testing

- Unit tests: `tests/test_*.py`
- Follow Arrange-Act-Assert pattern
- Use fixtures for common setup

## Contribution Workflow

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/your-feature`)
3. **Implement** your change with tests
4. **Run** lint and tests locally
5. **Commit** with a clear message
6. **Push** and open a Pull Request

## Areas to Contribute

- **Core Domain**: New initiative levels, gate types, approval workflows
- **Memory**: Vector store integration, memory layer improvements
- **Execution**: Heartbeat enhancements, failure handling
- **API**: New endpoints, rate limiting, authentication
- **Documentation**: Architecture docs, API reference, examples

## Questions?

- Open an issue for bugs or feature requests
- Discuss in Pull Requests

We welcome all contributions — from bug fixes to new features to documentation improvements.