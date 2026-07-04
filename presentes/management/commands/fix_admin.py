"""
Django management command para corrigir permissões de admin

Uso:
    python manage.py fix_admin
"""

import os

from django.core.management.base import BaseCommand
from presentes.models import Usuario


class Command(BaseCommand):
    help = 'Garante o superusuário admin (email/senha via env vars)'

    def handle(self, *args, **options):
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'maxwbh@gmail.com')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'a')
        # Por padrão NÃO sobrescreve a senha de um admin já existente.
        # Defina RESET_ADMIN_PASSWORD=true para forçar o reset no deploy.
        reset_password = os.environ.get('RESET_ADMIN_PASSWORD', 'false').lower() == 'true'

        self.stdout.write(self.style.WARNING(f'Buscando usuário {email}...'))

        try:
            user = Usuario.objects.get(email=email)

            self.stdout.write(self.style.SUCCESS(f'✅ Usuário encontrado: {user.username}'))
            self.stdout.write(f'   Email: {user.email}')
            self.stdout.write(f'   Superuser ANTES: {user.is_superuser}')
            self.stdout.write(f'   Staff ANTES: {user.is_staff}')
            self.stdout.write(f'   Active ANTES: {user.is_active}')

            # Atualizar permissões
            user.is_superuser = True
            user.is_staff = True
            user.is_active = True
            if reset_password:
                user.set_password(password)
            user.save()

            self.stdout.write(self.style.SUCCESS(f'\n✅ Permissões atualizadas!'))
            self.stdout.write(f'   Superuser DEPOIS: {user.is_superuser}')
            self.stdout.write(f'   Staff DEPOIS: {user.is_staff}')
            self.stdout.write(f'   Active DEPOIS: {user.is_active}')
            if reset_password:
                self.stdout.write(self.style.WARNING('   Senha redefinida (RESET_ADMIN_PASSWORD=true)'))
            else:
                self.stdout.write('   Senha mantida (defina RESET_ADMIN_PASSWORD=true para redefinir)')

            self.stdout.write(self.style.SUCCESS(f'\n🎉 Usuário {email} agora tem acesso ao admin!'))
            self.stdout.write(self.style.HTTP_INFO('🌐 Acesse: https://lista-presentes-0hbp.onrender.com/admin/'))

        except Usuario.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'❌ Usuário {email} não existe!'))
            self.stdout.write(self.style.WARNING('Criando novo superusuário...'))

            user = Usuario.objects.create_superuser(
                email=email,
                username='maxwbh',
                password=password,
                first_name='Max',
                last_name='WBH'
            )

            self.stdout.write(self.style.SUCCESS(f'✅ Superusuário criado!'))
            self.stdout.write(f'   Username: {user.username}')
            self.stdout.write(f'   Email: {user.email}')
            self.stdout.write(f'   Senha: {password}')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro: {str(e)}'))
            raise
