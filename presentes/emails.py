"""
E-mails enviados pelo sistema: redefinicao de senha, boas-vindas e presente comprado.

Cada e-mail tem versao em texto (templates/emails/<nome>.txt) e em HTML
(templates/emails/<nome>.html). Sem e-mail configurado (BREVO_API_KEY ou
EMAIL_HOST) nada e enviado.
"""
import logging
import threading

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db import connection, transaction
from django.template.loader import render_to_string
from django.urls import reverse

from .senha import email_configurado

logger = logging.getLogger(__name__)


def _link(nome_url, *args, base_url=None):
    return f"{(base_url or settings.SITE_URL).rstrip('/')}{reverse(nome_url, args=args)}"


def _enviar(nome, assunto, destinatario, contexto):
    """Envia o e-mail <nome>. Retorna True se foi entregue ao provedor."""
    if not email_configurado() or not destinatario:
        return False
    contexto = {'site_url': settings.SITE_URL.rstrip('/'), **contexto}
    mensagem = EmailMultiAlternatives(
        subject=assunto,
        body=render_to_string(f'emails/{nome}.txt', contexto),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[destinatario],
    )
    mensagem.attach_alternative(render_to_string(f'emails/{nome}.html', contexto), 'text/html')
    try:
        mensagem.send(fail_silently=False)
    except Exception as e:
        logger.warning(f"Nao foi possivel enviar o e-mail '{nome}' para {destinatario}: {e}")
        return False
    logger.info(f"E-mail '{nome}' enviado para {destinatario}")
    return True


def _depois_do_commit(funcao, *args):
    """Envia em segundo plano depois do commit, para nao atrasar a pagina"""
    if not email_configurado():
        return

    def executar():
        try:
            funcao(*args)
        finally:
            # A thread abre a propria conexao com o banco; fecha ao terminar
            connection.close()

    transaction.on_commit(lambda: threading.Thread(target=executar, daemon=True).start())


def email_redefinicao_senha(usuario, link):
    return _enviar('redefinicao_senha', 'Redefinição de senha - Lista de Presentes', usuario.email, {
        'usuario': usuario,
        'link': link,
    })


def email_boas_vindas(usuario_id):
    from .models import Usuario

    usuario = Usuario.objects.filter(pk=usuario_id).first()
    if not usuario:
        return False
    return _enviar('boas_vindas', 'Bem-vindo(a) à Lista de Presentes!', usuario.email, {
        'usuario': usuario,
        'link_lista': _link('meus_presentes'),
        'link_adicionar': _link('adicionar_presente'),
    })


def email_presente_comprado(presente_id):
    """Avisa o dono da lista. Nao diz quem comprou, para manter a surpresa."""
    from .models import Presente

    presente = Presente.objects.select_related('usuario').filter(pk=presente_id).first()
    if not presente:
        return False
    return _enviar('presente_comprado', '🎁 Um presente da sua lista foi comprado!', presente.usuario.email, {
        'usuario': presente.usuario,
        'presente': presente,
        'link_lista': _link('meus_presentes'),
    })


def agendar_boas_vindas(usuario):
    _depois_do_commit(email_boas_vindas, usuario.pk)


def agendar_presente_comprado(presente):
    _depois_do_commit(email_presente_comprado, presente.pk)
