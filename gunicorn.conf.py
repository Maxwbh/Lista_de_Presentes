"""
Configuração do Gunicorn otimizada para Render Free Tier (512MB RAM)
"""
import os

# Bind
bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"

# Workers
# Free Tier (512MB): 1 worker gthread + threads
# Starter+ (2GB+): workers = (2 x CPU cores) + 1
workers = int(os.environ.get('WEB_CONCURRENCY', 1))

# gthread: threads compartilham memória do worker — ideal para apps
# I/O-bound (chamadas a IA, scraping, banco remoto) em pouca RAM.
# Com 'sync' o worker atende 1 request por vez e as threads são ignoradas.
worker_class = 'gthread'
threads = int(os.environ.get('GUNICORN_THREADS', 4))

# Heartbeat em memória compartilhada em vez de disco.
# Em containers, /tmp em disco lento causa falsos timeouts de worker.
worker_tmp_dir = '/dev/shm'

# Timeout
timeout = int(os.environ.get('GUNICORN_TIMEOUT', 120))

# Keep-alive alto: atrás do proxy do Render, conexões reaproveitadas
# pelo load balancer não devem ser fechadas pelo gunicorn antes do proxy.
keepalive = 65

# Max requests antes de reiniciar worker (previne memory leaks)
max_requests = int(os.environ.get('MAX_REQUESTS', 1000))
max_requests_jitter = 50

# Logging
loglevel = 'info'
accesslog = '-'  # stdout
errorlog = '-'   # stderr
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Preload app: carrega o Django antes do fork — economiza memória
preload_app = True

# Graceful timeout
graceful_timeout = 30

# Process naming
proc_name = 'lista_presentes'


def on_starting(server):
    print("=" * 60)
    print("Lista de Presentes - Iniciando servidor")
    print(f"Workers: {workers} ({worker_class}) | Threads: {threads}")
    print(f"Timeout: {timeout}s | Keep-alive: {keepalive}s")
    print(f"Max Requests: {max_requests}")
    print("=" * 60)


def worker_int(worker):
    print(f"Worker {worker.pid} recebeu sinal de interrupção")


def on_exit(server):
    print("Lista de Presentes - Encerrando servidor")
