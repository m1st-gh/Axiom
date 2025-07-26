FROM alpine:3.14

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin 

WORKDIR /app

# Environment variables for uv
ENV UV_LINK_MODE copy 
ENV UV_COMPILE_BYTECODE 1 

COPY pyproject.toml uv.lock ./

RUN uv python install 3.13
RUN uv sync --locked --link-mode=copy

COPY . .

CMD ["uv", "run", "python", "run.py"]
