"""
Configuração do Gunicorn otimizada para Render Free Tier
"""
import multiprocessing
import os

# Bind
bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"

# Workers
# Free Tier (512MB): 1 worker + threads
# Starter+ (2GB+): workers = (2 x CPU cores) + 1
workers = int(os.environ.get('WEB_CONCURRENCY', 1))

# Threads por worker
# Free: 2-4 threads, Starter+: 2-4 threads
threads = 2

# Worker class
worker_class = 'sync'  # ou 'gthread' para threads

# Timeout
timeout = int(os.environ.get('GUNICORN_TIMEOUT', 120))

# Worker connections (para worker async)
# worker_connections = 1000

# Max requests antes de reiniciar worker
# Previne memory leaks
max_requests = int(os.environ.get('MAX_REQUESTS', 1000))
max_requests_jitter = 50

# Logging
loglevel = 'info'
accesslog = '-'  # stdout
errorlog = '-'   # stderr
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Preload app (pode economizar memória)
preload_app = True

# Graceful timeout
graceful_timeout = 30

# Keep alive
keepalive = 5

# Process naming
proc_name = 'lista_presentes'

# Server hooks
def on_starting(server):
    """
    Executado quando o servidor está iniciando
    """
    print("=" * 60)
    print("🚀 Lista de Presentes - Iniciando servidor")
    print(f"Workers: {workers}")
    print(f"Threads: {threads}")
    print(f"Timeout: {timeout}s")
    print(f"Max Requests: {max_requests}")
    print("=" * 60)


def worker_int(worker):
    """
    Executado quando worker recebe SIGINT ou SIGQUIT
    """
    print(f"⚠️  Worker {worker.pid} recebeu sinal de interrupção")


def on_exit(server):
    """
    Executado quando servidor está encerrando
    """
    print("=" * 60)
    print("👋 Lista de Presentes - Encerrando servidor")
    print("=" * 60)
