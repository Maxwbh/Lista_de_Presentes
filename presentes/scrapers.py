"""
Scrapers específicos para diferentes lojas online.
Cada loja tem sua própria lógica de extração otimizada.
"""
import requests
from bs4 import BeautifulSoup
import json
import re
import logging
import threading
from contextlib import contextmanager
from urllib.parse import urlparse

from .precos import converter_preco

logger = logging.getLogger(__name__)

# Loggers cujas mensagens entram nas issues automaticas, para a issue mostrar
# o que aconteceu na leitura (chamadas da API, respostas HTTP, avisos)
LOGGERS_EXTRACAO = ('presentes.scrapers', 'presentes.mercadolivre_api')


class _CapturaLog(logging.Handler):
    """Guarda as mensagens de log da thread que esta fazendo a extracao."""

    def __init__(self, limite=40):
        super().__init__(logging.INFO)
        self.thread = threading.get_ident()
        self.limite = limite
        self.linhas = []

    def emit(self, record):
        if record.thread != self.thread:
            return
        mensagem = record.getMessage().strip()
        if not mensagem or set(mensagem) <= set('= '):
            return
        if record.exc_info and record.exc_info[1]:
            mensagem += f" ({type(record.exc_info[1]).__name__}: {record.exc_info[1]})"
        self.linhas.append(f"{record.levelname} {record.name.rsplit('.', 1)[-1]}: {mensagem[:400]}")
        del self.linhas[:-self.limite]


@contextmanager
def capturar_log_extracao():
    captura = _CapturaLog()
    loggers = [logging.getLogger(nome) for nome in LOGGERS_EXTRACAO]
    for log in loggers:
        log.addHandler(captura)
    try:
        yield captura.linhas
    finally:
        for log in loggers:
            log.removeHandler(captura)


# Parametros de rastreamento (ex.: utm_source=...) nao identificam o produto
# e nao devem ir para a leitura nem para as issues
PARAMETROS_RASTREIO = re.compile(r'^(utm_\w+|gclid|fbclid|gad_source|srsltid)$', re.IGNORECASE)


def limpar_url_rastreio(url):
    """Remove da URL os parametros de rastreamento (utm_*, gclid, fbclid...)"""
    from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

    partes = urlsplit(url)
    if not partes.query:
        return url
    query = [(k, v) for k, v in parse_qsl(partes.query, keep_blank_values=True)
             if not PARAMETROS_RASTREIO.match(k)]
    return urlunsplit(partes._replace(query=urlencode(query)))


def secao_log_extracao(linhas):
    """Secao markdown com o log da extracao, para o corpo das issues"""
    if not linhas:
        return ''
    texto = '\n'.join(linhas).replace('```', "'''")
    return f"\n### Log da Extração\n```\n{texto}\n```\n"


class ScrapingError(Exception):
    """Excecao base para erros de scraping"""
    pass


class NetworkError(ScrapingError):
    """Erro de rede/HTTP (timeout, 404, 500, etc.) - NAO gera issue"""
    pass


class BlockedError(NetworkError):
    """Site respondeu com pagina de verificacao/anti-robo em vez do produto - NAO gera issue"""
    pass


# Trechos de URL de paginas de verificacao anti-robo (ex.: Mercado Livre
# redireciona para /gz/account-verification quando bloqueia a requisicao)
BLOCKED_URL_MARKERS = (
    '/gz/account-verification',
    '/captcha',
    '/challenge',
)


# Titulos de paginas de verificacao anti-robo (ex.: "Radware Bot Manager Captcha")
BLOCKED_TITLE_MARKERS = (
    'captcha',
    'bot manager',
    'attention required',
    'just a moment',
    'access denied',
    'acesso negado',
    'are you a robot',
    'are you human',
)


class ParsingError(ScrapingError):
    """Erro de parsing/extracao de dados (site acessivel mas dados nao extraidos) - GERA issue"""
    pass


class BaseScraper:
    """Classe base para scrapers de lojas"""

    def __init__(self):
        # Explicacao para o usuario quando a leitura vem incompleta por um
        # limite conhecido da loja (nao e falha do scraper)
        self.aviso = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        }

    def get_soup(self, url, timeout=10):
        """
        Obtém BeautifulSoup de uma URL.

        Lanca NetworkError para erros HTTP/rede (404, 500, timeout, etc.)
        Lanca BlockedError se o site redirecionar para pagina anti-robo.
        Retorna BeautifulSoup se sucesso.
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=timeout)
            response.raise_for_status()
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout ao acessar {url}: {str(e)}")
            raise NetworkError(f"Timeout ao acessar URL: {str(e)}")
        except requests.exceptions.HTTPError as e:
            # Erros HTTP (404, 500, etc.)
            logger.error(f"Erro HTTP ao acessar {url}: {str(e)}")
            raise NetworkError(f"Erro HTTP {e.response.status_code}: {str(e)}")
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Erro de conexao ao acessar {url}: {str(e)}")
            raise NetworkError(f"Erro de conexao: {str(e)}")
        except requests.exceptions.RequestException as e:
            # Outros erros de request
            logger.error(f"Erro de rede ao acessar {url}: {str(e)}")
            raise NetworkError(f"Erro de rede: {str(e)}")
        except Exception as e:
            # Erros inesperados (parsing HTML, etc.)
            logger.error(f"Erro inesperado ao obter página {url}: {str(e)}")
            raise NetworkError(f"Erro inesperado: {str(e)}")

        # Alguns sites (ex.: Mercado Livre) respondem 200 mas redirecionam
        # para uma pagina de verificacao anti-robo em vez do produto
        final_url = (response.url or '').lower()
        if any(marker in final_url for marker in BLOCKED_URL_MARKERS):
            logger.warning(f"Acesso bloqueado por verificacao anti-robo em {url} (redirecionado para {response.url})")
            raise BlockedError("O site bloqueou a consulta automática (verificação anti-robô)")

        soup = BeautifulSoup(response.content, 'html.parser')

        # Paginas de captcha/anti-robo que respondem 200 no proprio endereco
        titulo_pagina = (soup.title.get_text(' ', strip=True) if soup.title else '').lower()
        logger.info(f"Página obtida: HTTP {response.status_code}, {len(response.content)} bytes, "
                    f"URL final {response.url}, título da página: {titulo_pagina[:100] or '(vazio)'}")
        if any(marcador in titulo_pagina for marcador in BLOCKED_TITLE_MARKERS):
            logger.warning(f"Acesso bloqueado por verificacao anti-robo em {url} (titulo: {titulo_pagina[:80]})")
            raise BlockedError("O site bloqueou a consulta automática (verificação anti-robô)")

        return soup

    def clean_price(self, price_str):
        """Converte o texto do preço para float (ver presentes.precos.converter_preco)"""
        return converter_preco(price_str)

    def preco_de_meta(self, valor):
        """
        Preco de meta tag/JSON-LD (schema.org), que vem em formato de maquina:
        ponto como separador decimal ('254.00', '1371.6'). Se vier formatado
        para leitura ('R$ 1.371,60'), usa clean_price.
        """
        return converter_preco(valor)

    @staticmethod
    def moeda_da_pagina(soup):
        """Moeda do preco informada nas meta tags (ex.: 'USD'), ou None"""
        for atributos in ({'property': 'product:price:currency'}, {'property': 'og:price:currency'},
                          {'itemprop': 'priceCurrency'}):
            meta = soup.find('meta', attrs=atributos)
            if meta and meta.get('content'):
                return meta['content'].strip().upper()
        return None

    def _produtos_json_ld(self, soup):
        """Objetos Product/ProductGroup do JSON-LD da pagina"""
        produtos = []
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                dados = json.loads(script.string or script.get_text() or '')
            except ValueError:
                continue
            for item in dados if isinstance(dados, list) else [dados]:
                if isinstance(item, dict) and item.get('@type') in ('Product', 'ProductGroup'):
                    produtos.append(item)
        return produtos

    @staticmethod
    def _preco_oferta(produto):
        ofertas = produto.get('offers') or {}
        for oferta in ofertas if isinstance(ofertas, list) else [ofertas]:
            preco = oferta.get('price') or oferta.get('lowPrice')
            preco = converter_preco(preco)
            if preco:
                return preco
        return None

    def _preco(self, produto, sku_id):
        """Preco da variante do link (?skuId=), senao da primeira em estoque, senao o menor"""
        variantes = produto.get('hasVariant') or [produto]
        if sku_id:
            for variante in variantes:
                if str(variante.get('sku')) == sku_id:
                    preco = self._preco_oferta(variante)
                    if preco:
                        return preco
        em_estoque = [v for v in variantes
                      if 'InStock' in str((v.get('offers') or {}).get('availability', ''))]
        for variante in em_estoque:
            preco = self._preco_oferta(variante)
            if preco:
                return preco
        precos = [p for p in (self._preco_oferta(v) for v in variantes) if p]
        return min(precos) if precos else None

    def preco_dados_estruturados(self, soup, sku_id=None):
        """
        Preco dos dados estruturados (schema.org) da pagina: primeiro o
        JSON-LD; senao, ofertas embutidas em scripts/atributos (lojas VTEX e
        deco.cx, ex.: Farm Rio, guardam o produto com URL-encoding num
        atributo). So aceita ofertas em reais.
        """
        produtos = self._produtos_json_ld(soup)
        if produtos:
            preco = self._preco(produtos[0], sku_id)
            if preco:
                return preco

        from urllib.parse import unquote
        html = unquote(str(soup))
        for oferta in re.finditer(r'"priceCurrency"\s*:\s*"BRL"', html):
            trecho = html[oferta.end():oferta.end() + 400]
            valor = re.search(r'"(?:lowPrice|price)"\s*:\s*"?(\d+(?:\.\d+)?)', trecho)
            if valor:
                preco = converter_preco(valor.group(1))
                if preco:
                    return preco
        return None

    def extract(self, url):
        """Método a ser implementado por subclasses"""
        raise NotImplementedError


class AmazonScraper(BaseScraper):
    """Scraper específico para Amazon Brasil"""

    def __init__(self):
        super().__init__()
        # Headers mais completos para Amazon
        self.headers.update({
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://www.amazon.com.br/',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })

    def extract(self, url):
        """
        Extrai informações de produtos da Amazon.
        Retorna: (titulo, preco, imagem_url)
        Lanca NetworkError para erros de rede/HTTP.
        Lanca ParsingError se conseguir acessar mas nao extrair dados minimos.
        """
        # get_soup() pode lancar NetworkError (propagamos)
        soup = self.get_soup(url)

        titulo = None
        preco = None
        imagem_url = None

        # Título - Amazon tem IDs específicos + mais alternativas
        title_candidates = [
            soup.find('span', id='productTitle'),
            soup.find('h1', id='title'),
            soup.find('h1', class_='a-size-large'),
            soup.find('span', {'class': 'product-title-word-break'}),
            soup.find('h1', {'class': 'a-size-large a-spacing-none'}),
        ]

        for candidate in title_candidates:
            if candidate:
                titulo = candidate.get_text(strip=True)
                if titulo:  # Verifica se não está vazio
                    break

        # Preço - Amazon tem várias possibilidades + mais alternativas
        price_candidates = [
            # Preço principal
            soup.find('span', class_='a-price-whole'),
            # Preço de oferta
            soup.find('span', class_='a-offscreen'),
            # Preço no deal
            soup.find('span', class_='priceBlockBuyingPriceString'),
            # Preço atual
            soup.find('span', {'class': 'a-price aok-align-center reinventPricePriceToPayMargin priceToPay'}),
            # Preço no elemento data
            soup.find('span', {'data-a-color': 'price'}),
            # Preço em divs específicas
            soup.select_one('.a-price .a-offscreen'),
            soup.select_one('#priceblock_ourprice'),
            soup.select_one('#priceblock_dealprice'),
        ]

        for candidate in price_candidates:
            if candidate:
                price_text = candidate.get_text(strip=True)
                preco = self.clean_price(price_text)
                if preco:
                    break

        # Imagem - Amazon tem imgTagWrapper + mais alternativas
        img_candidates = [
            soup.find('img', id='landingImage'),
            soup.find('img', class_='a-dynamic-image'),
            soup.find('div', id='imgTagWrapperId'),
            soup.find('img', {'data-a-image-name': 'landingImage'}),
            soup.select_one('#imageBlock img'),
            soup.select_one('.imgTagWrapper img'),
        ]

        for candidate in img_candidates:
            if candidate:
                if candidate.name == 'img':
                    imagem_url = candidate.get('src') or candidate.get('data-old-hires') or candidate.get('data-a-dynamic-image')
                    # Se data-a-dynamic-image é um JSON, pegar a primeira URL
                    if imagem_url and imagem_url.startswith('{'):
                        try:
                            import json
                            images = json.loads(imagem_url)
                            if images:
                                imagem_url = list(images.keys())[0]
                        except:
                            pass
                else:
                    img = candidate.find('img')
                    if img:
                        imagem_url = img.get('src') or img.get('data-old-hires') or img.get('data-a-dynamic-image')

                if imagem_url and imagem_url.startswith('http'):
                    break

        # Log do resultado detalhado (visível no console Render)
        logger.info("=" * 80)
        logger.info(f"🛍️  AMAZON SCRAPING - URL: {url[:80]}...")
        logger.info(f"   📝 Título:  {'✅ Extraído' if titulo else '❌ FALHOU'} - {titulo[:60] if titulo else 'N/A'}...")
        logger.info(f"   💰 Preço:   {'✅ Extraído' if preco else '⚠️  Não encontrado'} - R$ {preco if preco else 'N/A'}")
        logger.info(f"   🖼️  Imagem:  {'✅ Extraída' if imagem_url else '⚠️  Não encontrada'}")
        logger.info("=" * 80)

        # Se nao conseguiu extrair NENHUM titulo, lancar ParsingError
        if not titulo:
            # Log de erro crítico (visível no Render)
            logger.error("!" * 80)
            logger.error("❌ ERRO CRÍTICO DE SCRAPING - AMAZON")
            logger.error(f"   URL: {url}")
            logger.error(f"   Título: Não extraído ❌")
            logger.error(f"   Preço: {f'R$ {preco}' if preco else 'Não extraído'}")
            logger.error(f"   Imagem: {'Extraída ✅' if imagem_url else 'Não extraída'}")
            logger.error("   ")
            logger.error("   ⚠️  ATENÇÃO: Issue será criada automaticamente no GitHub")
            logger.error("!" * 80)

            # Log HTML para debug (primeiros 1000 chars)
            html_snippet = str(soup)[:1000] if soup else 'N/A'
            logger.debug(f"Amazon ParsingError - HTML snippet: {html_snippet}")

            raise ParsingError(f"Nao foi possivel extrair titulo da Amazon. Dados parciais: preco={preco}, imagem={bool(imagem_url)}")

        return (titulo, preco, imagem_url)


AVISO_ML_FORA_DO_CATALOGO = (
    'Anúncio fora do catálogo do Mercado Livre: a API oficial não informa preço e foto '
    'de anúncios de outros vendedores, e a página exige verificação de conta. '
    'Preencha o preço e a foto manualmente.'
)


class MercadoLivreScraper(BaseScraper):
    """Scraper específico para Mercado Livre"""

    def extract(self, url):
        """
        Extrai informações de produtos do Mercado Livre.
        Retorna: (titulo, preco, imagem_url)
        Lanca NetworkError para erros de rede/HTTP.
        Lanca ParsingError se conseguir acessar mas nao extrair dados minimos.
        """
        # A API oficial e o caminho preferido: o site bloqueia consultas
        # automaticas com uma pagina de verificacao anti-robo
        from .mercadolivre_api import buscar_produto, MercadoLivreAPIError
        try:
            resultado = buscar_produto(url)
            if resultado and resultado[0]:
                logger.info(f"Mercado Livre (API) - Título: True, Preço: {resultado[1]}, Imagem: {bool(resultado[2])}")
                if not resultado[1] and not resultado[2]:
                    self.aviso = AVISO_ML_FORA_DO_CATALOGO
                return resultado
        except MercadoLivreAPIError as e:
            logger.warning(f"API do Mercado Livre falhou, tentando a pagina: {e}")

        # get_soup() pode lancar NetworkError (propagamos)
        soup = self.get_soup(url)

        titulo = None
        preco = None
        imagem_url = None

        # Título - Mercado Livre usa h1.ui-pdp-title
        title_candidates = [
            soup.find('h1', class_='ui-pdp-title'),
            soup.find('h1', class_=re.compile('title')),
        ]

        for candidate in title_candidates:
            if candidate:
                titulo = candidate.get_text(strip=True)
                break

        # Preço - Mercado Livre tem classes específicas
        price_candidates = [
            soup.find('span', class_='andes-money-amount__fraction'),
            soup.find('span', class_=re.compile('price-tag-fraction')),
            soup.find('meta', property='product:price:amount'),
        ]

        for candidate in price_candidates:
            if candidate:
                if candidate.name == 'meta':
                    preco = self.preco_de_meta(candidate.get('content', ''))
                else:
                    preco = self.clean_price(candidate.get_text(strip=True))
                if preco:
                    break

        # Imagem - Mercado Livre tem figura principal
        img_candidates = [
            soup.find('figure', class_='ui-pdp-gallery__figure'),
            soup.find('img', class_='ui-pdp-image'),
            soup.find('meta', property='og:image'),
        ]

        for candidate in img_candidates:
            if candidate:
                if candidate.name == 'meta':
                    imagem_url = candidate.get('content')
                elif candidate.name == 'img':
                    imagem_url = candidate.get('src') or candidate.get('data-src')
                else:
                    img = candidate.find('img')
                    if img:
                        imagem_url = img.get('src') or img.get('data-src')

                if imagem_url:
                    break

        # Log do resultado
        logger.info(f"Mercado Livre - Título: {bool(titulo)}, Preço: {preco}, Imagem: {bool(imagem_url)}")

        # Se nao conseguiu extrair NENHUM titulo, lancar ParsingError
        if not titulo:
            raise ParsingError(f"Nao foi possivel extrair titulo do Mercado Livre. Dados parciais: preco={preco}, imagem={bool(imagem_url)}")

        return (titulo, preco, imagem_url)


class KabumScraper(BaseScraper):
    """Scraper específico para Kabum"""

    def extract(self, url):
        """
        Extrai informações de produtos do Kabum.
        Retorna: (titulo, preco, imagem_url)
        Lanca NetworkError para erros de rede/HTTP.
        Lanca ParsingError se conseguir acessar mas nao extrair dados minimos.
        """
        # get_soup() pode lancar NetworkError (propagamos)
        soup = self.get_soup(url)

        titulo = None
        preco = None
        imagem_url = None

        # Título
        title_candidates = [
            soup.find('h1', class_=re.compile('title|product')),
            soup.find('h1'),
        ]

        for candidate in title_candidates:
            if candidate:
                titulo = candidate.get_text(strip=True)
                break

        # Preço
        price_candidates = [
            soup.find('span', class_=re.compile('price|preco')),
            soup.find('h4', class_=re.compile('price|preco')),
        ]

        for candidate in price_candidates:
            if candidate:
                price_text = candidate.get_text(strip=True)
                preco = self.clean_price(price_text)
                if preco:
                    break

        # Imagem
        imagem_url = None
        og_image = soup.find('meta', property='og:image')
        if og_image:
            imagem_url = og_image.get('content')

        logger.info(f"Kabum - Título: {bool(titulo)}, Preço: {preco}, Imagem: {bool(imagem_url)}")

        # Se nao conseguiu extrair NENHUM titulo, lancar ParsingError
        if not titulo:
            raise ParsingError(f"Nao foi possivel extrair titulo do Kabum. Dados parciais: preco={preco}, imagem={bool(imagem_url)}")

        return (titulo, preco, imagem_url)


class DecathlonScraper(BaseScraper):
    """
    Scraper especifico para a Decathlon Brasil (loja VTEX).

    O preco nao vem em meta tags: fica no JSON-LD (schema.org) da pagina,
    dentro de um ProductGroup com uma variante (Product) por tamanho/cor.
    """

    def extract(self, url):
        """
        Retorna: (titulo, preco, imagem_url)
        Lanca NetworkError para erros de rede/HTTP.
        Lanca ParsingError se conseguir acessar mas nao extrair o titulo.
        """
        from urllib.parse import parse_qs

        soup = self.get_soup(url)
        produtos = self._produtos_json_ld(soup)
        produto = produtos[0] if produtos else {}
        if not produtos:
            logger.info("Decathlon: página sem JSON-LD de produto")

        titulo = produto.get('name')
        if not titulo:
            og_title = soup.find('meta', property='og:title')
            titulo = og_title.get('content') if og_title else None

        sku_id = (parse_qs(urlparse(url).query).get('skuId') or [None])[0]
        preco = self._preco(produto, sku_id) if produto else None

        imagens = produto.get('image')
        imagem_url = imagens[0] if isinstance(imagens, list) and imagens else imagens
        if not imagem_url:
            og_image = soup.find('meta', property='og:image')
            imagem_url = og_image.get('content') if og_image else None

        logger.info(f"Decathlon - Título: {bool(titulo)}, Preço: {preco}, Imagem: {bool(imagem_url)}")

        if not titulo:
            raise ParsingError(f"Nao foi possivel extrair titulo da Decathlon. Dados parciais: preco={preco}, imagem={bool(imagem_url)}")

        return (titulo.strip()[:200], preco, imagem_url)


class GenericScraper(BaseScraper):
    """Scraper genérico para qualquer loja"""

    def extract(self, url):
        """
        Extrai informações usando meta tags genéricas.
        Retorna: (titulo, preco, imagem_url)
        Lanca NetworkError para erros de rede/HTTP.
        Lanca ParsingError se conseguir acessar mas nao extrair dados minimos.
        """
        # get_soup() pode lancar NetworkError (propagamos)
        soup = self.get_soup(url)

        titulo = None
        preco = None
        imagem_url = None

        # Título - tentar meta tags primeiro
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            titulo = og_title.get('content')

        if not titulo:
            twitter_title = soup.find('meta', attrs={'name': 'twitter:title'})
            if twitter_title and twitter_title.get('content'):
                titulo = twitter_title.get('content')

        if not titulo and soup.title:
            titulo = soup.title.string

        if not titulo:
            h1 = soup.find('h1')
            if h1:
                titulo = h1.get_text(strip=True)

        if titulo:
            titulo = re.sub(r'\s*[\|\-]\s*[A-Za-z0-9\s]+$', '', titulo)
            titulo = titulo.strip()[:200]

        # Preço - tentar várias estratégias
        price_patterns = [
            r'R\$?\s*(\d+(?:[.,]\d{3})*(?:[.,]\d{2}))',
            r'(\d+(?:[.,]\d{3})*(?:[.,]\d{2}))\s*reais?',
        ]

        moeda = self.moeda_da_pagina(soup)
        if moeda and moeda != 'BRL':
            # Preco em outra moeda (ex.: lojas do Paraguai em US$): usa o valor
            # em reais que a pagina mostra entre parenteses, ex. 'US$ 254,00 (R$ 1.371,60)'
            logger.info(f"Preço da página em {moeda}; procurando o valor em reais")
            em_reais = re.search(r'\(\s*R\$\s*(\d{1,3}(?:\.\d{3})*,\d{2})\s*\)', soup.get_text(' '))
            if em_reais:
                preco = self.clean_price(em_reais.group(1))
        else:
            price_meta = soup.find('meta', property='product:price:amount') or soup.find('meta', attrs={'itemprop': 'price'})
            if price_meta and price_meta.get('content'):
                preco = self.preco_de_meta(price_meta.get('content'))

        if not preco and (not moeda or moeda == 'BRL'):
            preco = self.preco_dados_estruturados(soup)

        # Com moeda estrangeira, so o valor em reais da pagina serve: os
        # textos de preco estariam em outra moeda
        if not preco and (not moeda or moeda == 'BRL'):
            price_elements = soup.find_all(['span', 'div', 'strong', 'p'], class_=re.compile(r'price|preco|valor|value', re.I))
            for elem in price_elements:
                text = elem.get_text(strip=True)
                for pattern in price_patterns:
                    match = re.search(pattern, text, re.I)
                    if match:
                        preco = self.clean_price(match.group(1))
                        if preco:
                            break
                if preco:
                    break

        # Imagem
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            imagem_url = og_image.get('content')

        if not imagem_url:
            twitter_image = soup.find('meta', attrs={'name': 'twitter:image'})
            if twitter_image and twitter_image.get('content'):
                imagem_url = twitter_image.get('content')

        if imagem_url and not imagem_url.startswith('http'):
            from urllib.parse import urljoin
            imagem_url = urljoin(url, imagem_url)

        logger.info(f"Generic - Título: {bool(titulo)}, Preço: {preco}, Imagem: {bool(imagem_url)}")

        # Se nao conseguiu extrair NENHUM titulo, lancar ParsingError
        if not titulo:
            raise ParsingError(f"Nao foi possivel extrair titulo (scraper generico). Dados parciais: preco={preco}, imagem={bool(imagem_url)}")

        return (titulo, preco, imagem_url)


class ScraperFactory:
    """Fábrica para selecionar o scraper apropriado baseado na URL"""

    @staticmethod
    def get_scraper(url):
        """
        Retorna o scraper apropriado baseado na URL.
        Retorna: (scraper, is_generic)
        """
        domain = urlparse(url).netloc.lower()

        # amzn.to e a.co: links curtos da Amazon (o requests segue o redirecionamento)
        if 'amazon.com' in domain or domain in ('amzn.to', 'www.amzn.to', 'a.co', 'amzn.com'):
            logger.info(f"🛍️  Usando AmazonScraper para {domain}")
            return AmazonScraper(), False
        elif 'mercadolivre.com' in domain or 'mercadolibre.com' in domain or domain.endswith('meli.la'):
            logger.info(f"🛒 Usando MercadoLivreScraper para {domain}")
            return MercadoLivreScraper(), False
        elif 'kabum.com' in domain:
            logger.info(f"🎮 Usando KabumScraper para {domain}")
            return KabumScraper(), False
        elif 'decathlon.com' in domain:
            logger.info(f"🏃 Usando DecathlonScraper para {domain}")
            return DecathlonScraper(), False
        else:
            logger.warning("=" * 80)
            logger.warning(f"⚠️  SITE NÃO MAPEADO: {domain}")
            logger.warning(f"   URL: {url}")
            logger.warning(f"   ")
            logger.warning(f"   ℹ️  Usando scraper genérico (pode ter menor taxa de sucesso)")
            logger.warning(f"   💡 Considere adicionar suporte específico para este site")
            logger.warning("=" * 80)
            return GenericScraper(), True

    @staticmethod
    def extract_product_info(url):
        """
        Extrai informações de produto usando o scraper apropriado.

        Retorna:
            - Em caso de sucesso: dict com {
                'success': True,
                'titulo': str,
                'preco': float or None,
                'imagem_url': str or None
              }
            - Em caso de erro de rede/HTTP: dict com {
                'success': False,
                'error_type': 'network',
                'error_message': str
              }
            - Em caso de erro de parsing: dict com {
                'success': False,
                'error_type': 'parsing',
                'error_message': str,
                'partial_data': {'titulo': ..., 'preco': ..., 'imagem_url': ...}
              }
        """
        url = limpar_url_rastreio(url)
        with capturar_log_extracao() as log_extracao:
            return ScraperFactory._extrair(url, log_extracao)

    @staticmethod
    def _extrair(url, log_extracao):
        try:
            scraper, is_generic = ScraperFactory.get_scraper(url)
            titulo, preco, imagem_url = scraper.extract(url)

            # Leitura incompleta (faltou título, preço ou imagem) abre issue:
            # com o scraper genérico, sugerindo suporte específico; com um
            # scraper específico, pedindo ajuste dos seletores. Leitura
            # completa não gera issue, porque não há o que melhorar.
            # (Sem título o scraper já lança ParsingError, que abre a issue de
            # falha de extração.)
            dados_faltando = [nome for nome, valor in
                              (('título', titulo), ('preço', preco), ('imagem', imagem_url)) if not valor]
            if is_generic and dados_faltando:
                try:
                    from .github_helper import criar_issue_erro_geral
                    from urllib.parse import urlparse

                    domain = urlparse(url).netloc
                    nome_classe = domain.removeprefix('www.').split('.')[0].title()
                    titulo_issue = f"[AUTO] Site não mapeado: {domain}"
                    descricao_issue = f"""## Site Não Mapeado Detectado

O **scraper genérico** extraiu os dados deste site de forma **incompleta** (faltou: {', '.join(dados_faltando)}), e o site não tem suporte específico implementado.

### Domínio
`{domain}`

### URL de Exemplo
```
{url}
```

### Dados Extraídos com Scraper Genérico
- **Título**: {titulo[:100] if titulo else 'N/A'}...
- **Preço**: R$ {preco if preco else 'N/A'}
- **Imagem**: {'Sim' if imagem_url else 'Não'}
{secao_log_extracao(log_extracao)}
### Por Que Adicionar Suporte Específico?
1. **Maior taxa de sucesso**: Scrapers específicos conhecem a estrutura exata do site
2. **Mais dados**: Podem extrair informações adicionais (descrição, avaliações, etc.)
3. **Mais confiável**: Menos propenso a falhas quando o site muda minimamente
4. **Melhor performance**: Busca direta nos elementos corretos

### Ações Sugeridas
- [ ] Analisar estrutura HTML do site `{domain}`
- [ ] Identificar padrões de classes CSS para título, preço, imagem
- [ ] Criar classe `{nome_classe}Scraper` em `scrapers.py`
- [ ] Implementar método `extract()` específico
- [ ] Adicionar ao `ScraperFactory.get_scraper()`
- [ ] Testar com múltiplas URLs do site

### Sites Populares que Merecem Suporte
Se este for um dos sites abaixo, priorize a implementação:
- Americanas
- Submarino
- Magazine Luiza
- Casas Bahia
- Shopee
- AliExpress
- Shein
- Netshoes
- Centauro

### Exemplo de Implementação
```python
class {nome_classe}Scraper(BaseScraper):
    def extract(self, url):
        soup = self.get_soup(url)

        # Título
        titulo = soup.find('h1', class_='product-title')

        # Preço
        preco = soup.find('span', class_='price')

        # Imagem
        imagem = soup.find('img', class_='product-image')

        return (titulo, preco, imagem)
```

### Informações Técnicas
- **Tipo**: Melhoria (Enhancement)
- **Prioridade**: Média (se site popular) / Baixa (se site raro)
- **Complexidade**: Baixa a Média
"""

                    criar_issue_erro_geral(
                        titulo=titulo_issue,
                        descricao=descricao_issue,
                        contexto={
                            'Domínio': domain,
                            'URL': url,
                            'Scraper usado': 'GenericScraper',
                            'Status': 'Leitura incompleta com scraper genérico',
                            'Dados faltando': ', '.join(dados_faltando),
                        },
                        labels=['auto-generated', 'enhancement', 'new-site-support', 'low-priority']
                    )

                    logger.info(f"💡 Issue criada sugerindo suporte específico para {domain}")

                except Exception as e:
                    logger.debug(f"Erro ao criar issue para site não mapeado: {str(e)}")

            elif dados_faltando and scraper.aviso:
                # Limite conhecido da loja (ex.: anuncio do ML fora do catalogo):
                # nao ha o que ajustar no codigo, entao nao abre issue. O motivo
                # vai para o log e para o admin (busca_imagem_resultado).
                logger.info(f"Leitura incompleta por limite conhecido da loja ({type(scraper).__name__}): "
                            f"{scraper.aviso}")

            elif dados_faltando:
                # Site mapeado com leitura incompleta: o site provavelmente mudou
                # o layout e o scraper específico precisa de ajuste
                try:
                    from .github_helper import criar_issue_erro_geral
                    from urllib.parse import urlparse

                    domain = urlparse(url).netloc
                    nome_scraper = type(scraper).__name__
                    criar_issue_erro_geral(
                        titulo=f"[AUTO] Leitura incompleta em site mapeado: {domain}",
                        descricao=f"""## Leitura Incompleta em Site Mapeado

O **{nome_scraper}** não conseguiu ler todos os dados do produto (faltou: {', '.join(dados_faltando)}). Provavelmente o site mudou o layout e o scraper precisa de ajuste.

### URL de Exemplo
```
{url}
```

### Dados Extraídos
- **Título**: {titulo[:100] if titulo else 'N/A'}
- **Preço**: R$ {preco if preco else 'N/A'}
- **Imagem**: {'Sim' if imagem_url else 'Não'}
{secao_log_extracao(log_extracao)}
### Ações Sugeridas
- [ ] Abrir a URL e conferir se o produto mostra {', '.join(dados_faltando)}
- [ ] Atualizar os seletores do `{nome_scraper}` em `scrapers.py`
- [ ] Testar com múltiplas URLs do site
""",
                        contexto={
                            'Domínio': domain,
                            'URL': url,
                            'Scraper usado': nome_scraper,
                            'Status': 'Leitura incompleta com scraper específico',
                            'Dados faltando': ', '.join(dados_faltando),
                        },
                        labels=['auto-generated', 'bug', 'scraping']
                    )
                    logger.info(f"🐛 Issue criada: leitura incompleta com {nome_scraper} em {domain}")
                except Exception as e:
                    logger.debug(f"Erro ao criar issue de leitura incompleta: {str(e)}")

            return {
                'success': True,
                'titulo': titulo,
                'preco': preco,
                'imagem_url': imagem_url,
                'used_generic_scraper': is_generic,
                'aviso': scraper.aviso,
            }

        except BlockedError as e:
            # Site bloqueou a consulta (pagina anti-robo)
            # NAO deve gerar issue no GitHub: nao ha o que corrigir no parser
            logger.warning(f"Acesso bloqueado ao extrair {url}: {str(e)}")
            return {
                'success': False,
                'error_type': 'blocked',
                'error_message': str(e)
            }

        except NetworkError as e:
            # Erro de rede/HTTP (404, 500, timeout, etc.)
            # NAO deve gerar issue no GitHub
            logger.warning(f"Erro de rede ao extrair {url}: {str(e)}")
            return {
                'success': False,
                'error_type': 'network',
                'error_message': str(e)
            }

        except ParsingError as e:
            # Erro de parsing (site acessivel mas dados nao extraidos)
            # DEVE gerar issue no GitHub
            logger.warning("=" * 80)
            logger.warning(f"⚠️  ERRO DE PARSING ao extrair dados de: {url}")
            logger.warning(f"   Erro: {str(e)}")
            logger.warning(f"   ")
            logger.warning(f"   ℹ️  Tentando criar issue no GitHub automaticamente...")
            logger.warning("=" * 80)

            # Tentar extrair dados parciais da mensagem de erro (se houver)
            # Formato da mensagem: "Nao foi possivel extrair titulo. Dados parciais: preco=123.45, imagem=True"
            partial_data = {'titulo': None, 'preco': None, 'imagem_url': None}

            # Tentar criar issue no GitHub
            try:
                from .github_helper import criar_issue_falha_scraping

                issue_result = criar_issue_falha_scraping(
                    url_produto=url,
                    dados_extraidos=partial_data,
                    usuario=None,  # Usuario nao disponivel neste contexto
                    grupo=None,
                    erro=str(e),
                    log_extracao=list(log_extracao),
                )

                if issue_result and issue_result.get('success'):
                    logger.info(f"✅ Issue #{issue_result['issue_number']} criada: {issue_result['issue_url']}")
                else:
                    logger.warning(f"⚠️  Falha ao criar issue: {issue_result.get('error') if issue_result else 'N/A'}")

            except Exception as issue_error:
                logger.error(f"❌ Erro ao tentar criar issue no GitHub: {str(issue_error)}")

            return {
                'success': False,
                'error_type': 'parsing',
                'error_message': str(e),
                'partial_data': partial_data,
                'log_extracao': list(log_extracao),
            }

        except Exception as e:
            # Outros erros inesperados
            logger.error(f"Erro inesperado ao extrair {url}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())

            return {
                'success': False,
                'error_type': 'unknown',
                'error_message': str(e)
            }
