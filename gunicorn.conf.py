"""
gunicorn.conf.py - Fresh Picks: Gunicorn Configuration
"""
import os
import multiprocessing

# Server socket
bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"
backlog = 2048

# Worker processes
workers = 2
worker_class = "gthread"
threads = 4
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50

# Timeout
timeout = 120
graceful_timeout = 30
keepalive = 5

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Process naming
proc_name = "freshpicks"

# Server hooks
def on_starting(server):
    server.log.info("FreshPicks starting up (Gunicorn %s workers)", workers)

def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def pre_exec(server):
    server.log.info("Forked child, re-executing.")

def when_ready(server):
    server.log.info("Server is ready. Accepting connections.")

def worker_int(worker):
    worker.log.info("Worker received interrupt signal.")
