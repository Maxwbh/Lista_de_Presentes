#!/usr/bin/env python
"""
Script para testar a conexão com o banco de dados Supabase PostgreSQL.

Uso:
    python scripts/test_supabase_connection.py

Ou com variáveis de ambiente:
    DATABASE_URL="postgresql://..." python scripts/test_supabase_connection.py
"""

import os
import sys
import django
from pathlib import Path

# Adicionar o diretório raiz ao PYTHONPATH
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lista_presentes.settings')
django.setup()

from django.db import connection
from django.core.management import call_command
import psycopg2


def print_header(text):
    """Imprime um cabeçalho formatado."""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)


def print_success(text):
    """Imprime mensagem de sucesso."""
    print(f"✅ {text}")


def print_error(text):
    """Imprime mensagem de erro."""
    print(f"❌ {text}")


def print_warning(text):
    """Imprime mensagem de aviso."""
    print(f"⚠️  {text}")


def print_info(text):
    """Imprime mensagem informativa."""
    print(f"ℹ️  {text}")


def test_database_connection():
    """Testa a conexão com o banco de dados."""
    print_header("1. TESTANDO CONEXÃO COM O BANCO DE DADOS")

    try:
        # Tentar conectar
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()

            if result[0] == 1:
                print_success("Conexão estabelecida com sucesso!")
                return True
            else:
                print_error("Conexão falhou - resultado inesperado")
                return False

    except Exception as e:
        print_error(f"Falha ao conectar: {e}")
        return False


def get_database_info():
    """Obtém informações sobre o banco de dados."""
    print_header("2. INFORMAÇÕES DO BANCO DE DADOS")

    try:
        with connection.cursor() as cursor:
            # Nome do banco
            cursor.execute("SELECT current_database()")
            db_name = cursor.fetchone()[0]
            print_info(f"Nome do banco: {db_name}")

            # Versão do PostgreSQL
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            print_info(f"Versão: {version.split(',')[0]}")

            # Usuário conectado
            cursor.execute("SELECT current_user")
            user = cursor.fetchone()[0]
            print_info(f"Usuário: {user}")

            # Host
            cursor.execute("SELECT inet_server_addr()")
            host = cursor.fetchone()[0]
            if host:
                print_info(f"Host: {host}")

            # Porta
            cursor.execute("SELECT inet_server_port()")
            port = cursor.fetchone()[0]
            print_info(f"Porta: {port}")

            # Tamanho do banco
            cursor.execute(f"SELECT pg_size_pretty(pg_database_size('{db_name}'))")
            size = cursor.fetchone()[0]
            print_info(f"Tamanho do banco: {size}")

            return True

    except Exception as e:
        print_error(f"Erro ao obter informações: {e}")
        return False


def check_tables():
    """Verifica se as tabelas do Django existem."""
    print_header("3. VERIFICANDO TABELAS DO DJANGO")

    try:
        with connection.cursor() as cursor:
            # Listar todas as tabelas
            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
            tables = cursor.fetchall()

            if tables:
                print_success(f"Encontradas {len(tables)} tabelas:")
                for table in tables:
                    # Contar registros
                    cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                    count = cursor.fetchone()[0]
                    print(f"   • {table[0]}: {count} registros")
                return True
            else:
                print_warning("Nenhuma tabela encontrada - execute as migrações")
                return False

    except Exception as e:
        print_error(f"Erro ao verificar tabelas: {e}")
        return False


def check_migrations():
    """Verifica o status das migrações."""
    print_header("4. VERIFICANDO MIGRAÇÕES")

    try:
        # Usar Django management command
        print_info("Migrações aplicadas:")
        call_command('showmigrations', '--plan')
        return True

    except Exception as e:
        print_error(f"Erro ao verificar migrações: {e}")
        return False


def check_extensions():
    """Verifica extensões PostgreSQL instaladas."""
    print_header("5. VERIFICANDO EXTENSÕES POSTGRESQL")

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT extname, extversion
                FROM pg_extension
                ORDER BY extname
            """)
            extensions = cursor.fetchall()

            if extensions:
                print_success(f"Encontradas {len(extensions)} extensões:")
                for ext in extensions:
                    print(f"   • {ext[0]} (v{ext[1]})")
            else:
                print_warning("Nenhuma extensão encontrada")

            # Verificar extensões recomendadas
            recommended = ['uuid-ossp', 'pgcrypto', 'pg_stat_statements']
            for rec in recommended:
                cursor.execute(f"SELECT COUNT(*) FROM pg_extension WHERE extname = '{rec}'")
                if cursor.fetchone()[0] == 0:
                    print_warning(f"Extensão recomendada '{rec}' não instalada")

            return True

    except Exception as e:
        print_error(f"Erro ao verificar extensões: {e}")
        return False


def check_connection_settings():
    """Verifica configurações de conexão."""
    print_header("6. CONFIGURAÇÕES DE CONEXÃO")

    try:
        db_settings = connection.settings_dict

        print_info(f"Engine: {db_settings.get('ENGINE', 'N/A')}")
        print_info(f"Nome: {db_settings.get('NAME', 'N/A')}")
        print_info(f"Host: {db_settings.get('HOST', 'N/A')}")
        print_info(f"Porta: {db_settings.get('PORT', 'N/A')}")
        print_info(f"Usuário: {db_settings.get('USER', 'N/A')}")

        # Configurações de pool
        conn_max_age = db_settings.get('CONN_MAX_AGE', 0)
        print_info(f"Connection Max Age: {conn_max_age}s")

        if conn_max_age > 0:
            print_success("Connection pooling habilitado")
        else:
            print_warning("Connection pooling desabilitado (conn_max_age=0)")

        # Verificar se é Supabase
        host = db_settings.get('HOST', '')
        if 'supabase.co' in host:
            print_success("Conectado ao Supabase PostgreSQL ✨")
        elif 'render.com' in host:
            print_info("Conectado ao Render PostgreSQL")
        else:
            print_info("Conectado a servidor PostgreSQL externo")

        return True

    except Exception as e:
        print_error(f"Erro ao verificar configurações: {e}")
        return False


def test_write_permissions():
    """Testa permissões de escrita."""
    print_header("7. TESTANDO PERMISSÕES DE ESCRITA")

    try:
        with connection.cursor() as cursor:
            # Tentar criar uma tabela temporária
            cursor.execute("""
                CREATE TEMPORARY TABLE test_permissions (
                    id SERIAL PRIMARY KEY,
                    test_data TEXT
                )
            """)
            print_success("Permissão de CREATE: OK")

            # Tentar inserir dados
            cursor.execute("INSERT INTO test_permissions (test_data) VALUES ('test')")
            print_success("Permissão de INSERT: OK")

            # Tentar ler dados
            cursor.execute("SELECT * FROM test_permissions")
            result = cursor.fetchone()
            if result:
                print_success("Permissão de SELECT: OK")

            # Tentar atualizar dados
            cursor.execute("UPDATE test_permissions SET test_data = 'updated' WHERE id = 1")
            print_success("Permissão de UPDATE: OK")

            # Tentar deletar dados
            cursor.execute("DELETE FROM test_permissions WHERE id = 1")
            print_success("Permissão de DELETE: OK")

            # Tentar dropar tabela
            cursor.execute("DROP TABLE test_permissions")
            print_success("Permissão de DROP: OK")

        print_success("Todas as permissões de escrita: OK ✅")
        return True

    except Exception as e:
        print_error(f"Erro ao testar permissões: {e}")
        return False


def print_summary(results):
    """Imprime resumo dos testes."""
    print_header("RESUMO DOS TESTES")

    total = len(results)
    passed = sum(results.values())
    failed = total - passed

    print(f"\nTotal de testes: {total}")
    print(f"✅ Passou: {passed}")
    print(f"❌ Falhou: {failed}")

    if failed == 0:
        print("\n🎉 TODOS OS TESTES PASSARAM! Conexão com Supabase está OK!")
        print("\n✅ Você pode fazer deploy no Render com segurança.")
    else:
        print("\n⚠️  ALGUNS TESTES FALHARAM!")
        print("\n📋 Próximos passos:")
        print("   1. Verifique se DATABASE_URL está correta")
        print("   2. Verifique se o Supabase está acessível")
        print("   3. Execute as migrações: python manage.py migrate")
        print("   4. Consulte RENDER_SUPABASE_SETUP.md para mais detalhes")

    print("\n" + "=" * 80 + "\n")


def main():
    """Função principal."""
    print("\n🔍 TESTE DE CONEXÃO COM SUPABASE POSTGRESQL")
    print("=" * 80)

    # Verificar se DATABASE_URL está definida
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        # Ocultar senha na exibição
        safe_url = database_url.split('@')[1] if '@' in database_url else database_url
        print(f"\nDATABASE_URL: ...@{safe_url}")
    else:
        print_warning("DATABASE_URL não definida - usando configuração padrão do settings.py")

    # Executar testes
    results = {
        'Conexão': test_database_connection(),
        'Informações': get_database_info(),
        'Tabelas': check_tables(),
        'Migrações': check_migrations(),
        'Extensões': check_extensions(),
        'Configurações': check_connection_settings(),
        'Permissões': test_write_permissions(),
    }

    # Imprimir resumo
    print_summary(results)

    # Retornar código de saída
    if all(results.values()):
        sys.exit(0)  # Sucesso
    else:
        sys.exit(1)  # Falha


if __name__ == '__main__':
    main()
