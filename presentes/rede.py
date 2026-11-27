"""
Acesso a URLs informadas por usuarios e validacao de imagens.

Toda busca feita pelo servidor a partir de um endereco vindo de fora (foto
por URL, pagina de produto, link curto) passa por aqui, para que o servidor
nao seja usado para alcancar a rede interna, e toda imagem guardada no banco
e conferida pelo conteudo, nao pelo tipo que o remetente declarou.
"""
import io
import ipaddress
import socket
from urllib.parse import urljoin, urlparse

import requests

ESQUEMAS_PERMITIDOS = {'http', 'https'}

# Formatos aceitos para guardar e servir. SVG fica de fora de proposito:
# e um documento que pode carregar script.
TIPOS_IMAGEM = {
    'JPEG': 'image/jpeg',
    'PNG': 'image/png',
    'GIF': 'image/gif',
    'WEBP': 'image/webp',
}
TIPOS_IMAGEM_PERMITIDOS = set(TIPOS_IMAGEM.values())
EXTENSOES = {'image/jpeg': 'jpg', 'image/png': 'png', 'image/gif': 'gif', 'image/webp': 'webp'}

TAMANHO_MAXIMO_IMAGEM = 5 * 1024 * 1024


class DestinoBloqueado(requests.exceptions.RequestException):
    """Endereco recusado: esquema invalido ou destino fora da internet publica.

    Herda de RequestException para cair nos mesmos tratamentos de erro de
    rede que ja existem em quem chama.
    """


def validar_destino(url):
    """Recusa URLs que nao sejam http(s) ou que apontem para IPs nao publicos.

    Resolve o nome e confere todos os enderecos devolvidos (loopback, rede
    privada, link-local/metadados de nuvem, CGNAT, reservados etc.). Se o nome
    nao resolver, deixa passar: a requisicao vai falhar do mesmo jeito.
    """
    partes = urlparse(url or '')
    if partes.scheme.lower() not in ESQUEMAS_PERMITIDOS:
        raise DestinoBloqueado(f'Esquema de URL não permitido: {partes.scheme or "(vazio)"}')
    host = partes.hostname
    if not host:
        raise DestinoBloqueado('URL sem host')
    try:
        porta = partes.port or (443 if partes.scheme.lower() == 'https' else 80)
    except ValueError:
        raise DestinoBloqueado('Porta inválida na URL')
    try:
        enderecos = [ipaddress.ip_address(host)]
    except ValueError:
        try:
            resolvidos = socket.getaddrinfo(host, porta, proto=socket.IPPROTO_TCP)
        except (socket.gaierror, UnicodeError):
            return
        enderecos = [ipaddress.ip_address(sockaddr[0].split('%')[0]) for *_, sockaddr in resolvidos]
    for ip in enderecos:
        if not _ip_publico(ip):
            raise DestinoBloqueado(f'Destino não permitido: {host}')


def _ip_publico(ip):
    mapeado = getattr(ip, 'ipv4_mapped', None)
    if mapeado is not None:
        ip = mapeado
    return ip.is_global and not ip.is_multicast


def _conferir_redirecionamento(resposta, *args, **kwargs):
    """Hook do requests: valida o proximo salto antes de ele ser seguido."""
    if getattr(resposta, 'is_redirect', False):
        destino = resposta.headers.get('Location', '')
        validar_destino(urljoin(resposta.url, destino))
    return resposta


def obter(url, **kwargs):
    """requests.get com o destino e cada redirecionamento validados."""
    validar_destino(url)
    hooks = dict(kwargs.pop('hooks', None) or {})
    existentes = hooks.get('response') or []
    if callable(existentes):
        existentes = [existentes]
    hooks['response'] = [_conferir_redirecionamento, *existentes]
    return requests.get(url, hooks=hooks, **kwargs)


def identificar_imagem(dados):
    """Devolve o MIME real da imagem (pelo conteudo) ou None se nao for aceita."""
    if not dados or len(dados) > TAMANHO_MAXIMO_IMAGEM:
        return None
    try:
        from PIL import Image
        with Image.open(io.BytesIO(dados)) as imagem:
            formato = imagem.format
            imagem.verify()
    except Exception:
        return None
    return TIPOS_IMAGEM.get(formato)
