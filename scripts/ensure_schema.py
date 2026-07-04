#!/usr/bin/env python
"""
Script para garantir que o schema lista_presentes existe no PostgreSQL.

Este script é executado automaticamente durante o build do Render,
antes das migrations Django.

Funcionalidades:
- Cria schema lista_presentes se não existir
- Concede permissões ao role postgres
- Idempotente (seguro executar múltiplas vezes)
"""

import os
import sys
import psycopg2
from urllib.parse import urlparse


def ensure_schema():
    """Garante que o schema lista_presentes existe no banco."""

    # Obter DATABASE_URL
    database_url = os.getenv('DATABASE_URL')

    if not database_url:
        print("⚠️  DATABASE_URL não configurada. Pulando criação de schema (modo SQLite?).")
        return True

    # Parse DATABASE_URL (apenas para logging — libpq decodifica a URI)
    try:
        result = urlparse(database_url)

        hostname = result.hostname
        port = result.port or 5432

        print(f"🔌 Conectando ao PostgreSQL em {hostname}:{port}...")

        # Conectar passando a URL diretamente: o libpq decodifica corretamente
        # o percent-encoding de usuário/senha (ex.: senhas com !@# viram %21%40%23).
        # O parse manual com urlparse NÃO decodifica, causando falha de autenticação.
        conn = psycopg2.connect(database_url, connect_timeout=10)

        conn.autocommit = True
        cursor = conn.cursor()

        # Verificar se schema existe
        cursor.execute("""
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name = 'lista_presentes'
        """)

        if cursor.fetchone():
            print("✅ Schema 'lista_presentes' já existe.")
        else:
            print("📦 Criando schema 'lista_presentes'...")

            # Criar schema
            cursor.execute("CREATE SCHEMA IF NOT EXISTS lista_presentes")

            # Conceder permissões ao role postgres
            cursor.execute("GRANT ALL ON SCHEMA lista_presentes TO postgres")
            cursor.execute("GRANT ALL ON SCHEMA lista_presentes TO CURRENT_USER")

            # Configurar default privileges para tabelas futuras
            cursor.execute("""
                ALTER DEFAULT PRIVILEGES IN SCHEMA lista_presentes
                GRANT ALL ON TABLES TO postgres
            """)
            cursor.execute("""
                ALTER DEFAULT PRIVILEGES IN SCHEMA lista_presentes
                GRANT ALL ON SEQUENCES TO postgres
            """)

            print("✅ Schema 'lista_presentes' criado com sucesso!")

        # Verificar search_path
        cursor.execute("SHOW search_path")
        search_path = cursor.fetchone()[0]
        print(f"📍 Search path atual: {search_path}")

        # GUARDA: detectar tabelas desta app criadas indevidamente no public
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND (table_name LIKE 'presentes_%' OR table_name = 'django_migrations')
        """)
        tabelas_vazadas = [row[0] for row in cursor.fetchall()]

        if tabelas_vazadas:
            print("⚠️  ATENÇÃO: Tabelas desta app encontradas no schema PUBLIC:")
            for t in tabelas_vazadas:
                print(f"   - public.{t}")
            print("   Mova-as para lista_presentes com:")
            print("   ALTER TABLE public.<tabela> SET SCHEMA lista_presentes;")
        else:
            print("✅ Nenhuma tabela da app no schema public (isolamento OK)")

        cursor.close()
        conn.close()

        print("✅ Schema configurado corretamente!")
        return True

    except psycopg2.Error as e:
        print(f"❌ Erro ao conectar/configurar PostgreSQL: {e}")
        print(f"   Código: {e.pgcode}")
        return False

    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False


if __name__ == "__main__":
    print("=" * 70)
    print("🔧 Garantindo que schema 'lista_presentes' existe...")
    print("=" * 70)

    success = ensure_schema()

    if success:
        print("=" * 70)
        print("✅ Schema pronto para migrations!")
        print("=" * 70)
        sys.exit(0)
    else:
        print("=" * 70)
        print("❌ Falha ao configurar schema!")
        print("=" * 70)
        sys.exit(1)
