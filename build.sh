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

# Run migrations
echo "🗄️  Running migrations..."
python manage.py migrate --noinput

echo "✅ Build completed successfully!"
