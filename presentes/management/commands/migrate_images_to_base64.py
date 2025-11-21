from django.core.management.base import BaseCommand
from presentes.models import Presente
import requests
import base64
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Migra imagens antigas de presentes para armazenamento base64'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Executa sem salvar alterações',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('Modo DRY RUN - nenhuma alteração será salva'))

        # Encontrar presentes com URL mas sem imagem base64
        presentes_sem_base64 = Presente.objects.filter(
            url__isnull=False
        ).exclude(url='').filter(imagem_base64__isnull=True)

        total = presentes_sem_base64.count()
        self.stdout.write(f'Encontrados {total} presentes com URL para processar')

        success_count = 0
        error_count = 0

        for presente in presentes_sem_base64:
            try:
                # Tentar baixar a imagem da URL
                self.stdout.write(f'Processando presente {presente.id}: {presente.descricao}')

                if not presente.url:
                    self.stdout.write(self.style.WARNING(f'  Presente {presente.id} sem URL'))
                    error_count += 1
                    continue

                # Baixar imagem
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }

                response = requests.get(presente.url, headers=headers, timeout=10)
                response.raise_for_status()

                # Verificar se é uma imagem
                content_type = response.headers.get('content-type', '')
                if not content_type.startswith('image/'):
                    self.stdout.write(
                        self.style.WARNING(f'  URL não é uma imagem: {content_type}')
                    )
                    error_count += 1
                    continue

                # Converter para base64
                imagem_data = response.content
                imagem_base64 = base64.b64encode(imagem_data).decode('utf-8')

                # Extrair nome do arquivo da URL
                nome_arquivo = presente.url.split('/')[-1].split('?')[0]
                if not nome_arquivo:
                    nome_arquivo = f'imagem_{presente.id}.jpg'

                # Salvar
                if not dry_run:
                    presente.imagem_base64 = imagem_base64
                    presente.imagem_nome = nome_arquivo
                    presente.imagem_tipo = content_type
                    presente.imagem = None  # Limpar campo antigo
                    presente.save()

                success_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ Imagem convertida ({len(imagem_data)} bytes)')
                )

            except requests.exceptions.RequestException as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Erro ao baixar imagem: {str(e)}')
                )
                logger.error(f'Erro ao migrar imagem do presente {presente.id}: {str(e)}')
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Erro inesperado: {str(e)}')
                )
                logger.error(f'Erro ao migrar presente {presente.id}: {str(e)}')

        # Resumo
        self.stdout.write('\n' + '='*50)
        self.stdout.write(f'Total de presentes: {total}')
        self.stdout.write(self.style.SUCCESS(f'Sucesso: {success_count}'))
        self.stdout.write(self.style.ERROR(f'Erros: {error_count}'))

        if dry_run:
            self.stdout.write(self.style.WARNING('\nNENHUMA ALTERAÇÃO FOI SALVA (modo dry-run)'))
        else:
            self.stdout.write(self.style.SUCCESS('\nMigração concluída!'))
