"""
Remove do historico os precos que vieram de produto errado.

A busca de preco aceitava qualquer resultado da pagina de busca, sem conferir
se era mesmo o produto do presente. O preco errado ia para o historico e
estourava a temperatura do card - um item de R$ 28 aparecia como "Preco alto
(+684%)" por causa de um ponto de R$ 219 de um produto sem nenhuma relacao.

O filtro de relevancia impede novos casos, mas nao desfaz o que ja foi gravado.
Este comando limpa esses pontos.

Como o historico nao guarda o titulo do produto, nao da para reaplicar o filtro
de relevancia sobre o passado. O criterio aqui e a distancia do preco de
referencia do presente (o valor que o dono cadastrou): um ponto muito acima ou
muito abaixo dele quase sempre e de outro produto.

Uso:
    python manage.py limpar_historico_precos              # so relatorio
    python manage.py limpar_historico_precos --aplicar    # remove de fato
    python manage.py limpar_historico_precos --fator 5    # criterio mais frouxo
    python manage.py limpar_historico_precos --presente 42
"""
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from presentes.models import Presente, PrecoHistorico, SugestaoCompra

FATOR_PADRAO = 3.0


class Command(BaseCommand):
    help = 'Remove do historico os precos incompativeis com o preco de referencia do presente'

    def add_arguments(self, parser):
        parser.add_argument(
            '--aplicar', action='store_true',
            help='Remove de fato. Sem esta opcao o comando so mostra o que seria removido.',
        )
        parser.add_argument(
            '--fator', type=float, default=FATOR_PADRAO,
            help=f'Quantas vezes o preco pode se afastar da referencia antes de virar suspeito '
                 f'(padrao: {FATOR_PADRAO}).',
        )
        parser.add_argument(
            '--presente', type=int, default=None,
            help='Limita a um presente especifico, pelo id.',
        )
        parser.add_argument(
            '--sugestoes', action='store_true',
            help='Remove tambem as sugestoes sem titulo de produto, gravadas antes do '
                 'filtro de relevancia e impossiveis de conferir.',
        )

    def handle(self, *args, **opcoes):
        fator = opcoes['fator']
        if fator <= 1:
            raise CommandError('O fator precisa ser maior que 1.')

        aplicar = opcoes['aplicar']
        presentes = Presente.objects.exclude(preco__isnull=True).prefetch_related('historico_precos')
        if opcoes['presente']:
            presentes = presentes.filter(pk=opcoes['presente'])
            if not presentes.exists():
                raise CommandError(f"Presente {opcoes['presente']} nao existe ou nao tem preco de referencia.")

        ids_suspeitos = []
        presentes_afetados = 0

        for presente in presentes:
            referencia = Decimal(presente.preco)
            if referencia <= 0:
                continue

            teto = referencia * Decimal(str(fator))
            piso = referencia / Decimal(str(fator))

            suspeitos = [
                ponto for ponto in presente.historico_precos.all()
                if ponto.preco is not None and (ponto.preco > teto or ponto.preco < piso)
            ]
            if not suspeitos:
                continue

            presentes_afetados += 1
            ids_suspeitos.extend(p.id for p in suspeitos)

            self.stdout.write(
                f'\nPresente {presente.id}: {presente.descricao[:60]}'
            )
            self.stdout.write(
                f'  referencia R$ {referencia} | aceitavel entre '
                f'R$ {piso.quantize(Decimal("0.01"))} e R$ {teto.quantize(Decimal("0.01"))}'
            )
            for ponto in suspeitos:
                self.stdout.write(
                    f'  - R$ {ponto.preco} ({ponto.loja or "sem loja"}, '
                    f'{ponto.fonte}, {ponto.data:%d/%m/%Y})'
                )

        # A limpeza das sugestoes nao depende de haver preco suspeito: sao
        # dois estragos diferentes do mesmo bug.
        sugestoes_sem_titulo = SugestaoCompra.objects.filter(titulo_produto='')
        if opcoes['presente']:
            sugestoes_sem_titulo = sugestoes_sem_titulo.filter(presente_id=opcoes['presente'])
        total_sugestoes = sugestoes_sem_titulo.count() if opcoes['sugestoes'] else 0

        if not ids_suspeitos and not total_sugestoes:
            self.stdout.write(self.style.SUCCESS('\nNada a limpar.'))
            return

        self.stdout.write('')
        if ids_suspeitos:
            self.stdout.write(
                f'{len(ids_suspeitos)} ponto(s) de preco suspeito(s) em {presentes_afetados} presente(s).'
            )
        if opcoes['sugestoes']:
            self.stdout.write(f'{total_sugestoes} sugestao(oes) sem titulo de produto.')

        if not aplicar:
            self.stdout.write(self.style.WARNING(
                '\nNada foi removido. Rode de novo com --aplicar para efetivar.'
            ))
            return

        with transaction.atomic():
            removidos = 0
            if ids_suspeitos:
                removidos, _ = PrecoHistorico.objects.filter(id__in=ids_suspeitos).delete()
            if opcoes['sugestoes']:
                sugestoes_sem_titulo.delete()

        self.stdout.write('')
        if removidos:
            self.stdout.write(self.style.SUCCESS(f'{removidos} registro(s) de historico removido(s).'))
        if opcoes['sugestoes']:
            self.stdout.write(self.style.SUCCESS(f'{total_sugestoes} sugestao(oes) removida(s).'))
