FROM python:3.12

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /application

# Copy project files (excluding .venv)
COPY pyproject.toml uv.lock ./
COPY api/ ./api/
COPY manage.py ./
COPY Makefile ./

# Install dependencies in container's own virtual environment
RUN uv sync --frozen

# Set environment variable to use uv's virtual environment
ENV PATH="/application/.venv/bin:$PATH"
