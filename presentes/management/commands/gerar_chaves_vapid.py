"""
Gera o par de chaves VAPID para as notificacoes push

Uso:
    python manage.py gerar_chaves_vapid

Copie os valores para as variaveis VAPID_PUBLIC_KEY e VAPID_PRIVATE_KEY
do servidor. Trocar as chaves invalida as assinaturas ja feitas.
"""

from django.core.management.base import BaseCommand

from presentes.push import gerar_chaves_vapid


class Command(BaseCommand):
    help = 'Gera chaves VAPID (publica e privada) para Web Push'

    def handle(self, *args, **options):
        publica, privada = gerar_chaves_vapid()
        self.stdout.write(f'VAPID_PUBLIC_KEY={publica}')
        self.stdout.write(f'VAPID_PRIVATE_KEY={privada}')
