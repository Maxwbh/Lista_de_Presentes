"""
Links de redefinicao de senha.

Usa o gerador de tokens do Django: o token nao fica guardado em lugar
nenhum (vale depois de o servidor dormir/reiniciar) e deixa de valer assim
que a senha muda ou depois de PASSWORD_RESET_TIMEOUT.
"""
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode


def token_redefinicao(usuario):
    """Token no formato '<uid>.<token>' usado na URL /redefinir-senha/<token>/"""
    uid = urlsafe_base64_encode(force_bytes(usuario.pk))
    return f"{uid}.{default_token_generator.make_token(usuario)}"


def link_redefinicao(usuario, base_url=None):
    caminho = reverse('redefinir_senha', args=[token_redefinicao(usuario)])
    return f"{(base_url or settings.SITE_URL).rstrip('/')}{caminho}"


def usuario_do_token(token):
    """Usuario dono do token, ou None se o token for invalido ou tiver expirado"""
    from .models import Usuario

    uid, _, token_usuario = token.partition('.')
    try:
        usuario = Usuario.objects.get(pk=urlsafe_base64_decode(uid).decode())
    except (ValueError, TypeError, OverflowError, Usuario.DoesNotExist):
        return None
    if not default_token_generator.check_token(usuario, token_usuario):
        return None
    return usuario


def email_configurado():
    """Se ha um meio real de enviar e-mail (sem configuracao, os e-mails so vao para o log)"""
    return not settings.EMAIL_BACKEND.endswith('console.EmailBackend')
