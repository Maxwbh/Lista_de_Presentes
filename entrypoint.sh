#!/bin/bash

# Script de inicialização para Django
set -e

echo "🚀 Iniciando aplicação Lista de Presentes..."

# Aguardar banco de dados estar pronto (se usando PostgreSQL)
if [ -n "$DATABASE_URL" ]; then
    echo "⏳ Aguardando banco de dados..."

    # Extrair host do DATABASE_URL
    DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
    DB_PORT=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')

    if [ -n "$DB_HOST" ] && [ -n "$DB_PORT" ]; then
        until nc -z $DB_HOST $DB_PORT; do
            echo "   Banco de dados ainda não está pronto - aguardando..."
            sleep 2
        done
        echo "✅ Banco de dados pronto!"
    fi
fi

# Executar migrations
echo "📦 Executando migrations..."
python manage.py migrate --noinput

# Coletar arquivos estáticos
echo "📁 Coletando arquivos estáticos..."
python manage.py collectstatic --noinput --clear

# Criar superusuário se não existir (opcional)
if [ "$CREATE_SUPERUSER" = "true" ]; then
    echo "👤 Criando superusuário..."
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
    print(f'✅ Superusuário criado: {email}')
else:
    print(f'ℹ️  Superusuário já existe: {email}')
END
fi

echo "✨ Inicialização completa!"
echo "🌐 Servidor iniciando..."

# Executar comando passado para o container
exec "$@"
