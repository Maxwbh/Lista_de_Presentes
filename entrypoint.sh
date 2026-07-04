#!/bin/bash

# Script de inicialização para Django
set -e

echo "Iniciando aplicação Lista de Presentes..."

# Aguardar banco de dados estar pronto (PostgreSQL)
# Usa psycopg2 (já instalado) em vez de netcat — sem dependência de sistema
if [ -n "$DATABASE_URL" ]; then
    echo "Aguardando banco de dados..."
    python - << 'END'
import os, sys, time
import psycopg2

url = os.environ['DATABASE_URL']
for tentativa in range(30):
    try:
        conn = psycopg2.connect(url, connect_timeout=5)
        conn.close()
        print("Banco de dados pronto!")
        sys.exit(0)
    except psycopg2.OperationalError as e:
        print(f"  Banco ainda não está pronto ({tentativa + 1}/30)...")
        time.sleep(2)
print("ERRO: banco de dados não respondeu após 60s", file=sys.stderr)
sys.exit(1)
END
fi

# Garantir que o schema existe antes das migrations
echo "Verificando schema do banco..."
python scripts/ensure_schema.py

# Executar migrations
echo "Executando migrations..."
python manage.py migrate --noinput

# Garantir superusuário admin (idempotente)
echo "Garantindo usuário admin..."
python manage.py fix_admin || echo "Não foi possível garantir o admin, continuando..."

# Coletar arquivos estáticos (incremental, sem --clear para acelerar boot)
echo "Coletando arquivos estáticos..."
python manage.py collectstatic --noinput

# Criar superusuário se não existir (opcional)
if [ "$CREATE_SUPERUSER" = "true" ]; then
    echo "Criando superusuário..."
    python manage.py shell << END
from presentes.models import Usuario
import os

email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123')
username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')

if not Usuario.objects.filter(email=email).exists():
    Usuario.objects.create_superuser(
        username=username,
        email=email,
        password=password,
        first_name='Admin',
        last_name='Sistema'
    )
    print(f'Superusuário criado: {email}')
else:
    print(f'Superusuário já existe: {email}')
END
fi

echo "Inicialização completa! Servidor iniciando..."

# Executar comando passado para o container
exec "$@"
