# ============================
# Builder Image (Dependencies)
# ============================
FROM astral/uv:python3.14-bookworm AS builder

ENV UV_LINK_MODE=copy \
    UV_FROZEN=True \
    UV_COMPILE_BYTECODE=True \
    UV_NO_MANAGED_PYTHON=True \
    UV_PYTHON_DOWNLOADS=never \
    VIRTUAL_ENV=/opt/venv \
    UV_CACHE_DIR=/root/.cache/uv

WORKDIR /builder
COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv venv ${VIRTUAL_ENV} && \
    uv sync --active --no-default-groups --no-install-project --extra postgres

COPY src ./src/
COPY README.md ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --no-deps .

# ==========
# Base image
# ==========
FROM python:3.14-slim AS base

ARG UID=1000 GID=1000

ENV VIRTUAL_ENV=/opt/venv \
    PYTHONUNBUFFERED=1
ENV PATH="${VIRTUAL_ENV}/bin:$PATH"

WORKDIR /app

RUN groupadd --gid ${GID} appgroup && \
    useradd --create-home --uid ${UID} --gid ${GID} --home-dir /home/appuser appuser && \
    chown -R appuser:appgroup /app

# ================
# Production image
# ================
FROM base AS production

# Copy pre-built dependencies
COPY --from=builder --chown=appuser:appgroup /opt/venv ${VIRTUAL_ENV}

# No need for src folder, it's already in venv
COPY --chown=appuser:appgroup ./static ./static/
COPY --chown=appuser:appgroup ./alembic ./alembic/
COPY --chown=appuser:appgroup README.md pyproject.toml ./

USER appuser

ENV APP_HOST=0.0.0.0 \
    APP_PORT=8000
EXPOSE 8000

ENV APP_RELOAD="False" \
    APP_STATICFILES="/app/static/" \
    APP_GRACEFULSHUTDOWNTIMEOUT="10" \
    APP_LOGGINGFORMAT="structured" \
    APP_DEBUG="False"

ENV APP_DB_DIALECT="" \
    APP_DB_DRIVER="" \
    APP_DB_ECHO="False" \
    APP_DB_CHECKSCHEMA="True"

CMD ["server"]
