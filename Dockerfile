FROM python:3.13-slim AS builder

WORKDIR /build

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy project metadata, then install deps
COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev

# --- Runtime stage ---
FROM python:3.13-slim

WORKDIR /app

# Install system deps needed at runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 && \
    rm -rf /var/lib/apt/lists/*

# Copy venv from builder
COPY --from=builder /build/.venv /app/.venv

# Copy app code
COPY app/ ./app/
COPY run.py alembic.ini ./

ENV PATH="/app/.venv/bin:$PATH"
ENV APP_ENV=prod

EXPOSE 8000

CMD ["python", "run.py", "--host", "0.0.0.0", "--port", "8000"]
