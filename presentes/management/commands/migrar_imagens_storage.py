"""
Leva para o Supabase Storage as imagens que ainda estão no banco (base64).

Roda no deploy (build.sh), porque o Render Free não tem console: sem o
Storage configurado ou sem imagens no banco, não faz nada. Cria o bucket
privado se precisar, envia uma imagem por vez e só então apaga o base64 da
linha. A versão da imagem não muda, então URLs e caches do navegador seguem
valendo. Se um envio falhar, a imagem continua no banco e o comando tenta
de novo no próximo deploy.

Uso:
    python manage.py migrar_imagens_storage --dry-run   # só conta
    python manage.py migrar_imagens_storage
"""
import base64

from django.core.management.base import BaseCommand

from presentes import storage
from presentes.models import Grupo, Presente, Usuario
from presentes.rede import EXTENSOES

ALVOS = (
    (Presente, 'imagem_base64', 'imagem_tipo', 'imagem_storage'),
    (Grupo, 'imagem_base64', 'imagem_tipo', 'imagem_storage'),
    (Usuario, 'foto_base64', 'foto_tipo', 'foto_storage'),
)


class Command(BaseCommand):
    help = 'Move as imagens em base64 do banco para o Supabase Storage'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Só conta, sem enviar nada.')

    def handle(self, *args, **options):
        if not storage.configurado():
            self.stdout.write('Storage não configurado (SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY): '
                              'as imagens continuam no banco.')
            return

        pendentes = []
        for modelo, campo, campo_tipo, campo_storage in ALVOS:
            pks = list(modelo.objects.exclude(**{f'{campo}__isnull': True}).exclude(**{campo: ''})
                       .order_by('pk').values_list('pk', flat=True))
            pendentes.append((modelo, campo, campo_tipo, campo_storage, pks))
        total = sum(len(p[-1]) for p in pendentes)
        if not total:
            self.stdout.write('Nenhuma imagem no banco para levar ao Storage.')
            return
        if options['dry_run']:
            for modelo, *_, pks in pendentes:
                self.stdout.write(f'{modelo.__name__}: {len(pks)} imagem(ns) no banco')
            self.stdout.write('Nada foi enviado (--dry-run).')
            return

        if storage.garantir_bucket():
            self.stdout.write('Bucket criado.')
        enviadas = falhas = bytes_movidos = 0
        for modelo, campo, campo_tipo, campo_storage, pks in pendentes:
            pasta = modelo._meta.model_name
            for pk in pks:
                linha = modelo.objects.filter(pk=pk).values(campo, campo_tipo).first()
                if not linha or not linha[campo]:
                    continue
                tipo = (linha[campo_tipo] or 'image/jpeg').lower()
                if tipo not in EXTENSOES:
                    self.stdout.write(self.style.WARNING(f'  {pasta} #{pk}: tipo {tipo} não aceito, mantido'))
                    falhas += 1
                    continue
                caminho = storage.novo_caminho(pasta, EXTENSOES[tipo])
                try:
                    storage.enviar(caminho, base64.b64decode(linha[campo]), tipo)
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'  {pasta} #{pk}: {e}'))
                    falhas += 1
                    continue
                # Só apaga do banco depois que o arquivo está no Storage
                modelo.objects.filter(pk=pk).update(**{campo_storage: caminho, campo: None})
                enviadas += 1
                bytes_movidos += len(linha[campo])

        self.stdout.write(self.style.SUCCESS(
            f'{enviadas} imagem(ns) levadas ao Storage ({bytes_movidos // 1024} KB a menos no banco)'
            + (f'; {falhas} ficaram no banco' if falhas else '')
        ))
