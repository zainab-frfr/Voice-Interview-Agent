FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app
COPY . .

# Sync dependencies with uv
RUN uv sync --frozen

# Run the agent
CMD ["uv", "run", "agent.py", "dev"]