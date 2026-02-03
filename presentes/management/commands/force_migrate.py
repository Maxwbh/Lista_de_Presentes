"""
Comando Django para forçar aplicação de migrações
Útil para resolver problemas de migrações no deploy
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection
import sys


class Command(BaseCommand):
    help = 'Força a aplicação de todas as migrações pendentes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--check',
            action='store_true',
            help='Apenas verifica migrações pendentes sem aplicar',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Modo verboso com mais detalhes',
        )

    def handle(self, *args, **options):
        check_only = options['check']
        verbose = options['verbose']

        self.stdout.write(self.style.WARNING('=' * 60))
        self.stdout.write(self.style.WARNING('FORCE MIGRATE - Aplicação forçada de migrações'))
        self.stdout.write(self.style.WARNING('=' * 60))
        self.stdout.write('')

        # Verificar conexão com banco de dados
        try:
            self.stdout.write('🔍 Testando conexão com banco de dados...')
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            self.stdout.write(self.style.SUCCESS('✅ Conexão com banco de dados OK'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro ao conectar com banco: {e}'))
            sys.exit(1)

        self.stdout.write('')

        # Mostrar status atual das migrações
        self.stdout.write('📋 Status atual das migrações:')
        self.stdout.write('-' * 60)
        try:
            call_command('showmigrations', '--list')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro ao mostrar migrações: {e}'))

        self.stdout.write('')

        if check_only:
            self.stdout.write(self.style.WARNING('⚠️  Modo CHECK: apenas verificando, não aplicando'))
            return

        # Criar migrações se houver mudanças nos models
        self.stdout.write('🔄 Criando novas migrações (se necessário)...')
        try:
            call_command('makemigrations', '--noinput', verbosity=2 if verbose else 1)
            self.stdout.write(self.style.SUCCESS('✅ Migrações criadas (se necessário)'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'⚠️  makemigrations: {e}'))

        self.stdout.write('')

        # Aplicar migrações com run-syncdb
        self.stdout.write('🗄️  Aplicando migrações com --run-syncdb...')
        try:
            call_command(
                'migrate',
                '--run-syncdb',
                '--noinput',
                verbosity=2 if verbose else 1
            )
            self.stdout.write(self.style.SUCCESS('✅ Migrações aplicadas com sucesso'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro ao aplicar migrações: {e}'))
            sys.exit(1)

        self.stdout.write('')

        # Verificar status final
        self.stdout.write('📋 Status final das migrações:')
        self.stdout.write('-' * 60)
        try:
            call_command('showmigrations', '--list')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro ao mostrar migrações: {e}'))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('✅ PROCESSO CONCLUÍDO'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
