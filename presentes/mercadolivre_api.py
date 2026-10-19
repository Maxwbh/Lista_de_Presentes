"""
Cliente da API oficial do Mercado Livre.

O site do Mercado Livre bloqueia consultas automaticas (redireciona para
/gz/account-verification) e a API publica passou a exigir token OAuth.
Este modulo cuida do fluxo OAuth (authorization_code + refresh_token) e
da consulta de anuncios (/items) e produtos de catalogo (/products).
"""
import logging
import re
from datetime import timedelta
from urllib.parse import urlencode, urlparse, parse_qs, unquote

import requests
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

API_BASE_URL = 'https://api.mercadolibre.com'
AUTH_URL = 'https://auth.mercadolivre.com.br/authorization'

# Renova o token um pouco antes de expirar para nao usar um token vencido
MARGEM_RENOVACAO = timedelta(minutes=5)

# Ex.: MLB2070594105, MLB-7136159042
ID_RE = re.compile(r'\b(ML[A-Z])-?(\d{6,})\b', re.IGNORECASE)


class MercadoLivreAPIError(Exception):
    """Falha ao consultar a API do Mercado Livre"""
    pass


def credenciais_configuradas():
    return bool(settings.MERCADOLIVRE_CLIENT_ID and settings.MERCADOLIVRE_CLIENT_SECRET)


def url_autorizacao(redirect_uri, state):
    """URL para o administrador autorizar o app no Mercado Livre"""
    params = {
        'response_type': 'code',
        'client_id': settings.MERCADOLIVRE_CLIENT_ID,
        'redirect_uri': redirect_uri,
        'state': state,
    }
    return f"{AUTH_URL}?{urlencode(params)}"


def _salvar_token(dados):
    from .models import MercadoLivreToken

    token = MercadoLivreToken.objects.first() or MercadoLivreToken()
    token.access_token = dados['access_token']
    # Se a resposta nao trouxer refresh token novo, mantem o anterior
    token.refresh_token = dados.get('refresh_token') or token.refresh_token
    token.expira_em = timezone.now() + timedelta(seconds=int(dados.get('expires_in', 21600)))
    token.save()
    return token


def _pedir_token(payload):
    payload = {
        'client_id': settings.MERCADOLIVRE_CLIENT_ID,
        'client_secret': settings.MERCADOLIVRE_CLIENT_SECRET,
        **payload,
    }
    try:
        response = requests.post(
            f"{API_BASE_URL}/oauth/token",
            data=payload,
            headers={'Accept': 'application/json'},
            timeout=10,
        )
    except requests.exceptions.RequestException as e:
        raise MercadoLivreAPIError(f"Erro de rede ao obter token: {e}")

    if response.status_code != 200:
        raise MercadoLivreAPIError(
            f"Falha ao obter token (HTTP {response.status_code}): {response.text[:300]}"
        )
    return _salvar_token(response.json())


def trocar_codigo_por_token(code, redirect_uri):
    """Troca o code recebido no callback do OAuth por access/refresh token"""
    return _pedir_token({
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_uri,
    })


def obter_access_token():
    """Retorna um access token valido, renovando se necessario. None se nao houver."""
    from .models import MercadoLivreToken

    if not credenciais_configuradas():
        return None

    token = MercadoLivreToken.objects.first()
    if not token:
        return None

    if token.expira_em - MARGEM_RENOVACAO > timezone.now():
        return token.access_token

    logger.info("Renovando token do Mercado Livre")
    token = _pedir_token({
        'grant_type': 'refresh_token',
        'refresh_token': token.refresh_token,
    })
    return token.access_token


def extrair_ids(url):
    """
    Extrai da URL o ID do anuncio (item) e o ID do produto de catalogo.

    Exemplos:
      https://www.mercadolivre.com.br/p/MLB2070594105?pdp_filters=item_id%3AMLB7136159042
        -> item_id=MLB7136159042, produto_id=MLB2070594105
      https://produto.mercadolivre.com.br/MLB-7136159042-nome-do-produto-_JM
        -> item_id=MLB7136159042, produto_id=None
    """
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    fragment = parse_qs(parsed.fragment)

    item_id = None
    produto_id = None

    # Anuncio indicado na query (pdp_filters=item_id:MLB..., wid=MLB...)
    candidatos_item = (
        query.get('pdp_filters', []) + query.get('item_id', []) +
        query.get('wid', []) + fragment.get('wid', [])
    )
    for valor in candidatos_item:
        match = ID_RE.search(unquote(valor))
        if match:
            item_id = f"{match.group(1)}{match.group(2)}".upper()
            break

    path = unquote(parsed.path)
    match = ID_RE.search(path)
    if match:
        id_path = f"{match.group(1)}{match.group(2)}".upper()
        if '/p/' in path:
            produto_id = id_path
        elif not item_id:
            item_id = id_path

    return item_id, produto_id


def _get(caminho, access_token):
    try:
        response = requests.get(
            f"{API_BASE_URL}{caminho}",
            headers={'Authorization': f'Bearer {access_token}', 'Accept': 'application/json'},
            timeout=10,
        )
    except requests.exceptions.RequestException as e:
        raise MercadoLivreAPIError(f"Erro de rede ao consultar {caminho}: {e}")

    if response.status_code != 200:
        raise MercadoLivreAPIError(
            f"Falha ao consultar {caminho} (HTTP {response.status_code}): {response.text[:300]}"
        )
    return response.json()


def _primeira_imagem(pictures):
    for picture in pictures or []:
        imagem = picture.get('secure_url') or picture.get('url')
        if imagem:
            return imagem
    return None


def buscar_produto(url):
    """
    Busca titulo, preco e imagem pela API oficial.

    Retorna (titulo, preco, imagem_url), ou None se a API nao estiver
    configurada/autorizada ou a URL nao tiver ID reconhecivel.
    Lanca MercadoLivreAPIError se a API responder com erro.
    """
    item_id, produto_id = extrair_ids(url)
    if not item_id and not produto_id:
        return None

    access_token = obter_access_token()
    if not access_token:
        return None

    if item_id:
        try:
            item = _get(f"/items/{item_id}", access_token)
            titulo = item.get('title')
            if titulo:
                return titulo, item.get('price'), _primeira_imagem(item.get('pictures'))
        except MercadoLivreAPIError:
            # Sem produto de catalogo nao ha alternativa
            if not produto_id:
                raise
            logger.warning(f"Falha ao consultar item {item_id}, tentando produto {produto_id}", exc_info=True)

    produto = _get(f"/products/{produto_id}", access_token)
    preco = (produto.get('buy_box_winner') or {}).get('price')
    return produto.get('name'), preco, _primeira_imagem(produto.get('pictures'))
