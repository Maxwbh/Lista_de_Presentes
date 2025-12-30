from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import secrets


class Grupo(models.Model):
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

    class Meta:
        verbose_name = 'Grupo'
        verbose_name_plural = 'Grupos'
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
        super().save(*args, **kwargs)

    def get_link_convite(self):
        """Retorna o link de convite completo"""
        from django.conf import settings
        base_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
        return f"{base_url}/grupos/convite/{self.codigo_convite}/"

    def tem_imagem(self):
        """Verifica se o grupo tem imagem"""
        return bool(self.imagem_base64)

    def get_imagem_url(self):
        """Retorna a URL da imagem do grupo"""
        if self.imagem_base64:
            return f'/grupo/{self.id}/imagem/'
        return None


class Usuario(AbstractUser):
    email = models.EmailField(unique=True)
    telefone = models.CharField(max_length=20, blank=True)
    ativo = models.BooleanField(default=True)
    data_cadastro = models.DateTimeField(auto_now_add=True)
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

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

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


class Presente(models.Model):
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

    class Meta:
        verbose_name = 'Presente'
        verbose_name_plural = 'Presentes'
        ordering = ['-data_cadastro']
        indexes = [
            models.Index(fields=['grupo', 'usuario', 'status'], name='presente_grupo_usuario_status_idx'),
            models.Index(fields=['grupo', 'status', '-data_cadastro'], name='presente_grupo_status_data_idx'),
            models.Index(fields=['grupo', '-data_cadastro'], name='presente_grupo_data_idx'),
            models.Index(fields=['usuario', 'status'], name='presente_usuario_status_idx'),
            models.Index(fields=['status', '-data_cadastro'], name='presente_status_data_idx'),
            models.Index(fields=['-data_cadastro'], name='presente_data_idx'),
        ]

    def __str__(self):
        return f"{self.descricao[:50]} - {self.usuario}"

    def tem_imagem(self):
        """Verifica se o presente tem imagem (novo formato ou antigo)"""
        return bool(self.imagem_base64 or self.imagem)

    def get_imagem_url(self):
        """Retorna a URL da imagem (novo formato tem prioridade)"""
        if self.imagem_base64:
            return f'/presente/{self.id}/imagem/'
        elif self.imagem:
            return self.imagem.url
        return None


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
            models.Index(fields=['grupo', 'comprador', '-data_compra'], name='compra_grupo_comprador_data_idx'),
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
    url_compra = models.URLField(max_length=1000)
    preco_sugerido = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    data_busca = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Sugestão de Compra'
        verbose_name_plural = 'Sugestões de Compra'
        ordering = ['preco_sugerido']
        indexes = [
            models.Index(fields=['grupo', 'presente', 'preco_sugerido'], name='sugestao_grupo_presente_preco_idx'),
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
            models.Index(fields=['grupo', 'usuario', 'lida', '-data_notificacao'], name='notif_grupo_usuario_lida_data_idx'),
            models.Index(fields=['grupo', 'lida', '-data_notificacao'], name='notif_grupo_lida_data_idx'),
            models.Index(fields=['usuario', 'lida', '-data_notificacao'], name='notif_usuario_lida_data_idx'),
            models.Index(fields=['lida', '-data_notificacao'], name='notif_lida_data_idx'),
        ]
    
    def __str__(self):
        return f"Notificação para {self.usuario} - {self.mensagem[:30]}"
