"""
Comando para executar a pesquisa de preços de todos os presentes ativos.

Uso:
    python manage.py pesquisar_precos            # respeita o intervalo de 7 dias
    python manage.py pesquisar_precos --forcar   # executa imediatamente
"""

from django.core.management.base import BaseCommand

from presentes.pesquisa_precos import executar_pesquisa, pesquisa_em_atraso


class Command(BaseCommand):
    help = 'Pesquisa preços de todos os presentes ativos e alimenta o histórico (temperatura de preços)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--forcar',
            action='store_true',
            help='Executa mesmo que a última pesquisa tenha menos de 7 dias'
        )

    def handle(self, *args, **options):
        if not options['forcar'] and not pesquisa_em_atraso():
            self.stdout.write(self.style.WARNING(
                'Última pesquisa tem menos de 7 dias. Use --forcar para executar mesmo assim.'
            ))
            return

        self.stdout.write('Iniciando pesquisa de preços...')
        log = executar_pesquisa(origem='comando')
        self.stdout.write(self.style.SUCCESS(
            f'Pesquisa concluída: {log.sucessos} sucessos, {log.erros} erros '
            f'de {log.total_presentes} presentes.'
        ))
