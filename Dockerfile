FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY ethos_os/ ./ethos_os/
COPY tests/ ./tests/
COPY docs/ ./docs/
COPY alembic/ ./alembic/
COPY seed.py ./
COPY alembic.ini ./
COPY .env.example ./

RUN pip install uv && uv sync --frozen --no-dev

EXPOSE 8000

CMD ["python", "-m", "ethos_os.main"]