FROM ghcr.io/astral-sh/uv:debian-slim

WORKDIR /app

COPY pyproject.toml .
COPY uv.lock .
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates
RUN uv sync --locked --link-mode=copy
RUN uv python install 3.13
COPY . .

CMD ["uv", "run", "python", "axiom.py"]
