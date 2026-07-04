#!/usr/bin/env bash
# Script para forçar aplicação de migrações no Render
# Usar em caso de problemas com migrações

set -e

echo "🔧 Force Migrations Script"
echo "=========================="

# Verificar se estamos no ambiente correto
if [ -z "$DATABASE_URL" ]; then
    echo "⚠️  WARNING: DATABASE_URL not set. Are you in Render environment?"
fi

# Forçar DJANGO_SETTINGS_MODULE
export DJANGO_SETTINGS_MODULE=lista_presentes.settings

echo "✅ DJANGO_SETTINGS_MODULE: $DJANGO_SETTINGS_MODULE"

# Mostrar migrações pendentes
echo ""
echo "📋 Current migration status:"
python manage.py showmigrations

# Tentar criar novas migrações
echo ""
echo "🔄 Creating migrations..."
python manage.py makemigrations || {
    echo "⚠️  makemigrations failed, continuing anyway..."
}

# Aplicar migrações com sync
echo ""
echo "🗄️  Applying migrations with --run-syncdb..."
python manage.py migrate --run-syncdb --noinput || {
    echo "❌ migrate --run-syncdb failed!"
    exit 1
}

# Verificar se todas foram aplicadas
echo ""
echo "✅ Final migration status:"
python manage.py showmigrations

# Contar migrações não aplicadas
NOT_APPLIED=$(python manage.py showmigrations | grep -c "\[ \]" || echo "0")

if [ "$NOT_APPLIED" -gt 0 ]; then
    echo ""
    echo "⚠️  WARNING: $NOT_APPLIED migrations not applied!"
    echo "   Please check the migration status above."
    exit 1
else
    echo ""
    echo "✅ All migrations applied successfully!"
fi
