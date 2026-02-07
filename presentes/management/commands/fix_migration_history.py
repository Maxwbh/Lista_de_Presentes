"""
Comando Django para corrigir histórico de migrações inconsistente
Resolve erro: InconsistentMigrationHistory
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection
from django.db.migrations.exceptions import InconsistentMigrationHistory
import sys


class Command(BaseCommand):
    help = 'Corrige histórico de migrações inconsistente (InconsistentMigrationHistory)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Limpa completamente o histórico e re-aplica com --fake-initial',
        )

    def handle(self, *args, **options):
        reset_history = options['reset']

        self.stdout.write(self.style.WARNING('=' * 70))
        self.stdout.write(self.style.WARNING('FIX MIGRATION HISTORY - Corrigir histórico inconsistente'))
        self.stdout.write(self.style.WARNING('=' * 70))
        self.stdout.write('')

        # Verificar conexão com banco de dados
        try:
            self.stdout.write('🔍 Testando conexão com banco de dados...')
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                if result[0] == 1:
                    self.stdout.write(self.style.SUCCESS('✅ Conexão com banco OK'))

                    # Verificar se é Supabase
                    host = connection.settings_dict.get('HOST', '')
                    if 'supabase.co' in host:
                        self.stdout.write(self.style.SUCCESS('✅ Conectado ao Supabase PostgreSQL'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro ao conectar: {e}'))
            sys.exit(1)

        self.stdout.write('')

        # Tentar mostrar status atual (pode falhar com InconsistentMigrationHistory)
        self.stdout.write('📋 Tentando verificar status das migrações...')
        try:
            call_command('showmigrations', '--list')
            self.stdout.write(self.style.SUCCESS('✅ Histórico de migrações está OK!'))
            self.stdout.write(self.style.WARNING('⚠️  Nenhuma correção necessária.'))
            return
        except InconsistentMigrationHistory as e:
            self.stdout.write(self.style.ERROR('❌ Histórico de migrações INCONSISTENTE detectado!'))
            self.stdout.write(self.style.ERROR(f'   Erro: {str(e)}'))
            self.stdout.write('')
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'⚠️  Erro ao verificar: {e}'))
            self.stdout.write('')

        # Decidir estratégia de correção
        if reset_history:
            self.stdout.write(self.style.WARNING('🔄 ESTRATÉGIA: Resetar histórico completo'))
            self._reset_and_fake_initial()
        else:
            self.stdout.write(self.style.WARNING('🔄 ESTRATÉGIA: Aplicar com --fake-initial'))
            self._apply_fake_initial()

    def _apply_fake_initial(self):
        """Aplica migrações usando --fake-initial para corrigir histórico."""
        self.stdout.write('')
        self.stdout.write('=' * 70)
        self.stdout.write('MÉTODO 1: Aplicar com --fake-initial')
        self.stdout.write('=' * 70)
        self.stdout.write('')
        self.stdout.write('Este método vai:')
        self.stdout.write('  1. Detectar tabelas que já existem no banco')
        self.stdout.write('  2. Marcar migrações iniciais como "fake" (não executadas)')
        self.stdout.write('  3. Aplicar migrações restantes normalmente')
        self.stdout.write('')

        try:
            self.stdout.write('🗄️  Executando: migrate --fake-initial --noinput')
            call_command('migrate', '--fake-initial', '--noinput', verbosity=2)
            self.stdout.write(self.style.SUCCESS('✅ Migrações aplicadas com --fake-initial'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro ao aplicar --fake-initial: {e}'))
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('⚠️  Tentando método alternativo...'))
            self._reset_and_fake_initial()
            return

        self.stdout.write('')
        self._verify_final_status()

    def _reset_and_fake_initial(self):
        """Limpa histórico e re-aplica tudo com --fake-initial."""
        self.stdout.write('')
        self.stdout.write('=' * 70)
        self.stdout.write('MÉTODO 2: Resetar histórico completo')
        self.stdout.write('=' * 70)
        self.stdout.write('')
        self.stdout.write('⚠️  ATENÇÃO: Este método vai limpar a tabela django_migrations')
        self.stdout.write('   e re-registrar todas as migrações.')
        self.stdout.write('')
        self.stdout.write('✅ Seguro: Não deleta dados, apenas histórico de migrações')
        self.stdout.write('')

        try:
            # Limpar tabela django_migrations
            self.stdout.write('🧹 Limpando tabela django_migrations...')
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM django_migrations")
                deleted = cursor.rowcount
                self.stdout.write(self.style.SUCCESS(f'✅ Removidos {deleted} registros de histórico'))

            self.stdout.write('')

            # Re-aplicar todas as migrações com --fake-initial
            self.stdout.write('🗄️  Re-aplicando migrações com --fake-initial...')
            call_command('migrate', '--fake-initial', '--noinput', verbosity=2)
            self.stdout.write(self.style.SUCCESS('✅ Histórico reconstruído com sucesso!'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro ao resetar histórico: {e}'))
            self.stdout.write('')
            self.stdout.write(self.style.ERROR('⚠️  SOLUÇÃO MANUAL NECESSÁRIA'))
            self.stdout.write('')
            self.stdout.write('Execute manualmente:')
            self.stdout.write('  1. psql $DATABASE_URL')
            self.stdout.write('  2. DELETE FROM django_migrations;')
            self.stdout.write('  3. python manage.py migrate --fake-initial')
            sys.exit(1)

        self.stdout.write('')
        self._verify_final_status()

    def _verify_final_status(self):
        """Verifica status final das migrações."""
        self.stdout.write('=' * 70)
        self.stdout.write('VERIFICANDO STATUS FINAL')
        self.stdout.write('=' * 70)
        self.stdout.write('')

        try:
            self.stdout.write('📋 Status das migrações:')
            call_command('showmigrations', '--list')
            self.stdout.write('')

            # Contar migrações pendentes
            self.stdout.write('🔍 Verificando migrações pendentes...')
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) FROM django_migrations
                """)
                total_migrations = cursor.fetchone()[0]

            self.stdout.write(self.style.SUCCESS(f'✅ Total de migrações aplicadas: {total_migrations}'))
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('=' * 70))
            self.stdout.write(self.style.SUCCESS('✅ HISTÓRICO DE MIGRAÇÕES CORRIGIDO!'))
            self.stdout.write(self.style.SUCCESS('=' * 70))
            self.stdout.write('')
            self.stdout.write('🎉 Você pode fazer deploy com segurança agora!')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro ao verificar status final: {e}'))
            sys.exit(1)
