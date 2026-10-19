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
    """
    Retorna um access token valido. None se as credenciais nao estiverem configuradas.

    O token e obtido com client_credentials (so o ID e a chave secreta do app);
    um token conectado via OAuth (com refresh token) e renovado pelo refresh.
    """
    from .models import MercadoLivreToken

    if not credenciais_configuradas():
        return None

    token = MercadoLivreToken.objects.first()
    if token and token.expira_em - MARGEM_RENOVACAO > timezone.now():
        return token.access_token

    if token and token.refresh_token:
        logger.info("Renovando token do Mercado Livre pelo refresh token")
        try:
            return _pedir_token({
                'grant_type': 'refresh_token',
                'refresh_token': token.refresh_token,
            }).access_token
        except MercadoLivreAPIError:
            logger.warning("Refresh token do Mercado Livre falhou, usando client_credentials", exc_info=True)

    logger.info("Obtendo token do Mercado Livre por client_credentials")
    return _pedir_token({'grant_type': 'client_credentials'}).access_token


def expandir_link_curto(url, timeout=10):
    """
    Resolve links curtos compartilhados pelo app (ex.: mercadolivre.com/sec/abc, meli.la/abc).

    Segue os redirecionamentos e procura o link do produto nos enderecos
    percorridos; quando o site bloqueia com /gz/account-verification, o link
    original vem no parametro "go". Retorna a URL original se nao achar nada.
    """
    try:
        response = requests.get(url, timeout=timeout, allow_redirects=True,
                                headers={'Accept-Language': 'pt-BR,pt;q=0.9'})
    except requests.exceptions.RequestException as e:
        logger.warning(f"Nao foi possivel expandir o link {url}: {e}")
        return url

    enderecos = [r.headers.get('Location', '') for r in response.history] + [response.url]
    for endereco in enderecos:
        go = parse_qs(urlparse(endereco).query).get('go')
        for candidato in (go or []) + [endereco]:
            if any(extrair_ids(candidato)):
                return candidato
    return url


def eh_link_curto(url):
    parsed = urlparse(url)
    host = (parsed.hostname or '').lower()
    return host in ('meli.la', 'www.meli.la') or (
        host in ('mercadolivre.com', 'www.mercadolivre.com') and parsed.path.startswith('/sec/')
    )


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


def titulo_do_link(url):
    """Titulo a partir do slug do link (ex.: /MLB-123-fone-bluetooth-_JM -> 'Fone bluetooth')"""
    path = unquote(urlparse(url).path)
    match = re.search(r'ML[A-Z]-?\d{6,}-([^/]+)', path, re.IGNORECASE)
    if not match:
        return None
    slug = re.sub(r'-?_JM$', '', match.group(1), flags=re.IGNORECASE)
    titulo = ' '.join(slug.split('-')).strip()
    return titulo[:1].upper() + titulo[1:] if titulo else None


def _titulo_da_descricao(item_id, access_token):
    """
    Primeira linha da descricao do anuncio, que costuma repetir o titulo.

    /items/{id} e bloqueado para anuncios de outros vendedores, mas a descricao
    nao; o nome do produto de catalogo as vezes vem em outro idioma.
    """
    try:
        texto = _get(f"/items/{item_id}/description", access_token).get('plain_text') or ''
    except MercadoLivreAPIError:
        return None
    linhas = [linha.strip() for linha in texto.splitlines() if linha.strip()]
    if linhas and 10 <= len(linhas[0]) <= 150:
        return linhas[0]
    return None


def _preco_do_anuncio(produto_id, item_id, access_token):
    """
    Preco do anuncio dentro do produto de catalogo.

    Retorna (preco, anuncio_encontrado). Sem item_id, usa o menor preco.
    """
    dados = _get(f"/products/{produto_id}/items", access_token)
    anuncios = dados.get('results') or []
    for anuncio in anuncios:
        if item_id and anuncio.get('item_id') == item_id:
            return anuncio.get('price'), True
    precos = [a['price'] for a in anuncios if a.get('price') is not None]
    return (min(precos) if precos else None), False


def _produto_do_anuncio(titulo, item_id, access_token, limite=5):
    """Procura no catalogo o produto que contem o anuncio. Retorna (produto_id, preco) ou None."""
    resultados = _get(
        f"/products/search?{urlencode({'status': 'active', 'site_id': 'MLB', 'q': titulo})}",
        access_token,
    ).get('results') or []
    for produto in resultados[:limite]:
        produto_id = produto.get('id')
        if not produto_id:
            continue
        try:
            preco, encontrado = _preco_do_anuncio(produto_id, item_id, access_token)
        except MercadoLivreAPIError:
            continue
        if encontrado:
            return produto_id, preco
    return None


def buscar_produto(url):
    """
    Busca titulo, preco e imagem pela API oficial.

    A API nao libera /items de anuncios de outros vendedores (403), mas libera
    o catalogo: /products/{id} (nome e fotos) e /products/{id}/items (precos).

    Retorna (titulo, preco, imagem_url), ou None se a API nao estiver
    configurada ou a URL nao tiver ID reconhecivel.
    Lanca MercadoLivreAPIError se a API responder com erro.
    """
    item_id, produto_id = extrair_ids(url)
    if not item_id and not produto_id and eh_link_curto(url):
        url = expandir_link_curto(url)
        item_id, produto_id = extrair_ids(url)
    if not item_id and not produto_id:
        return None

    access_token = obter_access_token()
    if not access_token:
        return None

    titulo_anuncio = (_titulo_da_descricao(item_id, access_token) if item_id else None) or titulo_do_link(url)
    preco = None

    if not produto_id:
        # Link so de anuncio: acha o produto de catalogo pelo titulo
        if not titulo_anuncio:
            return None
        encontrado = _produto_do_anuncio(titulo_anuncio, item_id, access_token)
        if not encontrado:
            # Anuncio fora do catalogo: so o titulo
            return titulo_anuncio, None, None
        produto_id, preco = encontrado

    produto = _get(f"/products/{produto_id}", access_token)
    if preco is None:
        try:
            preco, _ = _preco_do_anuncio(produto_id, item_id, access_token)
        except MercadoLivreAPIError:
            logger.warning(f"Sem preco para o produto {produto_id}", exc_info=True)
    if preco is None:
        preco = (produto.get('buy_box_winner') or {}).get('price')

    titulo = titulo_anuncio or produto.get('name')
    return titulo, preco, _primeira_imagem(produto.get('pictures'))
