#!/usr/bin/env python
"""
Script para detectar se DATABASE_URL foi configurada corretamente no Render.

Uso:
    python scripts/check_database_config.py
"""

import os
import sys
from pathlib import Path

# Adicionar o diretório raiz ao PYTHONPATH
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lista_presentes.settings')
import django
django.setup()

from django.db import connection


def print_error(text):
    """Imprime mensagem de erro."""
    print(f"\033[91m❌ {text}\033[0m")


def print_success(text):
    """Imprime mensagem de sucesso."""
    print(f"\033[92m✅ {text}\033[0m")


def print_warning(text):
    """Imprime mensagem de aviso."""
    print(f"\033[93m⚠️  {text}\033[0m")


def print_info(text):
    """Imprime mensagem informativa."""
    print(f"\033[94mℹ️  {text}\033[0m")


def check_database_config():
    """Verifica se DATABASE_URL foi configurada corretamente."""
    print("\n" + "=" * 70)
    print("🔍 VERIFICAÇÃO DE CONFIGURAÇÃO DO BANCO DE DADOS")
    print("=" * 70 + "\n")

    # 1. Verificar variável DATABASE_URL
    database_url = os.getenv('DATABASE_URL')

    if not database_url:
        print_error("DATABASE_URL não está definida!")
        print("\n📋 AÇÃO NECESSÁRIA:")
        print("   Adicione DATABASE_URL no Render Dashboard > Environment")
        print("\n   Key:   DATABASE_URL")
        print("   Value: postgresql://postgres.YOUR_PROJECT:YOUR_PASSWORD@aws-X-us-east-X.pooler.supabase.com:6543/postgres")
        print("\n📖 Consulte: docs/database/SUPABASE.md ou docs/deployment/RENDER.md")
        return False
    else:
        # Ocultar senha
        if '@' in database_url:
            safe_url = '...@' + database_url.split('@')[1]
        else:
            safe_url = database_url[:30] + '...'
        print_success(f"DATABASE_URL está definida: {safe_url}")

    # 2. Verificar backend do banco
    db_backend = connection.settings_dict.get('ENGINE', '')

    if 'sqlite' in db_backend.lower():
        print_error("Django está usando SQLite!")
        print_warning("Isso indica que DATABASE_URL não foi lida corretamente.")
        print("\n🔧 POSSÍVEIS CAUSAS:")
        print("   1. DATABASE_URL mal formatada (verifique URL encoding)")
        print("   2. USE_SQLITE=True definido (remova essa variável)")
        print("   3. DATABASE_URL vazia ou inválida")
        print("\n📋 SOLUÇÃO:")
        print("   Verifique se DATABASE_URL contém URL encoding correto:")
        print("   - ! → %21")
        print("   - @ → %40")
        print("   - # → %23")
        return False

    elif 'postgresql' in db_backend.lower():
        print_success("Django está usando PostgreSQL ✅")

        # Verificar se é Supabase
        host = connection.settings_dict.get('HOST', '')
        if 'supabase.co' in host:
            print_success("Conectado ao Supabase PostgreSQL ✨")
        else:
            print_info(f"Conectado a PostgreSQL em: {host}")

    else:
        print_warning(f"Backend desconhecido: {db_backend}")

    # 3. Testar conexão
    print("\n" + "-" * 70)
    print("🔌 Testando conexão com banco de dados...")
    print("-" * 70 + "\n")

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()

            if result[0] == 1:
                print_success("Conexão com banco de dados OK!")

                # Obter versão do PostgreSQL
                cursor.execute("SELECT version()")
                version = cursor.fetchone()[0]
                version_short = version.split(',')[0]
                print_info(f"Versão: {version_short}")

                # Obter nome do banco
                cursor.execute("SELECT current_database()")
                db_name = cursor.fetchone()[0]
                print_info(f"Database: {db_name}")

                return True
            else:
                print_error("Resposta inesperada do banco")
                return False

    except Exception as e:
        print_error(f"Falha ao conectar: {e}")
        print("\n🔧 POSSÍVEIS CAUSAS:")
        print("   1. Senha incorreta na DATABASE_URL")
        print("   2. Host/porta inacessível")
        print("   3. Banco de dados não existe")
        print("   4. Firewall bloqueando conexão")
        return False


def main():
    """Função principal."""
    success = check_database_config()

    print("\n" + "=" * 70)
    if success:
        print("✅ CONFIGURAÇÃO OK - Pronto para produção!")
        print("=" * 70 + "\n")
        sys.exit(0)
    else:
        print("❌ CONFIGURAÇÃO INCORRETA - Corrija antes de fazer deploy!")
        print("=" * 70 + "\n")
        print("📖 Documentação:")
        print("   - Guia rápido: CHECKLIST_SUPABASE.md")
        print("   - Guia completo: RENDER_SUPABASE_SETUP.md")
        print("   - Troubleshooting: MIGRATION_FIX.md")
        print()
        sys.exit(1)


if __name__ == '__main__':
    main()
