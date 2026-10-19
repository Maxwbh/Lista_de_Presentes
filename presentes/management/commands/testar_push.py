"""
Envia uma notificacao push de teste para um usuario

Uso:
    python manage.py testar_push email@exemplo.com
"""

from django.core.management.base import BaseCommand, CommandError

from presentes.models import Usuario
from presentes.push import enviar_push, push_configurado


class Command(BaseCommand):
    help = 'Envia uma notificacao push de teste para o usuario informado'

    def add_arguments(self, parser):
        parser.add_argument('email')

    def handle(self, *args, **options):
        if not push_configurado():
            raise CommandError('Configure VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY e VAPID_ADMIN_EMAIL.')

        usuario = Usuario.objects.filter(email=options['email']).first()
        if not usuario:
            raise CommandError(f"Usuario {options['email']} nao encontrado.")

        total = usuario.push_subscriptions.count()
        entregues = enviar_push(usuario, '🔔 Notificação de teste da Lista de Presentes.')
        self.stdout.write(f'Push entregue em {entregues} de {total} navegador(es).')
