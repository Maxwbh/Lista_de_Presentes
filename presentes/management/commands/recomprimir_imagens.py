"""
Reduz as imagens que ja estao gravadas no banco.

As imagens novas ja chegam reduzidas (ver presentes/imagens.py), mas as
antigas continuam com o tamanho original: fotos de varios MB em base64, que
pesam no egress do Supabase toda vez que alguem abre a imagem. Este comando
passa por cada imagem de presente, grupo e foto de usuario, uma por vez, e
grava a versao reduzida (no maximo 800 px, WebP) quando ela for menor.

No deploy isto roda sozinho uma vez, pela migracao
0015_recomprimir_imagens_existentes (o Render Free nao tem console). O
comando serve para rodar de novo quando quiser, da sua maquina com a
DATABASE_URL do Supabase:
    python manage.py recomprimir_imagens --dry-run   # so mostra o antes e depois
    python manage.py recomprimir_imagens             # grava
"""
from django.core.management.base import BaseCommand

from presentes.imagens import recomprimir_registros
from presentes.models import Grupo, Presente, Usuario

ALVOS = (
    # (modelo, coluna base64, coluna do tipo, coluna da versao, coluna do nome)
    (Presente, 'imagem_base64', 'imagem_tipo', 'imagem_versao', 'imagem_nome'),
    (Grupo, 'imagem_base64', 'imagem_tipo', 'imagem_versao', 'imagem_nome'),
    (Usuario, 'foto_base64', 'foto_tipo', 'foto_versao', None),
)


def _kb(n):
    return f'{n / 1024:,.0f} KB'.replace(',', '.')


class Command(BaseCommand):
    help = 'Reduz (800 px, WebP) as imagens em base64 ja gravadas no banco'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true',
                            help='So mostra o tamanho antes e depois, sem gravar nada.')

    def handle(self, *args, **options):
        simular = options['dry_run']
        totais = recomprimir_registros(ALVOS, simular=simular, escrever=self.stdout.write)
        acao = 'Seriam reduzidas' if simular else 'Reduzidas'
        mantidas = totais['mantidas']
        self.stdout.write(self.style.SUCCESS(
            f"{acao} {totais['alteradas']} imagem(ns): {_kb(totais['antes'])} -> {_kb(totais['depois'])}"
            + (f' ({mantidas} mantida(s) por não serem imagens aceitas)' if mantidas else '')
        ))
        if simular:
            self.stdout.write('Nada foi gravado (--dry-run).')
