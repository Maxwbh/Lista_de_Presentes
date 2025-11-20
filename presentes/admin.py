from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Presente, Compra, SugestaoCompra, Notificacao


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    """Admin customizado para o modelo Usuario"""
    list_display = ['email', 'username', 'first_name', 'last_name', 'ativo', 'data_cadastro']
    list_filter = ['ativo', 'is_staff', 'is_superuser', 'data_cadastro']
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering = ['-data_cadastro']

    fieldsets = UserAdmin.fieldsets + (
        ('Informações Adicionais', {
            'fields': ('telefone', 'ativo', 'data_cadastro')
        }),
    )

    readonly_fields = ['data_cadastro', 'last_login', 'date_joined']

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        # Otimizar query
        return queryset.prefetch_related('presentes', 'compras_realizadas', 'notificacoes')


@admin.register(Presente)
class PresenteAdmin(admin.ModelAdmin):
    """Admin para gerenciar Presentes"""
    list_display = ['descricao_curta', 'usuario', 'preco', 'status', 'tem_sugestoes', 'data_cadastro']
    list_filter = ['status', 'data_cadastro']
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


# Customizar o site admin
admin.site.site_header = '🎁 Lista de Presentes - Administração'
admin.site.site_title = 'Admin Lista de Presentes'
admin.site.index_title = 'Painel de Controle'
