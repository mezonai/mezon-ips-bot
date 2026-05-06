FROM python:3.13-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy project metadata, then install deps
COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev

# Copy app code
COPY . .

# Make sure the app venv is on PATH
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["python", "run.py", "--host", "0.0.0.0", "--port", "8000"]
