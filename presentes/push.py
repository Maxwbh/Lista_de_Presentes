"""
Envio de notificacoes Web Push (VAPID).

Toda Notificacao criada e enviada tambem por push para os navegadores em que
o usuario aceitou receber notificacoes (PushSubscription). Sem as chaves
VAPID configuradas o envio fica desligado.
"""
import base64
import json
import logging
import threading

from django.conf import settings
from django.db import connection, transaction

logger = logging.getLogger(__name__)

# Respostas do servico de push que indicam assinatura expirada/cancelada
STATUS_ASSINATURA_INVALIDA = (404, 410)


def push_configurado():
    return bool(settings.VAPID_PUBLIC_KEY and settings.VAPID_PRIVATE_KEY and settings.VAPID_ADMIN_EMAIL)


def gerar_chaves_vapid():
    """Gera um par de chaves VAPID: (publica, privada), ambas em base64url"""
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ec

    def b64url(dados):
        return base64.urlsafe_b64encode(dados).rstrip(b'=').decode()

    chave_privada = ec.generate_private_key(ec.SECP256R1())
    publica = chave_privada.public_key().public_bytes(
        serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint
    )
    privada = chave_privada.private_numbers().private_value.to_bytes(32, 'big')
    return b64url(publica), b64url(privada)


def enviar_push(usuario, mensagem, url='/notificacoes/', titulo='Lista de Presentes'):
    """Envia a mensagem para todas as assinaturas do usuario. Retorna quantas foram entregues."""
    from pywebpush import webpush, WebPushException
    from .models import PushSubscription

    if not push_configurado():
        return 0

    payload = json.dumps({'title': titulo, 'body': mensagem, 'url': url})
    email = settings.VAPID_ADMIN_EMAIL
    claims = {'sub': email if email.startswith('mailto:') else f'mailto:{email}'}

    entregues = 0
    for assinatura in PushSubscription.objects.filter(usuario=usuario):
        try:
            webpush(
                subscription_info={
                    'endpoint': assinatura.endpoint,
                    'keys': {'p256dh': assinatura.p256dh, 'auth': assinatura.auth},
                },
                data=payload,
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_claims=dict(claims),
                timeout=10,
            )
            entregues += 1
        except WebPushException as e:
            status = getattr(e.response, 'status_code', None)
            if status in STATUS_ASSINATURA_INVALIDA:
                logger.info(f"Removendo assinatura push expirada de {usuario}: {assinatura.endpoint[:60]}")
                assinatura.delete()
            else:
                logger.warning(f"Falha ao enviar push para {usuario}: {e}")
        except Exception as e:
            logger.error(f"Erro inesperado ao enviar push para {usuario}: {e}")
    return entregues


def _enviar_push_notificacao(notificacao_id):
    from .models import Notificacao

    try:
        notificacao = Notificacao.objects.select_related('usuario').get(pk=notificacao_id)
        enviar_push(notificacao.usuario, notificacao.mensagem)
    except Notificacao.DoesNotExist:
        pass
    finally:
        # A thread abre a propria conexao com o banco; fecha ao terminar
        connection.close()


def notificacao_criada(sender, instance, created, **kwargs):
    """post_save de Notificacao: envia o push depois do commit, em background"""
    if not created or not push_configurado():
        return
    transaction.on_commit(
        lambda: threading.Thread(target=_enviar_push_notificacao, args=(instance.pk,), daemon=True).start()
    )
