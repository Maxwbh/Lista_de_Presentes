import logging
import threading

from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.db import connection
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import path, reverse
from django.utils import timezone
from .models import Usuario, Presente, Compra, SugestaoCompra, Notificacao, Grupo, GrupoMembro, PrecoHistorico, PesquisaPrecoLog
from .models import AcessoHora, DespertarServidor

logger = logging.getLogger(__name__)

# Ate este numero de presentes a busca de imagens roda na hora e mostra o
# resultado; acima disso roda em segundo plano para nao estourar o tempo
# limite da requisicao (cada leitura de site pode levar alguns segundos)
LIMITE_BUSCA_IMAGEM_NA_HORA = 5

SEM_IMAGEM = (Q(imagem_base64__isnull=True) | Q(imagem_base64='')) & (Q(imagem__isnull=True) | Q(imagem=''))
COM_LINK = Q(url__isnull=False) & ~Q(url='')


def _buscar_imagens(ids):
    """
    Busca no site (link original) a imagem de cada presente; quem estiver sem
    preco ganha tambem o preco lido. Retorna (imagens, precos) encontrados.
    """
    from .services import IAService

    imagens = precos = 0
    for presente in Presente.objects.filter(pk__in=ids):
        sem_preco = presente.preco is None
        if IAService.buscar_imagem_para_presente(presente):
            imagens += 1
        if sem_preco and presente.preco is not None:
            precos += 1
    logger.info(f"[IMAGENS] Busca no site: {imagens} imagens e {precos} preços para {len(ids)} presentes")
    return imagens, precos


def _buscar_imagens_em_segundo_plano(ids):
    def executar():
        try:
            _buscar_imagens(ids)
        except Exception:
            logger.exception("[IMAGENS] Erro na busca de imagens em segundo plano")
        finally:
            connection.close()

    threading.Thread(target=executar, daemon=True).start()


class TemImagemFilter(admin.SimpleListFilter):
    title = 'imagem'
    parameter_name = 'tem_imagem'

    def lookups(self, request, model_admin):
        return [('sim', 'Com imagem'), ('nao', 'Sem imagem')]

    def queryset(self, request, queryset):
        if self.value() == 'nao':
            return queryset.filter(SEM_IMAGEM)
        if self.value() == 'sim':
            return queryset.exclude(SEM_IMAGEM)
        return queryset


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    """Admin customizado para o modelo Usuario"""
    list_display = ['email', 'username', 'first_name', 'last_name', 'grupo_ativo', 'ativo', 'data_cadastro']
    list_filter = ['ativo', 'grupo_ativo', 'is_staff', 'is_superuser', 'data_cadastro']
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering = ['-data_cadastro']

    fieldsets = UserAdmin.fieldsets + (
        ('Informações Adicionais', {
            'fields': ('telefone', 'ativo', 'grupo_ativo', 'data_cadastro')
        }),
    )

    readonly_fields = ['data_cadastro', 'last_login', 'date_joined']
    actions = ['gerar_link_redefinicao_senha']

    @admin.action(description='Gerar link de redefinição de senha')
    def gerar_link_redefinicao_senha(self, request, queryset):
        """Link para o usuário criar uma senha nova, para enviar por WhatsApp (sem precisar de e-mail)"""
        from django.contrib import messages
        from .senha import link_redefinicao

        for usuario in queryset:
            link = link_redefinicao(usuario, base_url=request.build_absolute_uri('/'))
            self.message_user(
                request,
                f'{usuario.get_full_name() or usuario.email}: {link} (vale 24 horas e uma única vez)',
                messages.INFO,
            )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        # Otimizar query
        return queryset.prefetch_related('presentes', 'compras_realizadas', 'notificacoes')


@admin.register(Presente)
class PresenteAdmin(admin.ModelAdmin):
    """Admin para gerenciar Presentes"""
    list_display = ['descricao_curta', 'usuario', 'preco', 'status', 'com_imagem', 'ultima_busca_imagem',
                    'tem_sugestoes', 'data_cadastro']
    list_filter = ['status', TemImagemFilter, 'data_cadastro']
    actions = ['buscar_imagem_no_site']
    change_list_template = 'admin/presentes/presente/change_list.html'
    search_fields = ['descricao', 'usuario__email', 'usuario__first_name', 'usuario__last_name']
    ordering = ['-data_cadastro']
    date_hierarchy = 'data_cadastro'

    fieldsets = (
        ('Informações do Presente', {
            'fields': ('usuario', 'descricao', 'imagem')
        }),
        ('Detalhes', {
            'fields': ('url', 'preco', 'status')
        }),
        ('Metadata', {
            'fields': ('data_cadastro',),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['data_cadastro']

    def descricao_curta(self, obj):
        """Mostrar descrição resumida"""
        return obj.descricao[:50] + '...' if len(obj.descricao) > 50 else obj.descricao
    descricao_curta.short_description = 'Descrição'

    @admin.display(description='Imagem', boolean=True)
    def com_imagem(self, obj):
        return obj.tem_imagem()

    @admin.display(description='Última busca de imagem', ordering='busca_imagem_em')
    def ultima_busca_imagem(self, obj):
        if not obj.busca_imagem_em:
            return '-'
        return f"{timezone.localtime(obj.busca_imagem_em):%d/%m %H:%M} · {obj.busca_imagem_resultado}"

    def get_urls(self):
        urls = [
            path('buscar-imagens/', self.admin_site.admin_view(self.buscar_imagens_faltantes_view),
                 name='presentes_presente_buscar_imagens'),
        ]
        return urls + super().get_urls()

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['total_sem_imagem'] = Presente.objects.filter(SEM_IMAGEM & COM_LINK).count()
        return super().changelist_view(request, extra_context=extra_context)

    def _buscar(self, request, queryset):
        ids = list(queryset.filter(SEM_IMAGEM & COM_LINK).values_list('pk', flat=True))
        if not ids:
            self.message_user(request, 'Nenhum presente sem imagem e com link para buscar.', messages.INFO)
        elif len(ids) <= LIMITE_BUSCA_IMAGEM_NA_HORA:
            imagens, precos = _buscar_imagens(ids)
            mensagem = f'{imagens} de {len(ids)} presente(s) ganharam imagem buscada no site.'
            if precos:
                mensagem += f' {precos} ganharam também o preço que faltava.'
            self.message_user(request, mensagem, messages.SUCCESS if imagens else messages.WARNING)
            for presente in Presente.objects.filter(pk__in=ids).filter(SEM_IMAGEM):
                self.message_user(request, f'{presente.descricao[:60]}: {presente.busca_imagem_resultado}',
                                  messages.WARNING)
        else:
            _buscar_imagens_em_segundo_plano(ids)
            self.message_user(
                request,
                f'Busca de imagem iniciada para {len(ids)} presentes. Ela roda em segundo plano e '
                f'pode levar alguns minutos; recarregue a página e veja a coluna "Última busca de imagem".',
                messages.INFO,
            )

    @admin.action(description='Buscar imagem no site (link original)')
    def buscar_imagem_no_site(self, request, queryset):
        self._buscar(request, queryset)

    def buscar_imagens_faltantes_view(self, request):
        """Botao da lista: busca a imagem de todos os presentes sem imagem que tem link"""
        if request.method == 'POST':
            self._buscar(request, Presente.objects.all())
        return redirect(reverse('admin:presentes_presente_changelist') + '?tem_imagem=nao')

    def tem_sugestoes(self, obj):
        """Indicar se tem sugestões de compra"""
        count = obj.sugestoes.count()
        return f'✅ {count}' if count > 0 else '❌'
    tem_sugestoes.short_description = 'Sugestões IA'

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        # Otimizar query
        return queryset.select_related('usuario').prefetch_related('sugestoes')


@admin.register(Compra)
class CompraAdmin(admin.ModelAdmin):
    """Admin para gerenciar Compras"""
    list_display = ['presente_descricao', 'comprador', 'presente_usuario', 'data_compra']
    list_filter = ['data_compra']
    search_fields = ['presente__descricao', 'comprador__email', 'presente__usuario__email']
    ordering = ['-data_compra']
    date_hierarchy = 'data_compra'

    fields = ['presente', 'comprador', 'data_compra']
    readonly_fields = ['data_compra']

    def presente_descricao(self, obj):
        """Mostrar descrição do presente"""
        return obj.presente.descricao[:40] + '...' if len(obj.presente.descricao) > 40 else obj.presente.descricao
    presente_descricao.short_description = 'Presente'

    def presente_usuario(self, obj):
        """Mostrar quem pediu o presente"""
        return obj.presente.usuario
    presente_usuario.short_description = 'Pedido por'

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        # Otimizar query
        return queryset.select_related('presente', 'presente__usuario', 'comprador')


@admin.register(SugestaoCompra)
class SugestaoCompraAdmin(admin.ModelAdmin):
    """Admin para gerenciar Sugestões de Compra"""
    list_display = ['presente_descricao', 'local_compra', 'preco_sugerido', 'data_busca']
    list_filter = ['data_busca', 'local_compra']
    search_fields = ['presente__descricao', 'local_compra', 'url_compra']
    ordering = ['preco_sugerido', '-data_busca']
    date_hierarchy = 'data_busca'

    fieldsets = (
        ('Presente', {
            'fields': ('presente',)
        }),
        ('Sugestão', {
            'fields': ('local_compra', 'url_compra', 'preco_sugerido')
        }),
        ('Metadata', {
            'fields': ('data_busca',),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['data_busca']

    def presente_descricao(self, obj):
        """Mostrar descrição do presente"""
        return obj.presente.descricao[:30] + '...' if len(obj.presente.descricao) > 30 else obj.presente.descricao
    presente_descricao.short_description = 'Presente'

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        # Otimizar query
        return queryset.select_related('presente', 'presente__usuario')


@admin.register(Notificacao)
class NotificacaoAdmin(admin.ModelAdmin):
    """Admin para gerenciar Notificações"""
    list_display = ['usuario', 'mensagem_curta', 'lida', 'data_notificacao']
    list_filter = ['lida', 'data_notificacao']
    search_fields = ['usuario__email', 'mensagem']
    ordering = ['-data_notificacao']
    date_hierarchy = 'data_notificacao'

    fields = ['usuario', 'mensagem', 'lida', 'data_notificacao']
    readonly_fields = ['data_notificacao']

    actions = ['marcar_como_lida', 'marcar_como_nao_lida']

    def mensagem_curta(self, obj):
        """Mostrar mensagem resumida"""
        return obj.mensagem[:60] + '...' if len(obj.mensagem) > 60 else obj.mensagem
    mensagem_curta.short_description = 'Mensagem'

    def marcar_como_lida(self, request, queryset):
        """Action para marcar notificações como lidas"""
        updated = queryset.update(lida=True)
        self.message_user(request, f'{updated} notificação(ões) marcada(s) como lida(s).')
    marcar_como_lida.short_description = 'Marcar como lida'

    def marcar_como_nao_lida(self, request, queryset):
        """Action para marcar notificações como não lidas"""
        updated = queryset.update(lida=False)
        self.message_user(request, f'{updated} notificação(ões) marcada(s) como não lida(s).')
    marcar_como_nao_lida.short_description = 'Marcar como não lida'

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        # Otimizar query
        return queryset.select_related('usuario')


@admin.register(Grupo)
class GrupoAdmin(admin.ModelAdmin):
    """Admin para gerenciar Grupos"""
    list_display = ['nome', 'codigo_convite', 'ativo', 'total_membros', 'data_criacao']
    list_filter = ['ativo', 'data_criacao']
    search_fields = ['nome', 'descricao', 'codigo_convite']
    ordering = ['-data_criacao']
    date_hierarchy = 'data_criacao'

    fieldsets = (
        ('Informações do Grupo', {
            'fields': ('nome', 'descricao', 'ativo')
        }),
        ('Convite', {
            'fields': ('codigo_convite',)
        }),
        ('Metadata', {
            'fields': ('data_criacao',),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['codigo_convite', 'data_criacao']

    def total_membros(self, obj):
        """Mostrar total de membros do grupo"""
        return obj.membros.count()
    total_membros.short_description = 'Membros'

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.prefetch_related('membros')


@admin.register(GrupoMembro)
class GrupoMembroAdmin(admin.ModelAdmin):
    """Admin para gerenciar Membros de Grupos"""
    list_display = ['usuario', 'grupo', 'e_mantenedor', 'data_entrada']
    list_filter = ['e_mantenedor', 'data_entrada', 'grupo']
    search_fields = ['usuario__email', 'usuario__first_name', 'grupo__nome']
    ordering = ['-data_entrada']
    date_hierarchy = 'data_entrada'

    fields = ['grupo', 'usuario', 'e_mantenedor', 'data_entrada']
    readonly_fields = ['data_entrada']

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('grupo', 'usuario')


@admin.register(PrecoHistorico)
class PrecoHistoricoAdmin(admin.ModelAdmin):
    """Admin do histórico de preços (temperatura de preços)"""
    list_display = ['presente_descricao', 'preco', 'loja', 'fonte', 'data']
    list_filter = ['fonte', 'data']
    search_fields = ['presente__descricao', 'loja']
    ordering = ['-data']
    date_hierarchy = 'data'
    readonly_fields = ['data']

    def presente_descricao(self, obj):
        return obj.presente.descricao[:40]
    presente_descricao.short_description = 'Presente'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('presente')


@admin.register(PesquisaPrecoLog)
class PesquisaPrecoLogAdmin(admin.ModelAdmin):
    """Admin das execuções da pesquisa semanal de preços"""
    list_display = ['origem', 'data_inicio', 'data_fim', 'total_presentes', 'sucessos', 'erros']
    list_filter = ['origem', 'data_inicio']
    ordering = ['-data_inicio']
    readonly_fields = ['data_inicio']


# Customizar o site admin
admin.site.site_header = '🎁 Lista de Presentes - Administração'
admin.site.site_title = 'Admin Lista de Presentes'
admin.site.index_title = 'Painel de Controle'


@admin.register(DespertarServidor)
class DespertarServidorAdmin(admin.ModelAdmin):
    list_display = ['iniciado_em', 'primeiro_acesso_em', 'origem', 'caminho']
    list_filter = ['origem']
    date_hierarchy = 'iniciado_em'


@admin.register(AcessoHora)
class AcessoHoraAdmin(admin.ModelAdmin):
    list_display = ['data', 'hora', 'acessos']
    date_hierarchy = 'data'
