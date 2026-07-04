"""
Validação das credenciais de login social (Google, Facebook, LinkedIn, Apple).

Duas camadas:
- validar_formato: checagens instantâneas de formato (sem rede). Usada para
  decidir se o botão do provedor aparece na tela de login — esconde valores
  vazios, placeholders ou com formato claramente errado.
- validar_online: confirma as credenciais contra a API do provedor (com rede).
  Usada pelo comando `python manage.py validar_social`.
"""
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

TIMEOUT = 8


def _apps():
    providers = getattr(settings, 'SOCIALACCOUNT_PROVIDERS', {})
    return {nome: cfg.get('APP', {}) for nome, cfg in providers.items()}


def validar_formato(provider, app=None):
    """Valida o formato das credenciais sem acessar a rede. Retorna (ok, msg)."""
    if app is None:
        app = _apps().get(provider, {})

    client_id = (app.get('client_id') or '').strip()
    secret = (app.get('secret') or '').strip()

    if not client_id:
        return False, 'client_id não configurado'
    if client_id.startswith('sua-') or 'example' in client_id.lower():
        return False, 'client_id é um placeholder'

    if provider == 'google':
        if not client_id.endswith('.apps.googleusercontent.com'):
            return False, 'client_id Google deve terminar com .apps.googleusercontent.com'
        if not secret:
            return False, 'GOOGLE_CLIENT_SECRET não configurado'
    elif provider == 'facebook':
        if not client_id.isdigit():
            return False, 'FACEBOOK_APP_ID deve ser numérico'
        if not secret:
            return False, 'FACEBOOK_APP_SECRET não configurado'
    elif provider == 'linkedin_oauth2':
        if not secret:
            return False, 'LINKEDIN_CLIENT_SECRET não configurado'
    elif provider == 'apple':
        key = (app.get('key') or '').strip()
        cert = (app.get('certificate_key') or '').strip()
        if not key:
            return False, 'APPLE_KEY_ID não configurado'
        if 'PRIVATE KEY' not in cert:
            return False, 'APPLE_PRIVATE_KEY deve conter a chave PEM (BEGIN PRIVATE KEY)'

    return True, 'formato OK'


def validar_online(provider, app=None):
    """Confirma as credenciais contra a API do provedor. Retorna (ok, msg)."""
    if app is None:
        app = _apps().get(provider, {})

    ok, msg = validar_formato(provider, app)
    if not ok:
        return False, msg

    client_id = app.get('client_id', '').strip()
    secret = app.get('secret', '').strip()

    try:
        if provider == 'google':
            # Truque: troca de token com code inválido. Se as credenciais forem
            # ruins o Google responde 'invalid_client'; caso contrário responde
            # erro de grant — o que confirma que client_id/secret são aceitos.
            resp = requests.post(
                'https://oauth2.googleapis.com/token',
                data={
                    'client_id': client_id, 'client_secret': secret,
                    'code': 'codigo-de-validacao-invalido',
                    'grant_type': 'authorization_code',
                    'redirect_uri': 'https://localhost/validacao',
                },
                timeout=TIMEOUT,
            )
            erro = resp.json().get('error', '')
            if erro == 'invalid_client':
                return False, 'Google rejeitou client_id/secret (invalid_client)'
            return True, 'credenciais aceitas pelo Google'

        if provider == 'facebook':
            # client_credentials emite um app token se id/secret forem válidos
            resp = requests.get(
                'https://graph.facebook.com/oauth/access_token',
                params={
                    'client_id': client_id, 'client_secret': secret,
                    'grant_type': 'client_credentials',
                },
                timeout=TIMEOUT,
            )
            dados = resp.json()
            if 'access_token' in dados:
                return True, 'credenciais válidas (app token emitido)'
            return False, f"Facebook rejeitou: {dados.get('error', {}).get('message', resp.text[:120])}"

        if provider == 'linkedin_oauth2':
            resp = requests.post(
                'https://www.linkedin.com/oauth/v2/accessToken',
                data={
                    'grant_type': 'client_credentials',
                    'client_id': client_id, 'client_secret': secret,
                },
                timeout=TIMEOUT,
            )
            dados = resp.json()
            if 'access_token' in dados:
                return True, 'credenciais válidas'
            erro = dados.get('error', '')
            if erro == 'invalid_client':
                return False, 'LinkedIn rejeitou client_id/secret (invalid_client)'
            # unauthorized_client/access_denied: o app existe mas não permite
            # este grant — as credenciais em si estão corretas
            return True, f'credenciais aceitas pelo LinkedIn ({erro or "grant não habilitado"})'

        if provider == 'apple':
            return True, 'formato OK (Apple não tem validação online simples — teste com login real)'

    except requests.exceptions.RequestException as e:
        return False, f'erro de rede ao validar: {e}'
    except ValueError:
        return False, 'resposta inesperada do provedor'

    return False, 'provedor desconhecido'


def validar_todos(online=False):
    """Valida todos os provedores. Retorna {provedor: (configurado, ok, msg)}."""
    resultado = {}
    for provider, app in _apps().items():
        configurado = bool((app.get('client_id') or '').strip())
        if not configurado:
            resultado[provider] = (False, False, 'não configurado')
            continue
        if online:
            ok, msg = validar_online(provider, app)
        else:
            ok, msg = validar_formato(provider, app)
        resultado[provider] = (True, ok, msg)
    return resultado
