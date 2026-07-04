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
        Retorna: (scraper, is_generic)
        """
        domain = urlparse(url).netloc.lower()

        if 'amazon.com' in domain:
            logger.info(f"🛍️  Usando AmazonScraper para {domain}")
            return AmazonScraper(), False
        elif 'mercadolivre.com' in domain or 'mercadolibre.com' in domain:
            logger.info(f"🛒 Usando MercadoLivreScraper para {domain}")
            return MercadoLivreScraper(), False
        elif 'kabum.com' in domain:
            logger.info(f"🎮 Usando KabumScraper para {domain}")
            return KabumScraper(), False
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
        try:
            scraper, is_generic = ScraperFactory.get_scraper(url)
            titulo, preco, imagem_url = scraper.extract(url)

            # Se usou scraper genérico e teve sucesso, criar issue sugerindo suporte específico
            if is_generic:
                try:
                    from .github_helper import criar_issue_erro_geral
                    from urllib.parse import urlparse

                    domain = urlparse(url).netloc
                    titulo_issue = f"[AUTO] Site não mapeado: {domain}"
                    descricao_issue = f"""## Site Não Mapeado Detectado

O sistema conseguiu extrair dados usando o **scraper genérico**, mas este site não tem suporte específico implementado.

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

### Por Que Adicionar Suporte Específico?
1. **Maior taxa de sucesso**: Scrapers específicos conhecem a estrutura exata do site
2. **Mais dados**: Podem extrair informações adicionais (descrição, avaliações, etc.)
3. **Mais confiável**: Menos propenso a falhas quando o site muda minimamente
4. **Melhor performance**: Busca direta nos elementos corretos

### Ações Sugeridas
- [ ] Analisar estrutura HTML do site `{domain}`
- [ ] Identificar padrões de classes CSS para título, preço, imagem
- [ ] Criar classe `{domain.split('.')[0].title()}Scraper` em `scrapers.py`
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
class {domain.split('.')[0].title()}Scraper(BaseScraper):
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
                            'Status': 'Sucesso com scraper genérico'
                        },
                        labels=['auto-generated', 'enhancement', 'new-site-support', 'low-priority']
                    )

                    logger.info(f"💡 Issue criada sugerindo suporte específico para {domain}")

                except Exception as e:
                    logger.debug(f"Erro ao criar issue para site não mapeado: {str(e)}")

            return {
                'success': True,
                'titulo': titulo,
                'preco': preco,
                'imagem_url': imagem_url,
                'used_generic_scraper': is_generic
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
                    grupo=None
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
