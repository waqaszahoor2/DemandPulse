FROM python:3.11.9-slim-bookworm

ARG APP_VERSION=0.4.0
ARG VCS_REF=unknown
ARG SOURCE_URL=unknown

LABEL org.opencontainers.image.title="DemandPulse API" \
      org.opencontainers.image.description="Production API and MLflow-enabled retail demand intelligence service" \
      org.opencontainers.image.version="${APP_VERSION}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.source="${SOURCE_URL}" \
      org.opencontainers.image.vendor="DemandPulse"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    APP_ENV=production \
    LOG_LEVEL=INFO \
    MODEL_DIR=/app/models \
    MLFLOW_TRACKING_URI=file:///app/mlruns \
    MLFLOW_EXPERIMENT_NAME=demandpulse-point-forecasting \
    API_HOST=0.0.0.0 \
    API_PORT=8000 \
    PORT=8000

RUN groupadd --system --gid 10001 demandpulse \
    && useradd --system --uid 10001 --gid demandpulse --home-dir /app --shell /usr/sbin/nologin demandpulse

WORKDIR /app

# Install third-party dependencies before copying source to maximize Docker layer reuse.
COPY requirements.txt ./requirements.txt
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY pyproject.toml README.md ./
COPY src ./src
RUN python -m pip install --no-deps --no-cache-dir . \
    && python -m pip freeze | sort > /app/BUILD_DEPENDENCIES.txt \
    && printf '%s\n' \
       "app_version=${APP_VERSION}" \
       "git_commit=${VCS_REF}" \
       "source=${SOURCE_URL}" \
       > /app/BUILD_INFO.txt

# Runtime artifacts only. Research notebooks/reports are intentionally not copied.
COPY models ./models

RUN mkdir -p /app/models /app/mlruns /mlflow \
    && touch /mlflow/.volume-init \
    && chown -R demandpulse:demandpulse /app /mlflow

USER demandpulse

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.environ.get('API_PORT', '8000') + '/health', timeout=3)" || exit 1

CMD ["sh", "-c", "exec uvicorn demandpulse.api.main:app --host ${API_HOST:-0.0.0.0} --port ${PORT:-${API_PORT:-8000}}"]
