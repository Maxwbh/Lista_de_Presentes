from django.core.management.base import BaseCommand
from django.db import transaction
from presentes.models import Grupo, Presente, Compra, Notificacao, SugestaoCompra


class Command(BaseCommand):
    help = 'Migra dados existentes (sem grupo) para o grupo padrao'

    def add_arguments(self, parser):
        parser.add_argument(
            '--grupo-nome',
            type=str,
            default='Natal Família Cruz e Credos 2025',
            help='Nome do grupo para migrar os dados'
        )

    def handle(self, *args, **options):
        """Migra dados existentes para o grupo padrao"""
        
        grupo_nome = options['grupo_nome']

        try:
            # Buscar o grupo
            try:
                grupo = Grupo.objects.get(nome=grupo_nome)
                self.stdout.write(self.style.SUCCESS(f'✓ Grupo encontrado: {grupo.nome}'))
            except Grupo.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(
                        f'❌ Grupo "{grupo_nome}" não encontrado. '
                        f'Execute primeiro: python manage.py criar_grupo_padrao'
                    )
                )
                return

            with transaction.atomic():
                # Migrar Presentes
                presentes_sem_grupo = Presente.objects.filter(grupo__isnull=True)
                total_presentes = presentes_sem_grupo.count()
                
                if total_presentes > 0:
                    presentes_sem_grupo.update(grupo=grupo)
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ {total_presentes} presentes migrados para o grupo'
                        )
                    )
                else:
                    self.stdout.write('  → Todos os presentes já têm grupo')

                # Migrar Compras
                compras_sem_grupo = Compra.objects.filter(grupo__isnull=True)
                total_compras = compras_sem_grupo.count()
                
                if total_compras > 0:
                    compras_sem_grupo.update(grupo=grupo)
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ {total_compras} compras migradas para o grupo'
                        )
                    )
                else:
                    self.stdout.write('  → Todas as compras já têm grupo')

                # Migrar Notificacoes
                notificacoes_sem_grupo = Notificacao.objects.filter(grupo__isnull=True)
                total_notificacoes = notificacoes_sem_grupo.count()
                
                if total_notificacoes > 0:
                    notificacoes_sem_grupo.update(grupo=grupo)
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ {total_notificacoes} notificações migradas para o grupo'
                        )
                    )
                else:
                    self.stdout.write('  → Todas as notificações já têm grupo')

                # Migrar Sugestoes de Compra
                sugestoes_sem_grupo = SugestaoCompra.objects.filter(grupo__isnull=True)
                total_sugestoes = sugestoes_sem_grupo.count()
                
                if total_sugestoes > 0:
                    sugestoes_sem_grupo.update(grupo=grupo)
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ {total_sugestoes} sugestões migradas para o grupo'
                        )
                    )
                else:
                    self.stdout.write('  → Todas as sugestões já têm grupo')

                # Resumo final
                total_migrado = total_presentes + total_compras + total_notificacoes + total_sugestoes
                
                self.stdout.write('\n' + '='*70)
                self.stdout.write(self.style.SUCCESS('\n✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!\n'))
                self.stdout.write(f'📋 Resumo:')
                self.stdout.write(f'  • Grupo destino: {grupo.nome}')
                self.stdout.write(f'  • Presentes migrados: {total_presentes}')
                self.stdout.write(f'  • Compras migradas: {total_compras}')
                self.stdout.write(f'  • Notificações migradas: {total_notificacoes}')
                self.stdout.write(f'  • Sugestões migradas: {total_sugestoes}')
                self.stdout.write(f'  • TOTAL: {total_migrado} registros')
                self.stdout.write('='*70 + '\n')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro ao migrar dados: {str(e)}'))
            raise
