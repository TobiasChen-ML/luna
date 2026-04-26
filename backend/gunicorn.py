"""Gunicorn config for the Roxy backend.

Usage:
    gunicorn -c gunicorn.py app.main:app
"""

from __future__ import annotations

import os

bind = f"{os.getenv('HOST', '0.0.0.0')}:{os.getenv('PORT', '8999')}"
workers = int(os.getenv('WEB_CONCURRENCY', '3'))
threads = int(os.getenv('WEB_THREADS', '7'))
worker_class = "uvicorn.workers.UvicornWorker"
loglevel = os.getenv('LOG_LEVEL', 'info')
forwarded_allow_ips = os.getenv('FORWARDED_ALLOW_IPS', '*')
accesslog = '-'
errorlog = '-'
