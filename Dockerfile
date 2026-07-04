# Dockerfile para Lista de Presentes (otimizado para Render Free Tier)
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Nenhuma dependencia de sistema necessaria:
# psycopg2-binary, Pillow, lxml e cryptography usam wheels pre-compilados

# Instalar dependencias Python (camada cacheavel)
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copiar codigo
COPY . .

# Usuario non-root (seguranca)
RUN useradd --create-home --shell /bin/bash app && \
    mkdir -p /app/staticfiles /app/media && \
    chmod +x /app/entrypoint.sh /app/build.sh 2>/dev/null; \
    chown -R app:app /app
USER app

# Coletar arquivos estaticos
RUN python manage.py collectstatic --noinput --settings=lista_presentes.settings || true

EXPOSE 8000

# Healthcheck no endpoint /health/ da aplicacao
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request,os; urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"PORT\",\"8000\")}/health/', timeout=4)" || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]

# Free Tier: gunicorn.conf.py define 1 worker gthread + 4 threads (512MB RAM)
CMD ["gunicorn", "--config", "gunicorn.conf.py", "lista_presentes.wsgi:application"]
