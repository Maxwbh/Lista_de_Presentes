"""
Django management command para corrigir permissões de admin

Uso:
    python manage.py fix_admin
"""

from django.core.management.base import BaseCommand
from presentes.models import Usuario


class Command(BaseCommand):
    help = 'Corrige permissões de admin para maxwbh@gmail.com'

    def handle(self, *args, **options):
        email = 'maxwbh@gmail.com'
        password = 'a'

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
            user.set_password(password)
            user.save()

            self.stdout.write(self.style.SUCCESS(f'\n✅ Permissões atualizadas!'))
            self.stdout.write(f'   Superuser DEPOIS: {user.is_superuser}')
            self.stdout.write(f'   Staff DEPOIS: {user.is_staff}')
            self.stdout.write(f'   Active DEPOIS: {user.is_active}')
            self.stdout.write(f'   Senha resetada para: {password}')

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
