#!/usr/bin/env bash
# Script para monitorar status do Render Free Tier
# Verifica memória, CPU, database, etc.

set -e

echo "📊 Monitor Render Free Tier"
echo "=========================="
echo ""

# Verificar se estamos no ambiente Render
if [ -z "$DATABASE_URL" ]; then
    echo "⚠️  Executando localmente (não no Render)"
    echo "   Para monitorar o Render, execute este script via Shell no dashboard"
    echo ""
fi

# 1. Informações do Sistema
echo "🖥️  Informações do Sistema:"
echo "--------------------------"
echo "Hostname: $(hostname)"
echo "Python: $(python --version)"
echo "Django: $(python -c 'import django; print(django.get_version())')"
echo ""

# 2. Memória
echo "💾 Uso de Memória:"
echo "--------------------------"
free -h 2>/dev/null || echo "Comando 'free' não disponível"
echo ""

# 3. Processos
echo "⚙️  Processos Gunicorn:"
echo "--------------------------"
ps aux | grep gunicorn | grep -v grep || echo "Gunicorn não está rodando"
echo ""

# 4. Uso de Disco
echo "💿 Uso de Disco:"
echo "--------------------------"
df -h / 2>/dev/null || echo "Comando 'df' não disponível"
echo ""

# 5. Database
if [ -n "$DATABASE_URL" ]; then
    echo "🗄️  Database Status:"
    echo "--------------------------"

    # Conectar ao database e verificar informações
    python << 'PYEOF'
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lista_presentes.settings')
django.setup()

from django.db import connection

try:
    with connection.cursor() as cursor:
        # Tamanho do database
        cursor.execute("""
            SELECT pg_size_pretty(pg_database_size(current_database())) as size;
        """)
        size = cursor.fetchone()[0]
        print(f"  Tamanho: {size}")

        # Número de tabelas
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.tables
            WHERE table_schema = 'public';
        """)
        tables = cursor.fetchone()[0]
        print(f"  Tabelas: {tables}")

        # Número de conexões
        cursor.execute("""
            SELECT COUNT(*) FROM pg_stat_activity;
        """)
        connections = cursor.fetchone()[0]
        print(f"  Conexões ativas: {connections}")

        print("  Status: ✅ OK")
except Exception as e:
    print(f"  Status: ❌ Erro - {e}")
PYEOF
    echo ""
else
    echo "🗄️  Database: Não configurado (DATABASE_URL não encontrado)"
    echo ""
fi

# 6. Migrações
echo "🔄 Status das Migrações:"
echo "--------------------------"
python manage.py showmigrations --list 2>/dev/null | head -20 || echo "Erro ao verificar migrações"
echo ""

# 7. Verificar variáveis de ambiente importantes
echo "🔧 Variáveis de Ambiente:"
echo "--------------------------"
echo "  DJANGO_SETTINGS_MODULE: ${DJANGO_SETTINGS_MODULE:-não definido}"
echo "  DEBUG: ${DEBUG:-não definido}"
echo "  WEB_CONCURRENCY: ${WEB_CONCURRENCY:-não definido}"
echo "  GUNICORN_TIMEOUT: ${GUNICORN_TIMEOUT:-não definido}"
echo "  MAX_REQUESTS: ${MAX_REQUESTS:-não definido}"
echo ""

# 8. Health Check
echo "🏥 Health Check:"
echo "--------------------------"
if command -v curl &> /dev/null; then
    response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:${PORT:-8000}/health/ 2>/dev/null || echo "000")
    if [ "$response" = "200" ]; then
        echo "  Status: ✅ OK (HTTP $response)"
    else
        echo "  Status: ⚠️  HTTP $response"
    fi
else
    echo "  curl não disponível"
fi
echo ""

# 9. Resumo
echo "📋 Resumo:"
echo "=========================="
echo "Se você está vendo isso no Render Shell, seu serviço está funcionando!"
echo ""
echo "Dicas:"
echo "  - Free Tier: 512 MB RAM, desliga após 15 min de inatividade"
echo "  - Database: Expira em 90 dias, faça backups regulares"
echo "  - Use keep-alive para evitar cold starts"
echo ""
echo "Para mais informações, consulte RENDER_FREE_TIER.md"
