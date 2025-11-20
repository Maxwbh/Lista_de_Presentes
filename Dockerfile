# Dockerfile para Lista de Presentes
FROM python:3.11-slim

# Prevenir Python de escrever arquivos .pyc
ENV PYTHONDONTWRITEBYTECODE=1
# Prevenir Python de fazer buffer de stdout/stderr
ENV PYTHONUNBUFFERED=1

# Definir diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primeiro para aproveitar cache do Docker
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY . .

# Criar diretórios necessários
RUN mkdir -p /app/staticfiles /app/media

# Coletar arquivos estáticos
RUN python manage.py collectstatic --noinput --settings=lista_presentes.settings || true

# Tornar entrypoint executável
RUN chmod +x /app/entrypoint.sh || true

# Expor porta
EXPOSE 8000

# Comando padrão
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120", "lista_presentes.wsgi:application"]
