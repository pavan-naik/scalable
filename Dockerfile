FROM python:3.12-slim AS builder
WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

COPY app/ ./app/
RUN uv sync --frozen --no-dev



FROM python:3.12-slim AS runtime

RUN groupadd --gid 1001 appgroup \
    && useradd --uid 1001 --gid appgroup --shell /bin/bash --create-home appuser

WORKDIR /app

COPY --from=builder /app/.venv ./.venv
COPY --from=builder --chown=appuser:appgroup /app/app ./app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

USER appuser

EXPOSE 8000

ENTRYPOINT ["uvicorn", "app.main:app"]
CMD ["--host", "0.0.0.0", "--port", "8000"]