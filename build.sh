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

# Create migrations (if any model changes)
echo "🔄 Creating migrations..."
python manage.py makemigrations --noinput || echo "⚠️  No migrations to create"

# Check for pending migrations
echo "🔍 Checking for pending migrations..."
python manage.py showmigrations --plan || echo "⚠️  Could not show migrations"

# Run migrations (force apply all)
echo "🗄️  Running migrations..."
python manage.py migrate --noinput --run-syncdb

# Verify migrations applied
echo "✅ Verifying migrations..."
python manage.py showmigrations | grep "\[ \]" && echo "⚠️  WARNING: Some migrations not applied!" || echo "✅ All migrations applied successfully"

# Create/fix admin user automatically
echo "👤 Creating/fixing admin user..."
python manage.py fix_admin || echo "⚠️  Could not fix admin user"

echo "✅ Build completed successfully!"
