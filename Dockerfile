FROM alpine:3.14

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin 

WORKDIR /app
ENV UV_LINK_MODE=copy \
  UV_COMPILE_BYTECODE=1 \
  UV_PYTHON_DOWNLOADS=never \
  UV_PROJECT_ENVIRONMENT=/app

COPY . .
RUN uv sync --locked --link-mode=copy
RUN uv python install 3.13

CMD ["uv", "run", "python", "run.py"]
