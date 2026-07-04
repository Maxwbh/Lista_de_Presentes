"""
Valida as credenciais de login social configuradas.

Uso:
    python manage.py validar_social             # valida online contra cada provedor
    python manage.py validar_social --formato   # só checagem de formato (sem rede)
"""

from django.core.management.base import BaseCommand

from presentes.social_validation import validar_todos

NOMES = {
    'google': 'Google',
    'facebook': 'Facebook',
    'linkedin_oauth2': 'LinkedIn',
    'apple': 'Apple',
}


class Command(BaseCommand):
    help = 'Valida as credenciais dos provedores de login social (Google, Facebook, LinkedIn, Apple)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--formato',
            action='store_true',
            help='Apenas validação de formato, sem chamadas de rede'
        )

    def handle(self, *args, **options):
        online = not options['formato']
        modo = 'online (contra a API de cada provedor)' if online else 'de formato (sem rede)'
        self.stdout.write(f'Validação {modo}:\n')

        resultados = validar_todos(online=online)
        algum_valido = False

        for provider, (configurado, ok, msg) in resultados.items():
            nome = NOMES.get(provider, provider)
            if not configurado:
                self.stdout.write(f'  ⚪ {nome:10s} — não configurado (botão oculto no login)')
            elif ok:
                algum_valido = True
                self.stdout.write(self.style.SUCCESS(f'  ✅ {nome:10s} — {msg}'))
            else:
                self.stdout.write(self.style.ERROR(f'  ❌ {nome:10s} — {msg} (botão oculto no login)'))

        self.stdout.write('')
        if algum_valido:
            self.stdout.write(self.style.SUCCESS('Pelo menos um provedor está válido — botões correspondentes aparecem no login.'))
        else:
            self.stdout.write(self.style.WARNING(
                'Nenhum provedor válido — a seção de login social fica oculta.\n'
                'Configure as env vars (ex.: GOOGLE_CLIENT_ID/GOOGLE_CLIENT_SECRET) e rode novamente.'
            ))
