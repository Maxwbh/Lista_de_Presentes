#!/usr/bin/env bash
# Build script para Render.com
# Este script garante que todas as configurações estão corretas

set -e  # Exit on error

echo "🔧 Render.com Build Script"
echo "=========================="

# Forçar DJANGO_SETTINGS_MODULE correto
export DJANGO_SETTINGS_MODULE=lista_presentes.settings

echo "✅ DJANGO_SETTINGS_MODULE: $DJANGO_SETTINGS_MODULE"

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Build Tailwind CSS
echo "🎨 Building Tailwind CSS..."
if [ -d "theme/static_src" ]; then
    cd theme/static_src
    npm install --prefer-offline 2>&1 | tail -5
    npx tailwindcss -i ./src/styles.css -o ../static/css/dist/styles.css --minify
    cd ../..
    echo "✅ Tailwind CSS compiled successfully!"
else
    echo "⚠️  theme/static_src not found, skipping Tailwind build"
fi

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Test database connection
echo "🔌 Testing database connection..."
if python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lista_presentes.settings')
django.setup()
from django.db import connection

# Check backend
backend = connection.settings_dict.get('ENGINE', '')

if 'sqlite' in backend.lower():
    print('❌ ERROR: Using SQLite instead of PostgreSQL!')
    print('')
    print('DATABASE_URL not configured in Render Dashboard!')
    print('')
    print('Action Required:')
    print('1. Go to Render Dashboard > lista-presentes > Environment')
    print('2. Add Environment Variable:')
    print('   Key:   DATABASE_URL')
    print('   Value: From your Supabase Dashboard or Render Database')
    print('')
    print('📖 See: USE_RENDER_POSTGRESQL.md for instructions')
    exit(1)

# Test connection
try:
    with connection.cursor() as cursor:
        cursor.execute('SELECT 1')
        result = cursor.fetchone()
        if result[0] == 1:
            print('✅ Database connection successful!')
            # Check if Supabase
            host = connection.settings_dict.get('HOST', '')
            if 'supabase' in host.lower():
                print('✅ Connected to Supabase PostgreSQL')
            elif '.internal' in host or 'render' in host.lower():
                print('✅ Connected to Render PostgreSQL')
            else:
                print(f'✅ Connected to PostgreSQL at {host}')
            exit(0)
        else:
            print('❌ Database connection failed - unexpected result')
            exit(1)
except Exception as e:
    import sys
    error_msg = str(e)

    # Network unreachable - IPv6 ou porta incorreta
    if 'Network is unreachable' in error_msg or 'IPv6' in error_msg:
        print('❌ ERROR: Network is unreachable')
        print('')
        print('This is usually caused by IPv6 routing issues.')
        print('')
        print('SOLUTION: Use Render PostgreSQL instead of external database')
        print('  1. Dashboard > New > PostgreSQL')
        print('  2. Name: lista-presentes-db')
        print('  3. Region: Oregon')
        print('  4. Deploy will connect automatically')
        print('')
        print('📖 See: USE_RENDER_POSTGRESQL.md for details')
    else:
        print(f'❌ ERROR: {error_msg}')
        print('')
        print('📖 Check logs and see: USE_RENDER_POSTGRESQL.md')

    sys.exit(1)
" 2>&1; then
    echo "✅ Database is ready"
else
    echo ""
    echo "================================================================"
    echo "❌ CRITICAL ERROR: Database connection failed!"
    echo "================================================================"
    echo ""
    echo "See error message above for specific solution"
    echo ""
    exit 1
fi

# Ensure schema lista_presentes exists (before migrations)
echo "🗂️  Ensuring schema 'lista_presentes' exists..."
if python scripts/ensure_schema.py; then
    echo "✅ Schema is ready"
else
    echo "❌ Failed to create/verify schema"
    echo "   This may cause migration errors!"
    echo "   Continuing anyway (schema may already exist)..."
fi

# Migrações são criadas no desenvolvimento e versionadas no Git; o deploy
# só confere que nenhuma ficou faltando (gerar aqui criaria arquivos que
# não existem no repositório).
echo "🔍 Checking that all migrations are committed..."
if ! python manage.py makemigrations --check --dry-run; then
    echo "❌ Há mudanças nos models sem migração versionada."
    echo "   Rode 'python manage.py makemigrations' localmente e faça commit."
    exit 1
fi

# Check for pending migrations
echo "🔍 Checking for pending migrations..."
python manage.py showmigrations --plan || echo "⚠️  Could not show migrations"

# Run migrations. Falha para o deploy em vez de mexer no histórico sozinho:
# corrigir histórico de migrações (fake/reset) é decisão manual.
echo "🗄️  Running migrations..."
set -o pipefail
if ! python manage.py migrate --noinput --run-syncdb 2>&1 | tee /tmp/migrate_output.log; then
    if grep -q "InconsistentMigrationHistory" /tmp/migrate_output.log; then
        echo ""
        echo "❌ InconsistentMigrationHistory: o histórico de migrações no banco não bate com o código."
        echo "   Nada foi alterado automaticamente. Para corrigir, da sua máquina, com a"
        echo "   DATABASE_URL do Supabase: python manage.py fix_migration_history"
        echo "   (veja docs/deployment/RENDER.md)."
    else
        echo "❌ Migration failed"
    fi
    exit 1
fi
set +o pipefail

# Imagens: leva para o Supabase Storage as que ainda estão no banco. Sem o
# Storage configurado (ou sem imagens pendentes) não faz nada; uma falha não
# derruba o deploy, porque a imagem continua no banco e é servida de lá.
echo "🖼️  Moving images to Supabase Storage..."
python manage.py migrar_imagens_storage || echo "⚠️  Could not move images to Storage (they stay in the database)"

# Verify migrations applied
echo "✅ Verifying migrations..."
python manage.py showmigrations | grep "\[ \]" && echo "⚠️  WARNING: Some migrations not applied!" || echo "✅ All migrations applied successfully"

# Create/fix admin user automatically
echo "👤 Creating/fixing admin user..."
python manage.py fix_admin || echo "⚠️  Could not fix admin user"

echo "✅ Build completed successfully!"
