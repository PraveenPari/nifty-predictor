# Nifty Predictor Pro — production image (slim deps, non-root, healthcheck)
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    FLASK_ENV=production \
    PORT=5000

WORKDIR /app

# curl for the docker HEALTHCHECK only
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# Non-root runtime user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -fsS http://127.0.0.1:${PORT}/healthz || exit 1

CMD ["gunicorn", "-c", "gunicorn.conf.py", "app:app"]
