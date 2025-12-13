from django.core.management.base import BaseCommand
from django.db import transaction
from presentes.models import Usuario, Grupo, GrupoMembro


class Command(BaseCommand):
    help = 'Cria grupo padrao Natal Familia Cruz e Credos 2025 e adiciona todos os usuarios'

    def handle(self, *args, **options):
        """Cria grupo padrao e adiciona todos os usuarios"""
        
        try:
            with transaction.atomic():
                # Verificar se o grupo ja existe
                grupo, criado = Grupo.objects.get_or_create(
                    nome='Natal Família Cruz e Credos 2025',
                    defaults={
                        'descricao': 'Grupo padrão para organizar os presentes de Natal da família',
                        'ativo': True,
                    }
                )

                if criado:
                    self.stdout.write(self.style.SUCCESS(f'✓ Grupo "{grupo.nome}" criado com sucesso!'))
                    self.stdout.write(f'  Código de convite: {grupo.codigo_convite}')
                else:
                    self.stdout.write(self.style.WARNING(f'⚠ Grupo "{grupo.nome}" já existia'))

                # Buscar todos os usuarios
                usuarios = Usuario.objects.all()
                total_usuarios = usuarios.count()

                if total_usuarios == 0:
                    self.stdout.write(self.style.WARNING('⚠ Nenhum usuário encontrado no sistema'))
                    return

                self.stdout.write(f'\n📊 Encontrados {total_usuarios} usuários')

                # Contadores
                adicionados = 0
                ja_membros = 0
                mantenedores = 0

                # Adicionar cada usuario ao grupo
                for usuario in usuarios:
                    # Verificar se ja e membro
                    membro, criado_membro = GrupoMembro.objects.get_or_create(
                        grupo=grupo,
                        usuario=usuario,
                        defaults={
                            'e_mantenedor': usuario.is_superuser  # Admins viram mantenedores
                        }
                    )

                    if criado_membro:
                        adicionados += 1
                        if usuario.is_superuser:
                            mantenedores += 1
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'  ✓ {usuario.email} adicionado como MANTENEDOR'
                                )
                            )
                        else:
                            self.stdout.write(f'  + {usuario.email} adicionado como membro')
                    else:
                        ja_membros += 1
                        # Atualizar para mantenedor se for superuser e ainda nao for
                        if usuario.is_superuser and not membro.e_mantenedor:
                            membro.e_mantenedor = True
                            membro.save()
                            mantenedores += 1
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'  ↑ {usuario.email} promovido a MANTENEDOR'
                                )
                            )
                        else:
                            self.stdout.write(
                                self.style.WARNING(f'  = {usuario.email} já era membro')
                            )

                    # Definir como grupo ativo se o usuario nao tiver um
                    if not usuario.grupo_ativo:
                        usuario.grupo_ativo = grupo
                        usuario.save()
                        self.stdout.write(f'    → Definido como grupo ativo para {usuario.email}')

                # Resumo final
                self.stdout.write('\n' + '='*70)
                self.stdout.write(self.style.SUCCESS('\n✅ OPERAÇÃO CONCLUÍDA COM SUCESSO!\n'))
                self.stdout.write(f'📋 Resumo:')
                self.stdout.write(f'  • Grupo: {grupo.nome}')
                self.stdout.write(f'  • Total de usuários: {total_usuarios}')
                self.stdout.write(f'  • Novos membros adicionados: {adicionados}')
                self.stdout.write(f'  • Já eram membros: {ja_membros}')
                self.stdout.write(f'  • Mantenedores (admins): {mantenedores}')
                self.stdout.write(f'  • Código de convite: {grupo.codigo_convite}')
                self.stdout.write(f'  • Link de convite: {grupo.get_link_convite()}')
                self.stdout.write('='*70 + '\n')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro ao criar grupo: {str(e)}'))
            raise
