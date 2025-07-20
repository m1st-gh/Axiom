FROM alpine:3.14

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin 

WORKDIR /app
ENV UV_LINK_MODE=copy \
  UV_COMPILE_BYTECODE=1 

COPY . .
RUN uv python install 3.13
RUN uv sync --locked --link-mode=copy

CMD ["uv", "run", "python", "run.py"]
