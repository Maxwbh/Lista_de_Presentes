"""
Mostra os horarios mais acessados e sugere o cron do keep-alive

Uso:
    python manage.py analisar_acessos [--dias 30] [--limite 5]
"""

from django.core.management.base import BaseCommand

from presentes.acessos import resumo_acessos


class Command(BaseCommand):
    help = 'Analisa acessos por hora e despertares do servidor e sugere o cron do keep-alive'

    def add_arguments(self, parser):
        parser.add_argument('--dias', type=int, default=30)
        parser.add_argument('--limite', type=float, default=5.0,
                            help='Percentual minimo de acessos para a hora ser pico')

    def handle(self, *args, **options):
        resumo = resumo_acessos(dias=options['dias'], limite_percentual=options['limite'])
        total = resumo['total_acessos']

        self.stdout.write(f"Acessos nos ultimos {resumo['periodo_dias']} dias: {total}\n")
        maior = max(resumo['acessos_por_hora']) or 1
        for hora, acessos in enumerate(resumo['acessos_por_hora']):
            barra = '#' * round(acessos * 40 / maior)
            pico = ' <- pico' if hora in resumo['horas_pico'] else ''
            self.stdout.write(f"{hora:02d}h {acessos:6d} {barra}{pico}")

        despertares = resumo['despertares']
        self.stdout.write(
            f"\nDespertares: {despertares['total']} "
            f"({despertares['por_usuario']} por usuario, {despertares['por_monitor']} por monitor)"
        )
        self.stdout.write(f"Faixas para manter acordado: {', '.join(resumo['faixas_sugeridas_local']) or '-'}")
        self.stdout.write("Cron sugerido para .github/workflows/keep-alive.yml (UTC):")
        for cron in resumo['cron_keep_alive_utc']:
            self.stdout.write(f"    - cron: '{cron}'")
