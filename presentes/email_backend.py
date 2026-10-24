"""
Backend de e-mail pela API HTTPS da Brevo.

O Render Free bloqueia as portas SMTP (25, 465 e 587) desde setembro de
2025, entao o envio precisa ser por HTTPS. A Brevo tem plano gratuito
(300 e-mails/dia) e aceita como remetente um e-mail verificado (ex.: Gmail).
"""
import logging

import requests
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend
from email.utils import parseaddr

logger = logging.getLogger(__name__)

BREVO_URL = 'https://api.brevo.com/v3/smtp/email'


class BrevoEmailBackend(BaseEmailBackend):

    def send_messages(self, email_messages):
        enviados = 0
        for mensagem in email_messages:
            nome, email = parseaddr(mensagem.from_email or settings.DEFAULT_FROM_EMAIL)
            payload = {
                'sender': {'email': email, 'name': nome or 'Lista de Presentes'},
                'to': [{'email': destino} for destino in mensagem.to],
                'subject': mensagem.subject,
                'textContent': mensagem.body,
            }
            for conteudo, tipo in getattr(mensagem, 'alternatives', []):
                if tipo == 'text/html':
                    payload['htmlContent'] = conteudo
            try:
                response = requests.post(
                    BREVO_URL, json=payload, timeout=15,
                    headers={'api-key': settings.BREVO_API_KEY, 'Accept': 'application/json'},
                )
            except requests.exceptions.RequestException as e:
                logger.error(f"Erro de rede ao enviar e-mail pela Brevo: {e}")
                if not self.fail_silently:
                    raise
                continue
            if response.status_code in (200, 201, 202):
                enviados += 1
            else:
                logger.error(f"Brevo recusou o e-mail (HTTP {response.status_code}): {response.text[:300]}")
                if not self.fail_silently:
                    raise RuntimeError(f"Falha ao enviar e-mail (HTTP {response.status_code})")
        return enviados
