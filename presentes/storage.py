"""
Imagens no Supabase Storage.

As imagens saem da tabela (base64) e vão para um bucket PRIVADO. Só o
servidor fala com o Storage, usando a chave de serviço; o navegador recebe,
depois de a rota de imagem conferir login e grupo, um redirecionamento para
uma URL assinada que expira.

Sem SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY configuradas, nada disso é
usado e as imagens continuam no banco (desenvolvimento local e testes).
"""
import logging
import uuid

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

TIMEOUT = 20
# URL assinada vale 7 dias; guardamos por 6 para nunca entregar uma vencida
VALIDADE_URL_ASSINADA = 7 * 24 * 3600
CACHE_URL_ASSINADA = 6 * 24 * 3600


class ErroStorage(Exception):
    pass


def configurado():
    return bool(getattr(settings, 'SUPABASE_URL', '') and getattr(settings, 'SUPABASE_SERVICE_ROLE_KEY', ''))


def _base():
    return settings.SUPABASE_URL.rstrip('/') + '/storage/v1'


def _bucket():
    return getattr(settings, 'SUPABASE_STORAGE_BUCKET', '') or 'lista-presentes'


def _cabecalhos(extra=None):
    chave = settings.SUPABASE_SERVICE_ROLE_KEY
    cabecalhos = {'apikey': chave}
    # Chave legada (JWT) também vai no Authorization; as novas (sb_secret_...) só no apikey
    if chave.startswith('eyJ'):
        cabecalhos['Authorization'] = f'Bearer {chave}'
    cabecalhos.update(extra or {})
    return cabecalhos


def novo_caminho(pasta, extensao):
    """Caminho único por envio: a URL muda junto com a imagem."""
    return f'{pasta}/{uuid.uuid4().hex}.{extensao}'


def garantir_bucket():
    """Cria o bucket privado se ainda não existir."""
    resposta = requests.post(f'{_base()}/bucket', headers=_cabecalhos(), timeout=TIMEOUT, json={
        'id': _bucket(), 'name': _bucket(), 'public': False,
        'allowed_mime_types': ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
    })
    if resposta.status_code in (200, 201):
        return True
    if 'already exists' in resposta.text.lower() or resposta.status_code == 409:
        return False
    raise ErroStorage(f'Não foi possível criar o bucket: HTTP {resposta.status_code} {resposta.text[:200]}')


def enviar(caminho, dados, content_type):
    resposta = requests.post(
        f'{_base()}/object/{_bucket()}/{caminho}', data=dados, timeout=TIMEOUT,
        headers=_cabecalhos({'Content-Type': content_type, 'x-upsert': 'true',
                             # o caminho muda a cada imagem, então o arquivo nunca muda
                             'cache-control': 'max-age=31536000'}),
    )
    if resposta.status_code not in (200, 201):
        raise ErroStorage(f'Falha ao enviar {caminho}: HTTP {resposta.status_code} {resposta.text[:200]}')


def remover(caminho):
    if not caminho or not configurado():
        return
    try:
        resposta = requests.delete(f'{_base()}/object/{_bucket()}', headers=_cabecalhos(),
                                   json={'prefixes': [caminho]}, timeout=TIMEOUT)
        if resposta.status_code not in (200, 204):
            logger.warning(f'Storage: falha ao remover {caminho}: HTTP {resposta.status_code}')
    except requests.RequestException as e:
        logger.warning(f'Storage: falha ao remover {caminho}: {e}')
    cache.delete(f'storage-url:{caminho}')


def url_assinada(caminho):
    """URL temporária para o navegador baixar o arquivo (guardada em cache)."""
    chave_cache = f'storage-url:{caminho}'
    url = cache.get(chave_cache)
    if url:
        return url
    resposta = requests.post(f'{_base()}/object/sign/{_bucket()}/{caminho}', headers=_cabecalhos(),
                             json={'expiresIn': VALIDADE_URL_ASSINADA}, timeout=TIMEOUT)
    if resposta.status_code != 200:
        raise ErroStorage(f'Falha ao assinar {caminho}: HTTP {resposta.status_code} {resposta.text[:200]}')
    assinada = resposta.json().get('signedURL') or resposta.json().get('signedUrl')
    if not assinada:
        raise ErroStorage(f'Resposta sem URL assinada para {caminho}')
    url = assinada if assinada.startswith('http') else _base() + assinada
    cache.set(chave_cache, url, CACHE_URL_ASSINADA)
    return url
