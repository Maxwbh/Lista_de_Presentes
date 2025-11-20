from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class Usuario(AbstractUser):
    email = models.EmailField(unique=True)
    telefone = models.CharField(max_length=20, blank=True)
    ativo = models.BooleanField(default=True)
    data_cadastro = models.DateTimeField(auto_now_add=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Presente(models.Model):
    STATUS_CHOICES = [
        ('ATIVO', 'Ativo'),
        ('COMPRADO', 'Comprado'),
    ]
    
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='presentes')
    descricao = models.TextField()
    url = models.URLField(max_length=1000, blank=True, null=True)
    preco = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ATIVO')
    data_cadastro = models.DateTimeField(auto_now_add=True)
    imagem = models.ImageField(upload_to='presentes/', blank=True, null=True)
    
    class Meta:
        verbose_name = 'Presente'
        verbose_name_plural = 'Presentes'
        ordering = ['-data_cadastro']
    
    def __str__(self):
        return f"{self.descricao[:50]} - {self.usuario}"


class Compra(models.Model):
    presente = models.OneToOneField(Presente, on_delete=models.CASCADE, related_name='compra')
    comprador = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='compras_realizadas')
    data_compra = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Compra'
        verbose_name_plural = 'Compras'
    
    def __str__(self):
        return f"Compra de {self.presente.descricao[:30]} por {self.comprador}"


class SugestaoCompra(models.Model):
    presente = models.ForeignKey(Presente, on_delete=models.CASCADE, related_name='sugestoes')
    local_compra = models.CharField(max_length=200)
    url_compra = models.URLField(max_length=1000)
    preco_sugerido = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    data_busca = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Sugestão de Compra'
        verbose_name_plural = 'Sugestões de Compra'
        ordering = ['preco_sugerido']
    
    def __str__(self):
        return f"{self.local_compra} - R$ {self.preco_sugerido}"


class Notificacao(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='notificacoes')
    mensagem = models.TextField()
    lida = models.BooleanField(default=False)
    data_notificacao = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Notificação'
        verbose_name_plural = 'Notificações'
        ordering = ['-data_notificacao']
    
    def __str__(self):
        return f"Notificação para {self.usuario} - {self.mensagem[:30]}"
