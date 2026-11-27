from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager
from django.utils import timezone
import hashlib
import secrets



def versao_da_imagem(conteudo):
    """Identificador curto do conteudo da imagem (muda quando a imagem muda)."""
    if not conteudo:
        return ''
    return hashlib.sha1(conteudo.encode('ascii', 'ignore'), usedforsecurity=False).hexdigest()[:12]


class SemImagemManager(models.Manager):
    """
    Manager que não traz a coluna da imagem em base64.

    As imagens chegam a vários MB por linha e só as rotas de imagem precisam
    delas; sem isso, cada página trazia do banco a foto do usuário logado, a
    imagem do grupo ativo e as dos presentes. A coluna continua acessível: o
    Django busca sob demanda se alguém ler o atributo.
    """
    campos_pesados = ()

    def get_queryset(self):
        return super().get_queryset().defer(*self.campos_pesados)


class GrupoManager(SemImagemManager):
    campos_pesados = ('imagem_base64',)


class PresenteManager(SemImagemManager):
    campos_pesados = ('imagem_base64',)


class UsuarioManager(UserManager):
    """UserManager que também deixa a foto de fora (inclusive no request.user)."""

    def get_queryset(self):
        return super().get_queryset().defer('foto_base64')


class VersaoImagemMixin:
    """
    Mantem um campo curto de versao sincronizado com cada campo base64 e, com
    o Supabase Storage configurado, leva a imagem para o bucket ao salvar.

    Com a versao, as listagens sabem se existe imagem e montam a URL com
    ?v= (cache longo no navegador) sem carregar o base64 do banco. A versao
    e calculada do conteudo, entao continua a mesma quando a imagem muda de
    lugar (banco -> Storage) e os caches do navegador seguem validos.
    """
    # (campo_base64, campo_versao, campo_storage, campo_tipo)
    CAMPOS_VERSAO = ()

    def refresh_from_db(self, using=None, fields=None, from_queryset=None):
        # O manager base adia o base64; sem isto, refresh_from_db() deixaria
        # a imagem com o valor antigo em vez de recarregá-la.
        if from_queryset is None:
            from_queryset = models.QuerySet(model=type(self), using=using)
        return super().refresh_from_db(using=using, fields=fields, from_queryset=from_queryset)

    def _campos_da_imagem(self, campo_base64):
        return next(c for c in self.CAMPOS_VERSAO if c[0] == campo_base64)

    def limpar_imagem(self, campo_base64):
        """Remove a imagem (do banco e do Storage). Devolve os campos alterados."""
        _, campo_versao, campo_storage, campo_tipo = self._campos_da_imagem(campo_base64)
        antigo = getattr(self, campo_storage)
        if antigo:
            self.__dict__.setdefault('_storage_remover', []).append(antigo)
        setattr(self, campo_base64, None)
        setattr(self, campo_tipo, None)
        setattr(self, campo_storage, '')
        setattr(self, campo_versao, '')
        return [campo_base64, campo_tipo, campo_storage, campo_versao]

    def _sincronizar_versoes(self, kwargs):
        from . import storage
        adiados = self.get_deferred_fields()
        update_fields = kwargs.get('update_fields')
        extras = []
        for campo_base64, campo_versao, campo_storage, campo_tipo in self.CAMPOS_VERSAO:
            if campo_base64 in adiados:
                continue
            if update_fields is not None and campo_base64 not in update_fields:
                continue
            conteudo = getattr(self, campo_base64)
            if not conteudo:
                # Sem base64: ou nao ha imagem, ou ela ja esta no Storage
                if not getattr(self, campo_storage):
                    setattr(self, campo_versao, '')
                    extras.append(campo_versao)
                continue
            setattr(self, campo_versao, versao_da_imagem(conteudo))
            extras.append(campo_versao)
            if storage.configurado():
                extras += self._enviar_para_storage(campo_base64, campo_storage, campo_tipo, conteudo)
        if update_fields is not None and extras:
            kwargs['update_fields'] = set(update_fields) | set(extras)

    def _enviar_para_storage(self, campo_base64, campo_storage, campo_tipo, conteudo):
        """Sobe a imagem; se falhar, ela fica no banco como antes."""
        import base64
        import logging
        from . import storage
        from .rede import EXTENSOES
        tipo = (getattr(self, campo_tipo) or 'image/jpeg').lower()
        caminho = storage.novo_caminho(self._meta.model_name, EXTENSOES.get(tipo, 'bin'))
        try:
            storage.enviar(caminho, base64.b64decode(conteudo), tipo)
        except Exception as e:
            logging.getLogger(__name__).warning(f'Imagem mantida no banco (Storage falhou): {e}')
            return []
        antigo = getattr(self, campo_storage)
        if antigo:
            self.__dict__.setdefault('_storage_remover', []).append(antigo)
        setattr(self, campo_storage, caminho)
        setattr(self, campo_base64, None)
        return [campo_storage]

    def _depois_de_salvar(self):
        """Apaga do Storage as imagens substituidas, depois do commit."""
        from django.db import transaction
        from . import storage
        for caminho in self.__dict__.pop('_storage_remover', []):
            transaction.on_commit(lambda c=caminho: storage.remover(c))

    def _tem_conteudo(self, campo_base64, campo_versao):
        """True se ha imagem, sem buscar o base64 quando ele foi adiado."""
        campo_storage = self._campos_da_imagem(campo_base64)[2]
        if getattr(self, campo_storage, ''):
            return True
        if campo_base64 in self.get_deferred_fields():
            return bool(getattr(self, campo_versao))
        return bool(getattr(self, campo_base64))

    def _url_versionada(self, caminho, campo_versao):
        versao = '' if campo_versao in self.get_deferred_fields() else getattr(self, campo_versao)
        return f'{caminho}?v={versao}' if versao else caminho


class Grupo(VersaoImagemMixin, models.Model):
    """
    Modelo para representar grupos de usuarios.
    Cada grupo tem seus proprios presentes, compras e notificacoes.
    """
    nome = models.CharField(max_length=200)
    descricao = models.TextField(blank=True, null=True)
    codigo_convite = models.CharField(max_length=32, unique=True, editable=False)
    ativo = models.BooleanField(default=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    # Campos para imagem do grupo (mesmo padrao de Presente)
    imagem_base64 = models.TextField(blank=True, null=True, help_text='Imagem codificada em base64')
    imagem_nome = models.CharField(max_length=255, blank=True, null=True, help_text='Nome original do arquivo')
    imagem_tipo = models.CharField(max_length=50, blank=True, null=True, help_text='MIME type da imagem')
    imagem_versao = models.CharField(max_length=12, blank=True, default='', db_default='', editable=False,
                                     help_text='Muda quando a imagem muda (cache e URL)')
    imagem_storage = models.CharField(max_length=200, blank=True, default='', db_default='', editable=False,
                                      help_text='Caminho da imagem no Supabase Storage')

    CAMPOS_VERSAO = (('imagem_base64', 'imagem_versao', 'imagem_storage', 'imagem_tipo'),)

    objects = GrupoManager()

    class Meta:
        verbose_name = 'Grupo'
        verbose_name_plural = 'Grupos'
        # Também ao seguir chaves estrangeiras (ex.: request.user.grupo_ativo)
        base_manager_name = 'objects'
        ordering = ['-data_criacao']
        indexes = [
            models.Index(fields=['codigo_convite'], name='grupo_codigo_idx'),
            models.Index(fields=['ativo', '-data_criacao'], name='grupo_ativo_data_idx'),
        ]

    def __str__(self):
        return self.nome

    def save(self, *args, **kwargs):
        """Gera codigo de convite unico ao criar o grupo"""
        if not self.codigo_convite:
            self.codigo_convite = secrets.token_urlsafe(24)
        self._sincronizar_versoes(kwargs)
        super().save(*args, **kwargs)
        self._depois_de_salvar()

    def get_link_convite(self):
        """Retorna o link de convite completo"""
        from django.conf import settings
        base_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
        return f"{base_url}/grupos/convite/{self.codigo_convite}/"

    def tem_imagem(self):
        """Verifica se o grupo tem imagem"""
        return self._tem_conteudo('imagem_base64', 'imagem_versao')

    def get_imagem_url(self):
        """Retorna a URL da imagem do grupo"""
        if self.tem_imagem():
            return self._url_versionada(f'/grupo/{self.id}/imagem/', 'imagem_versao')
        return None


class Usuario(VersaoImagemMixin, AbstractUser):
    email = models.EmailField(unique=True)
    telefone = models.CharField(max_length=20, blank=True)
    ativo = models.BooleanField(default=True)
    data_cadastro = models.DateTimeField(auto_now_add=True)
    avatar = models.CharField(max_length=50, blank=True, default='avatar-1', help_text='ID do avatar pre-definido')
    foto_base64 = models.TextField(blank=True, null=True, help_text='Foto do usuario em base64')
    foto_tipo = models.CharField(max_length=50, blank=True, null=True, help_text='MIME type da foto')
    foto_versao = models.CharField(max_length=12, blank=True, default='', db_default='', editable=False,
                                   help_text='Muda quando a foto muda (cache e URL)')
    foto_storage = models.CharField(max_length=200, blank=True, default='', db_default='', editable=False,
                                    help_text='Caminho da foto no Supabase Storage')
    grupo_ativo = models.ForeignKey(
        Grupo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='usuarios_ativos',
        help_text='Grupo atualmente selecionado pelo usuario'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    objects = UsuarioManager()

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        base_manager_name = 'objects'

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    CAMPOS_VERSAO = (('foto_base64', 'foto_versao', 'foto_storage', 'foto_tipo'),)

    def save(self, *args, **kwargs):
        self._sincronizar_versoes(kwargs)
        super().save(*args, **kwargs)
        self._depois_de_salvar()

    def tem_foto(self):
        return self._tem_conteudo('foto_base64', 'foto_versao')

    def get_foto_url(self):
        if self.pk and self.tem_foto():
            return self._url_versionada(f'/usuario/{self.pk}/foto/', 'foto_versao')
        return None

    def get_grupos(self):
        """Retorna todos os grupos que o usuario pertence"""
        return Grupo.objects.filter(membros__usuario=self, ativo=True).distinct()

    def e_mantenedor_grupo_ativo(self):
        """Verifica se o usuario e mantenedor do grupo ativo"""
        if not self.grupo_ativo:
            return False
        return GrupoMembro.objects.filter(
            grupo=self.grupo_ativo,
            usuario=self,
            e_mantenedor=True
        ).exists()


class GrupoMembro(models.Model):
    """
    Modelo intermediario para relacionamento entre Grupo e Usuario.
    Controla permissoes e funcoes de cada membro.
    """
    grupo = models.ForeignKey(Grupo, on_delete=models.CASCADE, related_name='membros')
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='grupos_membro')
    e_mantenedor = models.BooleanField(
        default=False,
        help_text='Mantenedores podem gerenciar o grupo e seus membros'
    )
    data_entrada = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Membro do Grupo'
        verbose_name_plural = 'Membros dos Grupos'
        unique_together = [['grupo', 'usuario']]
        ordering = ['-e_mantenedor', '-data_entrada']
        indexes = [
            models.Index(fields=['grupo', 'usuario'], name='grupomembro_grupo_usuario_idx'),
            models.Index(fields=['usuario', '-data_entrada'], name='grupomembro_usuario_data_idx'),
            models.Index(fields=['grupo', 'e_mantenedor'], name='grupomembro_grupo_manten_idx'),
        ]

    def __str__(self):
        tipo = "Mantenedor" if self.e_mantenedor else "Membro"
        return f"{self.usuario} - {self.grupo} ({tipo})"


class Presente(VersaoImagemMixin, models.Model):
    STATUS_CHOICES = [
        ('ATIVO', 'Ativo'),
        ('COMPRADO', 'Comprado'),
    ]

    grupo = models.ForeignKey(
        Grupo,
        on_delete=models.CASCADE,
        related_name='presentes',
        null=True,
        blank=True,
        help_text='Grupo ao qual o presente pertence'
    )
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='presentes')
    descricao = models.TextField()
    url = models.URLField(max_length=1000, blank=True, null=True)
    preco = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ATIVO')
    data_cadastro = models.DateTimeField(auto_now_add=True)

    # Campo antigo (mantido para compatibilidade)
    imagem = models.ImageField(upload_to='presentes/', blank=True, null=True)

    # Campos novos para armazenar imagem no BD
    imagem_base64 = models.TextField(blank=True, null=True, help_text='Imagem codificada em base64')
    imagem_nome = models.CharField(max_length=255, blank=True, null=True, help_text='Nome original do arquivo')
    imagem_tipo = models.CharField(max_length=50, blank=True, null=True, help_text='MIME type da imagem')
    imagem_versao = models.CharField(max_length=12, blank=True, default='', db_default='', editable=False,
                                     help_text='Muda quando a imagem muda (cache e URL)')
    imagem_storage = models.CharField(max_length=200, blank=True, default='', db_default='', editable=False,
                                      help_text='Caminho da imagem no Supabase Storage')

    CAMPOS_VERSAO = (('imagem_base64', 'imagem_versao', 'imagem_storage', 'imagem_tipo'),)

    # Resultado da ultima busca de imagem no site (link original)
    busca_imagem_em = models.DateTimeField(null=True, blank=True)
    busca_imagem_resultado = models.CharField(max_length=300, blank=True, default='')

    objects = PresenteManager()

    class Meta:
        base_manager_name = 'objects'
        verbose_name = 'Presente'
        verbose_name_plural = 'Presentes'
        ordering = ['-data_cadastro']
        indexes = [
            models.Index(fields=['grupo', 'usuario', 'status'], name='presente_grp_user_status_idx'),
            models.Index(fields=['grupo', 'status', '-data_cadastro'], name='presente_grupo_status_data_idx'),
            models.Index(fields=['grupo', '-data_cadastro'], name='presente_grupo_data_idx'),
            models.Index(fields=['usuario', 'status'], name='presente_usuario_status_idx'),
            models.Index(fields=['status', '-data_cadastro'], name='presente_status_data_idx'),
            models.Index(fields=['-data_cadastro'], name='presente_data_idx'),
        ]

    def __str__(self):
        return f"{self.descricao[:50]} - {self.usuario}"

    def save(self, *args, **kwargs):
        self._sincronizar_versoes(kwargs)
        super().save(*args, **kwargs)
        self._depois_de_salvar()

    def tem_imagem(self):
        """Verifica se o presente tem imagem (novo formato ou antigo)"""
        return self._tem_conteudo('imagem_base64', 'imagem_versao') or bool(self.imagem)

    def get_imagem_url(self):
        """Retorna a URL da imagem (novo formato tem prioridade)"""
        if self._tem_conteudo('imagem_base64', 'imagem_versao'):
            return self._url_versionada(f'/presente/{self.id}/imagem/', 'imagem_versao')
        elif self.imagem:
            return self.imagem.url
        return None

    def registrar_preco(self, preco, loja='', fonte='sistema'):
        """Registra um ponto no histórico de preços (sem duplicar o último valor)."""
        if preco is None:
            return None
        ultimo = self.historico_precos.order_by('-data').first()
        if ultimo and ultimo.preco == preco:
            return None
        return PrecoHistorico.objects.create(
            presente=self,
            preco=preco,
            loja=(loja or '')[:200],
            fonte=fonte
        )

    def temperatura(self):
        """
        Temperatura do preço: compara o preço mais recente com a média do histórico.
        Quente (caiu >= 5%) = bom momento de compra; Frio (subiu >= 5%) = aguardar.
        Usa o cache do prefetch_related('historico_precos') quando disponível.
        """
        pontos = sorted(self.historico_precos.all(), key=lambda p: p.data)
        precos = [float(p.preco) for p in pontos if p.preco]
        if len(precos) < 2:
            return {
                'codigo': 'sem_dados', 'icone': 'bi-thermometer-half',
                'label': 'Sem histórico', 'css': 'bg-base-200 text-base-content/70',
                'variacao': None,
            }
        atual = precos[-1]
        media = sum(precos[:-1]) / len(precos[:-1])
        variacao = ((atual - media) / media * 100) if media else 0
        if variacao <= -5:
            return {
                'codigo': 'quente', 'icone': 'bi-fire',
                'label': f'Preço baixo ({variacao:.0f}%)', 'css': 'bg-error/10 text-error',
                'variacao': variacao,
            }
        if variacao >= 5:
            return {
                'codigo': 'frio', 'icone': 'bi-snow',
                'label': f'Preço alto (+{variacao:.0f}%)', 'css': 'bg-info/10 text-info',
                'variacao': variacao,
            }
        return {
            'codigo': 'estavel', 'icone': 'bi-dash-lg',
            'label': 'Preço estável', 'css': 'bg-base-200 text-base-content/70',
            'variacao': variacao,
        }


class PrecoHistorico(models.Model):
    """
    Ponto do histórico de preços de um presente (estilo priceHistory do LPII).
    Alimentado no cadastro, nas buscas de sugestões e na pesquisa semanal.
    """
    presente = models.ForeignKey(
        Presente,
        on_delete=models.CASCADE,
        related_name='historico_precos'
    )
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    loja = models.CharField(max_length=200, blank=True, default='')
    fonte = models.CharField(
        max_length=30,
        default='sistema',
        help_text='Origem do registro: cadastro, sugestao, aplicado, pesquisa_semanal'
    )
    data = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Histórico de Preço'
        verbose_name_plural = 'Histórico de Preços'
        ordering = ['data']
        indexes = [
            models.Index(fields=['presente', 'data'], name='precohist_presente_data_idx'),
        ]

    def __str__(self):
        return f"{self.presente_id} - R$ {self.preco} ({self.data:%d/%m/%Y})"


class PesquisaPrecoLog(models.Model):
    """Registro de execuções da pesquisa de preços (semanal automática ou manual)."""
    ORIGEM_CHOICES = [
        ('automatica', 'Automática (semanal)'),
        ('manual', 'Manual (admin)'),
        ('comando', 'Comando (cron)'),
    ]
    origem = models.CharField(max_length=20, choices=ORIGEM_CHOICES, default='automatica')
    data_inicio = models.DateTimeField(auto_now_add=True)
    data_fim = models.DateTimeField(null=True, blank=True)
    total_presentes = models.IntegerField(default=0)
    sucessos = models.IntegerField(default=0)
    erros = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'Pesquisa de Preços'
        verbose_name_plural = 'Pesquisas de Preços'
        ordering = ['-data_inicio']

    def __str__(self):
        return f"Pesquisa {self.get_origem_display()} em {self.data_inicio:%d/%m/%Y %H:%M}"


class Compra(models.Model):
    grupo = models.ForeignKey(
        Grupo,
        on_delete=models.CASCADE,
        related_name='compras',
        null=True,
        blank=True,
        help_text='Grupo ao qual a compra pertence'
    )
    presente = models.OneToOneField(Presente, on_delete=models.CASCADE, related_name='compra')
    comprador = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='compras_realizadas')
    data_compra = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Compra'
        verbose_name_plural = 'Compras'
        indexes = [
            models.Index(fields=['grupo', 'comprador', '-data_compra'], name='compra_grp_comprador_data_idx'),
            models.Index(fields=['grupo', '-data_compra'], name='compra_grupo_data_idx'),
            models.Index(fields=['comprador', '-data_compra'], name='compra_comprador_data_idx'),
            models.Index(fields=['-data_compra'], name='compra_data_idx'),
        ]
    
    def __str__(self):
        return f"Compra de {self.presente.descricao[:30]} por {self.comprador}"


class SugestaoCompra(models.Model):
    grupo = models.ForeignKey(
        Grupo,
        on_delete=models.CASCADE,
        related_name='sugestoes',
        null=True,
        blank=True,
        help_text='Grupo ao qual a sugestao pertence'
    )
    presente = models.ForeignKey(Presente, on_delete=models.CASCADE, related_name='sugestoes')
    local_compra = models.CharField(max_length=200)
    titulo_produto = models.CharField(
        max_length=300,
        blank=True,
        default='',
        help_text='Titulo do produto no resultado da busca, para conferir se e o mesmo item'
    )
    url_compra = models.URLField(max_length=1000)
    preco_sugerido = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    data_busca = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Sugestão de Compra'
        verbose_name_plural = 'Sugestões de Compra'
        ordering = ['preco_sugerido']
        indexes = [
            models.Index(fields=['grupo', 'presente', 'preco_sugerido'], name='sugestao_grp_pres_preco_idx'),
            models.Index(fields=['grupo', '-data_busca'], name='sugestao_grupo_data_idx'),
            models.Index(fields=['presente', 'preco_sugerido'], name='sugestao_presente_preco_idx'),
            models.Index(fields=['-data_busca'], name='sugestao_data_idx'),
        ]
    
    def __str__(self):
        return f"{self.local_compra} - R$ {self.preco_sugerido}"


class Notificacao(models.Model):
    grupo = models.ForeignKey(
        Grupo,
        on_delete=models.CASCADE,
        related_name='notificacoes',
        null=True,
        blank=True,
        help_text='Grupo ao qual a notificacao pertence'
    )
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='notificacoes')
    mensagem = models.TextField()
    lida = models.BooleanField(default=False)
    data_notificacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Notificação'
        verbose_name_plural = 'Notificações'
        ordering = ['-data_notificacao']
        indexes = [
            models.Index(fields=['grupo', 'usuario', 'lida', '-data_notificacao'], name='notif_grp_user_lida_data_idx'),
            models.Index(fields=['grupo', 'lida', '-data_notificacao'], name='notif_grupo_lida_data_idx'),
            models.Index(fields=['usuario', 'lida', '-data_notificacao'], name='notif_usuario_lida_data_idx'),
            models.Index(fields=['lida', '-data_notificacao'], name='notif_lida_data_idx'),
        ]

    def __str__(self):
        return f"Notificação para {self.usuario} - {self.mensagem[:30]}"


class PushSubscription(models.Model):
    """Assinatura de push notification (Web Push) de um usuário/dispositivo."""
    endpoint = models.URLField(max_length=500, unique=True)
    p256dh = models.CharField(max_length=200)
    auth = models.CharField(max_length=100)
    criado_em = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='push_subscriptions'
    )

    class Meta:
        verbose_name = 'Push Subscription'
        verbose_name_plural = 'Push Subscriptions'

    def __str__(self):
        return f"Push de {self.usuario} ({self.endpoint[:40]}...)"


class MercadoLivreToken(models.Model):
    """Token OAuth da API do Mercado Livre (registro unico).

    O refresh token do Mercado Livre e de uso unico: cada renovacao devolve
    um novo, por isso ele fica no banco e nao em variavel de ambiente.
    """
    access_token = models.CharField(max_length=500)
    refresh_token = models.CharField(max_length=500)
    expira_em = models.DateTimeField()
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Token do Mercado Livre'
        verbose_name_plural = 'Token do Mercado Livre'

    def __str__(self):
        return f"Token Mercado Livre (expira em {self.expira_em:%d/%m/%Y %H:%M})"


class DespertarServidor(models.Model):
    """Cada vez que o servidor sobe (no Render Free, ao acordar depois de dormir)."""
    ORIGEM_CHOICES = [
        ('USUARIO', 'Usuário'),
        ('MONITOR', 'Ping de monitoramento'),
    ]
    iniciado_em = models.DateTimeField(unique=True, help_text='Quando o processo do servidor subiu')
    primeiro_acesso_em = models.DateTimeField(help_text='Primeira requisição depois de subir')
    caminho = models.CharField(max_length=300)
    origem = models.CharField(max_length=10, choices=ORIGEM_CHOICES)
    user_agent = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = 'Despertar do servidor'
        verbose_name_plural = 'Despertares do servidor'
        ordering = ['-iniciado_em']

    def __str__(self):
        return f"Despertar em {self.iniciado_em:%d/%m/%Y %H:%M} ({self.get_origem_display()})"


class AcessoHora(models.Model):
    """Quantidade de acessos de usuários por dia e hora (horário local)."""
    data = models.DateField()
    hora = models.PositiveSmallIntegerField()
    acessos = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Acessos por hora'
        verbose_name_plural = 'Acessos por hora'
        ordering = ['-data', '-hora']
        constraints = [
            models.UniqueConstraint(fields=['data', 'hora'], name='acesso_hora_unico'),
        ]

    def __str__(self):
        return f"{self.data:%d/%m/%Y} {self.hora:02d}h: {self.acessos} acesso(s)"


def _apagar_do_storage(sender, instance, **kwargs):
    """Ao excluir presente, grupo ou usuario, apaga a imagem do Storage."""
    from django.db import transaction
    from . import storage
    for _, _, campo_storage, _ in getattr(instance, 'CAMPOS_VERSAO', ()):
        caminho = getattr(instance, campo_storage, '')
        if caminho:
            transaction.on_commit(lambda c=caminho: storage.remover(c))


for _modelo in (Grupo, Usuario, Presente):
    models.signals.post_delete.connect(_apagar_do_storage, sender=_modelo,
                                       dispatch_uid=f'apagar-storage-{_modelo.__name__}')
