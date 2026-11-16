"""Gunicorn config tuned for free-tier hosts (512MB RAM)."""
import os

bind = f"0.0.0.0:{os.getenv('PORT', '5000')}"
workers = int(os.getenv("GUNICORN_WORKERS", "1"))
worker_class = os.getenv("GUNICORN_WORKER_CLASS", "gthread")
threads = int(os.getenv("GUNICORN_THREADS", "4"))
timeout = int(os.getenv("GUNICORN_TIMEOUT", "120"))
graceful_timeout = 30
keepalive = 5

preload_app = False  # each worker boots its own ML state cleanly
max_requests = 500   # recycle workers to bound memory on tiny dynos
max_requests_jitter = 50

accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info")
