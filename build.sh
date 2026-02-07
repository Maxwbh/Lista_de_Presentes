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

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Test database connection (Supabase)
echo "🔌 Testing database connection..."
if python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lista_presentes.settings')
django.setup()
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute('SELECT 1')
    result = cursor.fetchone()
    if result[0] == 1:
        print('✅ Database connection successful!')
        # Check if Supabase
        host = connection.settings_dict.get('HOST', '')
        if 'supabase.co' in host:
            print('✅ Connected to Supabase PostgreSQL')
        exit(0)
    else:
        print('❌ Database connection failed')
        exit(1)
" 2>&1; then
    echo "✅ Database is ready"
else
    echo "❌ ERROR: Could not connect to database!"
    echo "⚠️  Please check DATABASE_URL in Render Dashboard"
    echo "📖 See RENDER_SUPABASE_SETUP.md for setup instructions"
    exit 1
fi

# Create migrations (if any model changes)
echo "🔄 Creating migrations..."
python manage.py makemigrations --noinput || echo "⚠️  No migrations to create"

# Check for pending migrations
echo "🔍 Checking for pending migrations..."
python manage.py showmigrations --plan || echo "⚠️  Could not show migrations"

# Run migrations with automatic fix for inconsistent history
echo "🗄️  Running migrations..."
if ! python manage.py migrate --noinput --run-syncdb 2>&1 | tee /tmp/migrate_output.log; then
    # Check if error is InconsistentMigrationHistory
    if grep -q "InconsistentMigrationHistory" /tmp/migrate_output.log; then
        echo ""
        echo "⚠️  InconsistentMigrationHistory detected!"
        echo "🔧 Auto-fixing migration history..."
        echo ""

        # Try to fix with --fake-initial first
        if python manage.py migrate --fake-initial --noinput; then
            echo "✅ Fixed with --fake-initial"
        else
            echo "⚠️  --fake-initial failed, trying full reset..."
            # Use fix_migration_history command as last resort
            python manage.py fix_migration_history --reset
        fi

        echo ""
        echo "🔄 Retrying migrations after fix..."
        python manage.py migrate --noinput --run-syncdb
    else
        echo "❌ Migration failed with different error"
        cat /tmp/migrate_output.log
        exit 1
    fi
fi

# Verify migrations applied
echo "✅ Verifying migrations..."
python manage.py showmigrations | grep "\[ \]" && echo "⚠️  WARNING: Some migrations not applied!" || echo "✅ All migrations applied successfully"

# Create/fix admin user automatically
echo "👤 Creating/fixing admin user..."
python manage.py fix_admin || echo "⚠️  Could not fix admin user"

echo "✅ Build completed successfully!"
