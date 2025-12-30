"""
Scrapers específicos para diferentes lojas online.
Cada loja tem sua própria lógica de extração otimizada.
"""
import requests
from bs4 import BeautifulSoup
import re
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class ScrapingError(Exception):
    """Excecao base para erros de scraping"""
    pass


class NetworkError(ScrapingError):
    """Erro de rede/HTTP (timeout, 404, 500, etc.) - NAO gera issue"""
    pass


class ParsingError(ScrapingError):
    """Erro de parsing/extracao de dados (site acessivel mas dados nao extraidos) - GERA issue"""
    pass


class BaseScraper:
    """Classe base para scrapers de lojas"""

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        }

    def get_soup(self, url, timeout=10):
        """
        Obtém BeautifulSoup de uma URL.

        Lanca NetworkError para erros HTTP/rede (404, 500, timeout, etc.)
        Retorna BeautifulSoup se sucesso.
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=timeout)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
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

    def clean_price(self, price_str):
        """Limpa e converte string de preço para float"""
        if not price_str:
            return None

        # Remove tudo exceto números, vírgula e ponto
        price_str = re.sub(r'[^\d,.]', '', price_str)

        # Substitui vírgula por ponto
        price_str = price_str.replace('.', '').replace(',', '.')

        try:
            return float(price_str)
        except:
            return None

    def extract(self, url):
        """Método a ser implementado por subclasses"""
        raise NotImplementedError


class AmazonScraper(BaseScraper):
    """Scraper específico para Amazon Brasil"""

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

        # Título - Amazon tem IDs específicos
        title_candidates = [
            soup.find('span', id='productTitle'),
            soup.find('h1', class_='a-size-large'),
        ]

        for candidate in title_candidates:
            if candidate:
                titulo = candidate.get_text(strip=True)
                break

        # Preço - Amazon tem várias possibilidades
        price_candidates = [
            # Preço principal
            soup.find('span', class_='a-price-whole'),
            # Preço de oferta
            soup.find('span', class_='a-offscreen'),
            # Preço no deal
            soup.find('span', class_='priceBlockBuyingPriceString'),
        ]

        for candidate in price_candidates:
            if candidate:
                price_text = candidate.get_text(strip=True)
                preco = self.clean_price(price_text)
                if preco:
                    break

        # Imagem - Amazon tem imgTagWrapper
        img_candidates = [
            soup.find('img', id='landingImage'),
            soup.find('img', class_='a-dynamic-image'),
            soup.find('div', id='imgTagWrapperId'),
        ]

        for candidate in img_candidates:
            if candidate:
                if candidate.name == 'img':
                    imagem_url = candidate.get('src') or candidate.get('data-old-hires')
                else:
                    img = candidate.find('img')
                    if img:
                        imagem_url = img.get('src') or img.get('data-old-hires')

                if imagem_url:
                    break

        # Log do resultado
        logger.info(f"Amazon - Título: {bool(titulo)}, Preço: {preco}, Imagem: {bool(imagem_url)}")

        # Se nao conseguiu extrair NENHUM titulo, lancar ParsingError
        if not titulo:
            raise ParsingError(f"Nao foi possivel extrair titulo da Amazon. Dados parciais: preco={preco}, imagem={bool(imagem_url)}")

        return (titulo, preco, imagem_url)


class MercadoLivreScraper(BaseScraper):
    """Scraper específico para Mercado Livre"""

    def extract(self, url):
        """
        Extrai informações de produtos do Mercado Livre.
        Retorna: (titulo, preco, imagem_url)
        Lanca NetworkError para erros de rede/HTTP.
        Lanca ParsingError se conseguir acessar mas nao extrair dados minimos.
        """
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
                    price_text = candidate.get('content', '')
                else:
                    price_text = candidate.get_text(strip=True)

                preco = self.clean_price(price_text)
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

        price_meta = soup.find('meta', property='product:price:amount') or soup.find('meta', attrs={'itemprop': 'price'})
        if price_meta and price_meta.get('content'):
            preco = self.clean_price(price_meta.get('content'))

        if not preco:
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
        """
        domain = urlparse(url).netloc.lower()

        if 'amazon.com' in domain:
            logger.info(f"Usando AmazonScraper para {domain}")
            return AmazonScraper()
        elif 'mercadolivre.com' in domain or 'mercadolibre.com' in domain:
            logger.info(f"Usando MercadoLivreScraper para {domain}")
            return MercadoLivreScraper()
        elif 'kabum.com' in domain:
            logger.info(f"Usando KabumScraper para {domain}")
            return KabumScraper()
        else:
            logger.info(f"Usando GenericScraper para {domain}")
            return GenericScraper()

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
        try:
            scraper = ScraperFactory.get_scraper(url)
            titulo, preco, imagem_url = scraper.extract(url)

            return {
                'success': True,
                'titulo': titulo,
                'preco': preco,
                'imagem_url': imagem_url
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
            logger.warning(f"Erro de parsing ao extrair {url}: {str(e)}")

            # Tentar extrair dados parciais da mensagem de erro (se houver)
            # Formato da mensagem: "Nao foi possivel extrair titulo. Dados parciais: preco=123.45, imagem=True"
            partial_data = {'titulo': None, 'preco': None, 'imagem_url': None}

            return {
                'success': False,
                'error_type': 'parsing',
                'error_message': str(e),
                'partial_data': partial_data
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
