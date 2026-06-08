FROM python:3.13-slim AS builder

WORKDIR /app
RUN pip install uv

COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev

FROM python:3.13-slim AS production

WORKDIR /app
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/pyproject.toml /app/pyproject.toml

# Copy source code
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini ./alembic.ini

# Make uv available
RUN pip install uv

EXPOSE 9000

CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "9000"]
