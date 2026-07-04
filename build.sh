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
