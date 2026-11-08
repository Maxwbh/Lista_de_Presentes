import anthropic
import openai
import requests
import json
import logging
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
from django.conf import settings
from .models import SugestaoCompra
from .precos import converter_preco, converter_preco_decimal
from .relevancia import resultado_relevante

logger = logging.getLogger(__name__)

class IAService:
    # Headers para simular navegador
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }

    @staticmethod
    def buscar_preco_zoom(query, max_results=5):
        """Busca preços no site Zoom"""
        try:
            # URL do Zoom com busca
            url = f"https://www.zoom.com.br/search?q={quote_plus(query)}"
            logger.info(f"Buscando no Zoom: {url}")

            response = requests.get(url, headers=IAService.HEADERS, timeout=10)
            response.raise_for_status()

            # Log do status e tamanho da resposta
            logger.info(f"Zoom: Status {response.status_code}, Tamanho: {len(response.content)} bytes")

            soup = BeautifulSoup(response.content, 'html.parser')
            produtos = []

            # Tentar múltiplos seletores (a estrutura pode mudar)
            cards = (
                soup.find_all('div', {'data-testid': 'product-card'}) or
                soup.find_all('div', class_=lambda x: x and 'product-card' in x.lower() if x else False) or
                soup.find_all('article', class_=lambda x: x and 'product' in x.lower() if x else False) or
                soup.find_all('div', class_=lambda x: x and 'card' in x.lower() if x else False)
            )

            logger.info(f"Zoom: Encontrados {len(cards)} cards no HTML")

            # Se não encontrou cards, log debug
            if len(cards) == 0:
                logger.warning("Zoom: Nenhum card encontrado, salvando HTML para debug...")
                logger.debug(f"Zoom HTML (primeiros 1000 chars): {str(soup)[:1000]}")

            for i, card in enumerate(cards[:max_results]):
                try:
                    logger.debug(f"Processando card {i+1} do Zoom")

                    # Extrair nome da loja (múltiplos seletores)
                    # No HTML real: <p>Menor preço via Amazon</p>
                    loja_elem = (
                        card.find(attrs={'data-testid': 'product-card::store-name'}) or
                        card.find(class_=lambda x: x and 'BestOfferMerchant' in x if x else False) or
                        card.find(class_=lambda x: x and 'store' in x.lower() if x else False) or
                        card.find(class_=lambda x: x and 'seller' in x.lower() if x else False)
                    )

                    if loja_elem:
                        loja_text = loja_elem.text.strip()
                        # Extrair nome da loja de textos como "Menor preço via Amazon"
                        if 'via' in loja_text.lower():
                            loja = loja_text.split('via')[-1].strip()
                        elif 'por' in loja_text.lower():
                            loja = loja_text.split('por')[-1].strip()
                        else:
                            loja = loja_text
                    else:
                        loja = "Zoom"

                    logger.debug(f"Zoom: Loja encontrada: {loja}")

                    # Extrair o titulo do produto. Sem ele nao da para saber
                    # se o card e mesmo o produto procurado - a pagina de
                    # resultados tambem traz recomendacoes e produtos soltos.
                    titulo_elem = (
                        card.find(attrs={'data-testid': 'product-card::name'}) or
                        card.find('h2') or
                        card.find('h3') or
                        card.find(class_=lambda x: x and 'name' in x.lower() if x else False)
                    )
                    titulo = titulo_elem.text.strip() if titulo_elem else ''
                    logger.debug(f"Zoom: Titulo encontrado: {titulo}")

                    # Extrair preço (múltiplos seletores)
                    # No HTML real: <strong data-testid="product-card::price">R$ 4.749,00</strong>
                    preco_elem = (
                        card.find(attrs={'data-testid': 'product-card::price'}) or
                        card.find('strong', class_=lambda x: x and 'price' in x.lower() if x else False) or
                        card.find('p', class_=lambda x: x and 'price' in x.lower() if x else False) or
                        card.find('span', class_=lambda x: x and 'price' in x.lower() if x else False)
                    )

                    if preco_elem:
                        preco_text = preco_elem.text.strip()
                        logger.debug(f"Zoom: Preço encontrado: {preco_text}")
                        # Remover "R$" e converter para float
                        preco = converter_preco(preco_text)
                        if preco is None:
                            logger.warning(f"Zoom: Não foi possível converter preço: {preco_text}")
                            continue
                    else:
                        logger.debug("Zoom: Preço não encontrado no card")
                        continue

                    # Extrair URL
                    # No HTML real: <a data-testid="product-card::card" href="/celular/...">
                    link_elem = (
                        card.find('a', attrs={'data-testid': 'product-card::card'}) or
                        card.find('a', attrs={'data-testid': 'product-card::product'}) or
                        card.find('a', href=True)
                    )

                    if link_elem and link_elem.get('href'):
                        href = link_elem.get('href')
                        url_produto = f"https://www.zoom.com.br{href}" if not href.startswith('http') else href
                    else:
                        url_produto = url  # URL de busca como fallback

                    produtos.append({
                        'loja': loja,
                        'titulo': titulo,
                        'preco': preco,
                        'url': url_produto,
                        'fonte': 'Zoom'
                    })
                    logger.info(f"Zoom: Produto adicionado - {loja}: R$ {preco}")

                except Exception as e:
                    logger.warning(f"Erro ao processar produto {i+1} do Zoom: {str(e)}")
                    import traceback
                    logger.debug(f"Traceback: {traceback.format_exc()}")
                    continue

            logger.info(f"Zoom: Total de {len(produtos)} produtos válidos encontrados")
            return produtos

        except Exception as e:
            logger.error(f"Erro ao buscar no Zoom: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return []

    @staticmethod
    def buscar_preco_buscape(query, max_results=5):
        """Busca preços no site Buscapé"""
        try:
            # URL do Buscapé com busca
            url = f"https://www.buscape.com.br/search?q={quote_plus(query)}"
            logger.info(f"Buscando no Buscapé: {url}")

            response = requests.get(url, headers=IAService.HEADERS, timeout=10)
            response.raise_for_status()

            # Log do status e tamanho da resposta
            logger.info(f"Buscapé: Status {response.status_code}, Tamanho: {len(response.content)} bytes")

            soup = BeautifulSoup(response.content, 'html.parser')
            produtos = []

            # Buscapé usa a mesma estrutura que Zoom (data-testid)
            # Primeiro tentar encontrar pelo link <a data-testid="product-card::card">
            cards = (
                soup.find_all('a', attrs={'data-testid': 'product-card::card'}) or
                soup.find_all('div', {'data-testid': 'product-card'}) or
                soup.find_all('div', class_=lambda x: x and 'ProductCard' in x if x else False) or
                soup.find_all('article', class_=lambda x: x and 'product' in x.lower() if x else False)
            )

            logger.info(f"Buscapé: Encontrados {len(cards)} cards no HTML")

            # Se não encontrou cards, log debug
            if len(cards) == 0:
                logger.warning("Buscapé: Nenhum card encontrado, salvando HTML para debug...")
                logger.debug(f"Buscapé HTML (primeiros 1000 chars): {str(soup)[:1000]}")

            for i, card in enumerate(cards[:max_results]):
                try:
                    logger.debug(f"Processando card {i+1} do Buscapé")

                    # Extrair nome da loja
                    # Real HTML: <p class="BestOfferMerchant_ProductCard_BestOfferMerchant__KI8oj">Menor preço via Amazon</p>
                    loja_elem = (
                        card.find(attrs={'data-testid': 'product-card::store-name'}) or
                        card.find(class_=lambda x: x and 'BestOfferMerchant' in x if x else False) or
                        card.find(class_=lambda x: x and 'store' in x.lower() if x else False) or
                        card.find(class_=lambda x: x and 'merchant' in x.lower() if x else False)
                    )

                    if loja_elem:
                        loja_text = loja_elem.text.strip()
                        # Extrair nome da loja de textos como "Menor preço via Amazon"
                        if 'via' in loja_text.lower():
                            loja = loja_text.split('via')[-1].strip()
                        elif 'por' in loja_text.lower():
                            loja = loja_text.split('por')[-1].strip()
                        elif ':' in loja_text:
                            loja = loja_text.split(':')[-1].strip()
                        else:
                            loja = loja_text
                    else:
                        loja = "Buscapé"

                    logger.debug(f"Buscapé: Loja encontrada: {loja}")

                    # Extrair o titulo do produto - sem ele nao da para
                    # conferir se o card e mesmo o produto procurado
                    titulo_elem = (
                        card.find(attrs={'data-testid': 'product-card::name'}) or
                        card.find('h2') or
                        card.find('h3') or
                        card.find(class_=lambda x: x and 'name' in x.lower() if x else False)
                    )
                    titulo = titulo_elem.text.strip() if titulo_elem else ''
                    logger.debug(f"Buscapé: Titulo encontrado: {titulo}")

                    # Extrair preço
                    # Real HTML: <strong data-testid="product-card::price">R$ 4.749,00</strong>
                    preco_elem = (
                        card.find(attrs={'data-testid': 'product-card::price'}) or
                        card.find('strong', class_=lambda x: x and 'price' in x.lower() if x else False) or
                        card.find('p', class_=lambda x: x and 'price' in x.lower() if x else False)
                    )

                    if preco_elem:
                        preco_text = preco_elem.text.strip()
                        logger.debug(f"Buscapé: Preço encontrado: {preco_text}")
                        # Remover "R$" e converter para float
                        preco = converter_preco(preco_text)
                        if preco is None:
                            logger.warning(f"Buscapé: Não foi possível converter preço: {preco_text}")
                            continue
                    else:
                        logger.debug("Buscapé: Preço não encontrado no card")
                        continue

                    # Extrair URL
                    # Real HTML: <a data-testid="product-card::card" href="/celular/...">
                    # Se o card já é o link <a>, usar ele mesmo
                    if card.name == 'a' and card.get('href'):
                        href = card.get('href')
                        url_produto = f"https://www.buscape.com.br{href}" if not href.startswith('http') else href
                    else:
                        # Se não, procurar link dentro do card
                        link_elem = (
                            card.find('a', attrs={'data-testid': 'product-card::card'}) or
                            card.find('a', href=True)
                        )
                        if link_elem and link_elem.get('href'):
                            href = link_elem.get('href')
                            url_produto = f"https://www.buscape.com.br{href}" if not href.startswith('http') else href
                        else:
                            url_produto = url  # URL de busca como fallback

                    produtos.append({
                        'loja': loja,
                        'titulo': titulo,
                        'preco': preco,
                        'url': url_produto,
                        'fonte': 'Buscapé'
                    })
                    logger.info(f"Buscapé: Produto adicionado - {loja}: R$ {preco}")

                except Exception as e:
                    logger.warning(f"Erro ao processar produto {i+1} do Buscapé: {str(e)}")
                    import traceback
                    logger.debug(f"Traceback: {traceback.format_exc()}")
                    continue

            logger.info(f"Buscapé: Total de {len(produtos)} produtos válidos encontrados")
            return produtos

        except Exception as e:
            logger.error(f"Erro ao buscar no Buscapé: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return []

    @staticmethod
    def buscar_sugestoes_reais(presente):
        """Busca sugestões combinando IA + Zoom + Buscapé"""
        try:
            # Le o site do link do presente: completa o que falta (foto, preco,
            # descricao generica) e traz o preco atual da loja para a comparacao
            oferta_link = IAService._oferta_do_link(presente)

            query = presente.descricao
            todos_produtos = []
            if IAService.descricao_generica(query):
                # Buscar 'Pronta Entrega!' trazia produtos sem relacao (ex.: barbeador)
                logger.warning(f"Descrição genérica, sem busca em outras lojas: '{query}'")
                return IAService._gravar_sugestoes(presente, [], oferta_link, (
                    "A descrição do presente é genérica. Edite o presente com o nome do produto "
                    "para comparar preços em outras lojas."
                ))
            logger.info(f"Buscando preços com IA + Zoom + Buscapé para: {query}")

            # 1. Buscar com IA Gemini (free tier - principal)
            try:
                logger.info("Tentando buscar com IA Gemini...")
                sucesso_ia, mensagem_ia = IAService.buscar_sugestoes_gemini(presente)
                if sucesso_ia:
                    logger.info(f"IA Gemini: {mensagem_ia}")
                    # IA já salvou as sugestões, vamos pegá-las
                    sugestoes_ia = SugestaoCompra.objects.filter(presente=presente)
                    for sug in sugestoes_ia:
                        todos_produtos.append({
                            'loja': sug.local_compra,
                            'preco': float(sug.preco_sugerido) if sug.preco_sugerido else 0.0,
                            'url': sug.url_compra or '',
                            'fonte': 'IA'
                        })
                    logger.info(f"Adicionados {len(sugestoes_ia)} produtos da IA")
                else:
                    logger.warning(f"IA Gemini não retornou sugestões: {mensagem_ia}")
            except Exception as e:
                logger.error(f"Erro ao buscar com IA Gemini: {str(e)}")

            # 2. Buscar no Zoom
            try:
                logger.info("Tentando buscar no Zoom...")
                produtos_zoom = IAService.buscar_preco_zoom(query, max_results=3)
                if produtos_zoom:
                    todos_produtos.extend(produtos_zoom)
                    logger.info(f"Adicionados {len(produtos_zoom)} produtos do Zoom")
            except Exception as e:
                logger.error(f"Erro ao buscar no Zoom: {str(e)}")

            # 3. Buscar no Buscapé
            try:
                logger.info("Tentando buscar no Buscapé...")
                produtos_buscape = IAService.buscar_preco_buscape(query, max_results=3)
                if produtos_buscape:
                    todos_produtos.extend(produtos_buscape)
                    logger.info(f"Adicionados {len(produtos_buscape)} produtos do Buscapé")
            except Exception as e:
                logger.error(f"Erro ao buscar no Buscapé: {str(e)}")

            if not todos_produtos:
                logger.warning("Nenhum produto encontrado em nenhuma fonte")
                return IAService._gravar_sugestoes(presente, [], oferta_link,
                                                   "Não foram encontrados produtos nas fontes de busca.")

            # Descartar o que nao e o produto procurado. A pagina de resultados
            # dos buscadores tambem traz recomendacoes e produtos soltos, e sem
            # essa conferencia um item de R$ 28 acabava com "melhor oferta" de
            # R$ 219 de um produto sem nenhuma relacao - preco que ainda entrava
            # no historico e estourava a temperatura do card.
            relevantes = []
            for produto in todos_produtos:
                if resultado_relevante(query, produto.get('titulo', '')):
                    relevantes.append(produto)
                else:
                    logger.info(
                        "Descartado por nao corresponder ao presente "
                        f"'{query}': titulo='{produto.get('titulo', '')}' "
                        f"loja='{produto.get('loja', '')}' fonte={produto.get('fonte', '')}"
                    )

            if not relevantes:
                logger.warning(f"Nenhum resultado correspondeu ao presente: {query}")
                return IAService._gravar_sugestoes(presente, [], oferta_link, (
                    "Nenhum resultado da busca corresponde a este presente. "
                    "Tente uma descrição mais específica."
                ))

            todos_produtos = relevantes

            # Ordenar por preço (menor primeiro), ignorando preços zerados
            todos_produtos_com_preco = [p for p in todos_produtos if p.get('preco', 0) > 0]
            if todos_produtos_com_preco:
                todos_produtos_com_preco.sort(key=lambda x: x['preco'])

                # Descartar outliers: preços muito fora da mediana costumam ser
                # produto errado no resultado do scraper (acessório ou kit)
                precos = [p['preco'] for p in todos_produtos_com_preco]
                mediana = precos[len(precos) // 2]
                todos_produtos_com_preco = [
                    p for p in todos_produtos_com_preco
                    if mediana * 0.35 <= p['preco'] <= mediana * 2.5
                ]

                # Pegar os melhores preços primeiro, depois os sem preço
                todos_produtos_sem_preco = [p for p in todos_produtos if p.get('preco', 0) == 0]
                todos_produtos = todos_produtos_com_preco + todos_produtos_sem_preco

            return IAService._gravar_sugestoes(presente, todos_produtos, oferta_link,
                                               "Não foram encontrados produtos nas fontes de busca.")

        except Exception as e:
            logger.error(f"Erro ao buscar sugestões: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False, f"Erro ao buscar preços: {str(e)}"

    LOJAS_CONHECIDAS = {
        'mercadolivre': 'Mercado Livre', 'mercadolibre': 'Mercado Livre', 'meli': 'Mercado Livre',
        'amazon': 'Amazon', 'amzn': 'Amazon', 'magazineluiza': 'Magazine Luiza', 'magalu': 'Magazine Luiza',
        'kabum': 'KaBuM!', 'decathlon': 'Decathlon', 'shopee': 'Shopee', 'americanas': 'Americanas',
        'casasbahia': 'Casas Bahia', 'pontofrio': 'Ponto', 'aliexpress': 'AliExpress', 'shein': 'Shein',
        'netshoes': 'Netshoes', 'centauro': 'Centauro', 'submarino': 'Submarino',
    }

    @staticmethod
    def nome_loja_do_link(url):
        """Nome da loja a partir do dominio (ex.: www.mercadolivre.com.br -> 'Mercado Livre')"""
        from urllib.parse import urlparse
        dominio = urlparse(url or '').netloc.lower().split(':')[0]
        partes = [p for p in dominio.split('.') if p not in ('www', 'm', 'produto', 'lista', 'loja')]
        for parte in partes:
            if parte in IAService.LOJAS_CONHECIDAS:
                return IAService.LOJAS_CONHECIDAS[parte]
        return partes[0].capitalize() if partes else 'Loja do link'

    @staticmethod
    def _oferta_do_link(presente):
        """
        Le o site do link do presente: completa o que falta no presente e
        devolve a oferta da propria loja ({'loja', 'url', 'preco', 'titulo'})
        com o preco atual do site (ou o preco cadastrado), ou None.
        """
        if not presente.url:
            return None
        from .scrapers import ScraperFactory
        try:
            leitura = ScraperFactory.extract_product_info(presente.url) or {}
        except Exception as e:
            logger.warning(f"Falha ao ler o link do presente {presente.id}: {e}")
            leitura = {}
        IAService.completar_pelo_site(presente, leitura=leitura)
        preco = converter_preco_decimal(leitura.get('preco')) if leitura.get('success') else None
        preco = preco or presente.preco
        if not preco:
            return None
        return {
            'loja': IAService.nome_loja_do_link(presente.url),
            'url': presente.url,
            'preco': float(preco),
            'titulo': (leitura.get('titulo') or presente.descricao or '')[:300],
        }

    @staticmethod
    def _gravar_sugestoes(presente, produtos, oferta_link, mensagem_vazia):
        """
        Substitui as sugestoes do presente: a loja do link do presente (sempre,
        com o preco atual) e ate 10 lojas encontradas, uma por loja, a mais barata.
        """
        if not produtos and not oferta_link:
            return False, mensagem_vazia

        SugestaoCompra.objects.filter(presente=presente).delete()
        lojas_salvas = set()
        sugestoes_salvas = 0
        if oferta_link:
            produtos = [oferta_link] + list(produtos)
        for produto in produtos:
            if sugestoes_salvas >= 10:
                break
            loja_nome = IAService._limpar_nome_loja(produto.get('loja', ''))
            url = (produto.get('url') or '').strip()
            preco = converter_preco_decimal(produto.get('preco'))
            if not loja_nome or not url:
                logger.warning(f"Ignorando sugestão sem loja ou URL: {produto}")
                continue
            # Uma por loja: a do link do presente vem primeiro; nas demais, a
            # lista ja esta ordenada por preco
            if loja_nome.lower() in lojas_salvas:
                continue
            lojas_salvas.add(loja_nome.lower())
            logger.info(f"Salvando sugestão: loja='{loja_nome}', url='{url}', preco={preco}")
            SugestaoCompra.objects.create(
                grupo=presente.grupo,
                presente=presente,
                local_compra=loja_nome,
                titulo_produto=(produto.get('titulo') or '')[:300],
                url_compra=url,
                preco_sugerido=preco,
            )
            sugestoes_salvas += 1

        IAService._registrar_historico(presente)
        outras = sugestoes_salvas - (1 if oferta_link else 0)
        if outras <= 0:
            return True, f"Só a loja do link do presente. {mensagem_vazia}"
        return True, f"Encontradas {sugestoes_salvas} sugestões (loja do link + IA, Zoom e Buscapé)!"

    @staticmethod
    def buscar_sugestoes_claude(presente):
        """Busca sugestões usando Claude AI"""
        try:
            client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        except TypeError as e:
            logger.error(f"Erro ao inicializar cliente Anthropic: {str(e)}")
            # Tentar com configuração básica sem argumentos extras
            try:
                import os
                os.environ['ANTHROPIC_API_KEY'] = settings.ANTHROPIC_API_KEY
                client = anthropic.Anthropic()
            except Exception as e2:
                logger.error(f"Erro ao inicializar cliente Anthropic (tentativa 2): {str(e2)}")
                return False, f"Erro ao configurar o motor de busca: {str(e2)}"
        
        prompt = f"""
        Encontre 5 lojas online no Brasil que vendem o seguinte produto: {presente.descricao}
        Preço estimado: R$ {presente.preco if presente.preco else 'Não informado'}
        
        Retorne APENAS um JSON válido no seguinte formato:
        {{
            "sugestoes": [
                {{
                    "loja": "Nome da Loja",
                    "produto": "Titulo do produto na loja",
                    "url": "https://www.loja.com.br/produto",
                    "preco": 199.90
                }}
            ]
        }}

        Busque por lojas reais e conhecidas como Amazon, Mercado Livre, Magazine Luiza, Americanas, etc.
        O campo "produto" deve trazer o titulo do anuncio na loja, exatamente como aparece la.
        Nao sugira acessorios nem produtos parecidos: se nao encontrar o produto exato, devolva a lista vazia.
        """
        
        try:
            # Haiku 4.5: modelo atual mais barato ($1/$5 por MTok) — suficiente
            # para extração JSON simples. O anterior (claude-sonnet-4-20250514)
            # foi descontinuado e aposenta em 15/06/2026.
            modelo = getattr(settings, 'ANTHROPIC_MODEL', 'claude-haiku-4-5')
            message = client.messages.create(
                model=modelo,
                max_tokens=1024,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            resposta = message.content[0].text
            # Limpar markdown se existir
            resposta = resposta.replace('```json', '').replace('```', '').strip()
            dados = json.loads(resposta)
            
            # Salvar sugestões
            IAService._salvar_sugestoes(presente, dados['sugestoes'])
            return True, "Sugestões encontradas com sucesso!"
            
        except Exception as e:
            return False, f"Erro ao buscar sugestões: {str(e)}"
    
    @staticmethod
    def buscar_sugestoes_chatgpt(presente):
        """Busca sugestões usando ChatGPT"""
        openai.api_key = settings.OPENAI_API_KEY
        
        prompt = f"""
        Encontre 5 lojas online no Brasil que vendem: {presente.descricao}
        Preço estimado: R$ {presente.preco if presente.preco else 'Não informado'}
        
        Retorne em formato JSON:
        {{
            "sugestoes": [
                {{"loja": "Nome", "produto": "Titulo do produto na loja", "url": "URL", "preco": 199.90}}
            ]
        }}

        O campo "produto" deve trazer o titulo do anuncio na loja, exatamente como aparece la.
        Nao sugira acessorios nem produtos parecidos: se nao encontrar o produto exato, devolva a lista vazia.
        """
        
        try:
            modelo = getattr(settings, 'OPENAI_MODEL', 'gpt-4o-mini')
            response = openai.chat.completions.create(
                model=modelo,
                messages=[
                    {"role": "system", "content": "Você é um assistente que busca produtos em lojas brasileiras."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            resposta = response.choices[0].message.content
            resposta = resposta.replace('```json', '').replace('```', '').strip()
            dados = json.loads(resposta)
            
            IAService._salvar_sugestoes(presente, dados['sugestoes'])
            return True, "Sugestões encontradas com sucesso!"
            
        except Exception as e:
            return False, f"Erro ao buscar sugestões: {str(e)}"
    
    @staticmethod
    def buscar_sugestoes_gemini(presente):
        """Busca sugestões usando Google Gemini (free tier - gemini-2.5-flash)"""
        if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == 'sua-chave-gemini':
            logger.warning("GEMINI_API_KEY não configurada")
            return False, "Chave da API Gemini não configurada."

        # Modelo gratuito do Gemini (free tier generoso)
        modelo = getattr(settings, 'GEMINI_MODEL', 'gemini-2.5-flash')
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{modelo}:generateContent?key={settings.GEMINI_API_KEY}"
        )

        prompt = f"""
        Encontre 5 lojas online no Brasil que vendem o seguinte produto: {presente.descricao}
        Preço estimado: R$ {presente.preco if presente.preco else 'Não informado'}

        Retorne APENAS um JSON válido (sem markdown, sem texto extra) no formato:
        {{
            "sugestoes": [
                {{"loja": "Nome da Loja", "produto": "Titulo do produto na loja", "url": "https://www.loja.com.br/produto", "preco": 199.90}}
            ]
        }}

        Busque por lojas reais e conhecidas como Amazon, Mercado Livre, Magazine Luiza, Americanas, Kabum, etc.
        O campo "produto" deve trazer o titulo do anuncio na loja, exatamente como aparece la.
        Nao sugira acessorios nem produtos parecidos: se nao encontrar o produto exato, devolva a lista vazia.
        """

        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "responseMimeType": "application/json"
            }
        }

        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            dados = response.json()

            texto = dados['candidates'][0]['content']['parts'][0]['text']
            texto = texto.replace('```json', '').replace('```', '').strip()
            sugestoes = json.loads(texto)

            IAService._salvar_sugestoes(presente, sugestoes['sugestoes'])
            return True, "Sugestões encontradas com sucesso via Gemini!"

        except requests.exceptions.RequestException as e:
            logger.error(f"Erro de rede ao buscar com Gemini: {str(e)}")
            return False, f"Erro de conexão com Gemini: {str(e)}"
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            logger.error(f"Erro ao processar resposta do Gemini: {str(e)}")
            return False, f"Resposta inválida do Gemini: {str(e)}"
        except Exception as e:
            logger.error(f"Erro ao buscar sugestões com Gemini: {str(e)}")
            return False, f"Erro ao buscar sugestões: {str(e)}"
    
    @staticmethod
    def descricao_generica(texto):
        """Descricao vazia ou so chamada de venda (ex.: 'Pronta Entrega!')"""
        import re
        from .mercadolivre_api import CHAMADA_DE_VENDA_RE
        texto = (texto or '').strip()
        if not texto:
            return True
        return bool(CHAMADA_DE_VENDA_RE.search(texto)) and len(re.findall(r'\w+', texto)) < 6

    @staticmethod
    def precisa_completar(presente):
        """Presente com link e sem foto, sem preco ou com descricao vazia/generica"""
        return bool(presente.url) and (
            not presente.tem_imagem() or presente.preco is None
            or IAService.descricao_generica(presente.descricao)
        )

    @staticmethod
    def completar_pelo_site(presente, leitura=None):
        """
        Le o site do link original e preenche o que falta no presente: foto
        (se nao tiver), preco (se vazio) e descricao (se vazia ou generica e o
        site trouxer um titulo melhor). Nao altera o que ja esta preenchido.
        Chamado na atualizacao de precos e pelo botao do admin.

        Grava em busca_imagem_resultado o que aconteceu (para o admin mostrar).
        Retorna o conjunto de campos preenchidos ('imagem', 'preco', 'descricao').
        """
        if not IAService.precisa_completar(presente):
            return set()
        from django.utils import timezone
        from .mercadolivre_api import _serve_de_titulo

        faltando = []
        if not presente.tem_imagem():
            faltando.append('imagem')
        if presente.preco is None:
            faltando.append('preco')
        if IAService.descricao_generica(presente.descricao):
            faltando.append('descricao')
        preenchidos = set()
        campos = []
        motivo = None
        motivo_imagem = None

        try:
            if leitura:
                resultado = leitura
            else:
                from .scrapers import ScraperFactory
                resultado = ScraperFactory.extract_product_info(presente.url) or {}
            dados = resultado if resultado.get('success') else (resultado.get('partial_data') or {})

            if resultado.get('success'):
                motivo = resultado.get('aviso') or 'O site não informou.'
            elif resultado.get('error_type') == 'blocked':
                motivo = 'O site bloqueou a consulta automática.'
            else:
                motivo = f"Erro ao ler o site: {resultado.get('error_message') or 'desconhecido'}"

            preco_site = converter_preco_decimal(dados.get('preco'))
            if 'preco' in faltando and preco_site:
                presente.preco = preco_site
                campos.append('preco')
                preenchidos.add('preco')

            titulo = (dados.get('titulo') or '').strip()
            if 'descricao' in faltando and titulo and _serve_de_titulo(titulo):
                presente.descricao = titulo
                campos.append('descricao')
                preenchidos.add('descricao')

            imagem_url = dados.get('imagem_url')
            if 'imagem' in faltando and imagem_url:
                motivo_imagem = IAService._baixar_foto(presente, imagem_url)
                if motivo_imagem is None:
                    campos += ['imagem_base64', 'imagem_nome', 'imagem_tipo']
                    preenchidos.add('imagem')
        except Exception as e:
            logger.warning(f"Falha ao completar o presente {presente.id} pelo site: {str(e)}")
            motivo = f'Erro ao ler o site: {e}'

        nomes = {'imagem': 'foto', 'preco': 'preço', 'descricao': 'descrição'}
        mensagens = []
        if 'imagem' in preenchidos:
            mensagens.append('Foto encontrada.')
        if 'preco' in preenchidos:
            mensagens.append('Preço preenchido.')
        if 'descricao' in preenchidos:
            mensagens.append('Descrição atualizada.')
        if 'imagem' in faltando and 'imagem' not in preenchidos and motivo_imagem:
            mensagens.append(motivo_imagem)
        sem = [nomes[c] for c in faltando if c not in preenchidos and not (c == 'imagem' and motivo_imagem)]
        if sem:
            mensagens.append(f"Sem {' e '.join(sem)}: {motivo or 'erro desconhecido'}")

        try:
            presente.busca_imagem_em = timezone.now()
            presente.busca_imagem_resultado = ' '.join(mensagens)[:300]
            presente.save(update_fields=['busca_imagem_em', 'busca_imagem_resultado', *campos])
            if 'preco' in preenchidos:
                presente.registrar_preco(presente.preco, fonte='site')
        except Exception:
            logger.exception("Falha ao registrar o resultado da busca no site")
        logger.info(f"Presente {presente.id} completado pelo site: {sorted(preenchidos) or 'nada'} "
                    f"({presente.busca_imagem_resultado})")
        return preenchidos

    @staticmethod
    def _baixar_foto(presente, imagem_url):
        """Baixa a foto para o presente (sem salvar). Retorna None ou o motivo da falha."""
        import base64
        try:
            resp = requests.get(imagem_url, headers=IAService.HEADERS, timeout=15)
            resp.raise_for_status()
        except Exception as e:
            return f'Erro ao baixar a foto: {e}'
        content_type = resp.headers.get('content-type', '').split(';')[0].strip()
        if not content_type.startswith('image/'):
            return f'O endereço da foto não devolveu uma imagem ({content_type or "sem tipo"}).'
        if len(resp.content) > 5 * 1024 * 1024:
            return 'A foto do site tem mais de 5 MB.'
        presente.imagem_base64 = base64.b64encode(resp.content).decode('utf-8')
        presente.imagem_nome = imagem_url.split('/')[-1].split('?')[0][:255] or 'produto.jpg'
        presente.imagem_tipo = content_type
        return None

    @staticmethod
    def buscar_imagem_para_presente(presente):
        """Compatibilidade: completa o presente pelo site; True se ganhou foto"""
        return 'imagem' in IAService.completar_pelo_site(presente)

    @staticmethod
    def _registrar_historico(presente, fonte='sugestao'):
        """Grava no histórico o melhor preço encontrado entre as sugestões."""
        try:
            melhor = SugestaoCompra.objects.filter(
                presente=presente,
                preco_sugerido__isnull=False
            ).order_by('preco_sugerido').first()
            if melhor and melhor.preco_sugerido:
                presente.registrar_preco(
                    melhor.preco_sugerido,
                    loja=melhor.local_compra,
                    fonte=fonte
                )
        except Exception as e:
            logger.error(f"Erro ao registrar histórico de preço do presente {presente.id}: {str(e)}")

    @staticmethod
    def buscar_sugestoes_com_fallback(presente):
        """
        Busca sugestões tentando os motores de IA em ordem de custo crescente:
        Gemini (free tier) -> ChatGPT (gpt-4o-mini) -> Claude (haiku 4.5).
        Se um motor falhar (sem crédito, chave inválida, indisponível),
        passa automaticamente para o próximo.
        """
        oferta_link = IAService._oferta_do_link(presente)
        if IAService.descricao_generica(presente.descricao):
            return IAService._gravar_sugestoes(presente, [], oferta_link, (
                "A descrição do presente é genérica. Edite o presente com o nome do produto "
                "para comparar preços em outras lojas."
            ))

        motores = [
            ('Gemini', settings.GEMINI_API_KEY, IAService.buscar_sugestoes_gemini),
            ('ChatGPT', settings.OPENAI_API_KEY, IAService.buscar_sugestoes_chatgpt),
            ('Claude', settings.ANTHROPIC_API_KEY, IAService.buscar_sugestoes_claude),
        ]

        for nome, chave, funcao in motores:
            if not chave or chave.startswith('sua-chave'):
                logger.info(f"[IA] {nome}: chave não configurada, pulando para o próximo motor")
                continue
            try:
                sucesso, mensagem = funcao(presente)
                if sucesso:
                    logger.info(f"[IA] Sugestões obtidas com {nome}")
                    IAService._incluir_oferta_link(presente, oferta_link)
                    return True, "Sugestões encontradas com sucesso!"
                logger.warning(f"[IA] {nome} não retornou sugestões: {mensagem}. Tentando próximo motor...")
            except Exception as e:
                logger.warning(f"[IA] {nome} falhou: {str(e)}. Tentando próximo motor...")

        return IAService._gravar_sugestoes(
            presente, [], oferta_link,
            "Os motores de busca estão indisponíveis no momento. Tente novamente mais tarde.")

    @staticmethod
    def _incluir_oferta_link(presente, oferta_link):
        """Poe a loja do link do presente entre as sugestoes ja gravadas (no lugar da mesma loja)"""
        if not oferta_link:
            return
        loja = IAService._limpar_nome_loja(oferta_link['loja'])
        SugestaoCompra.objects.filter(presente=presente, local_compra__iexact=loja).delete()
        SugestaoCompra.objects.create(
            grupo=presente.grupo, presente=presente, local_compra=loja,
            titulo_produto=oferta_link['titulo'], url_compra=oferta_link['url'],
            preco_sugerido=converter_preco_decimal(oferta_link['preco']),
        )
        IAService._registrar_historico(presente)

    @staticmethod
    def _limpar_nome_loja(nome):
        """
        Normaliza o nome da loja para exibição:
        'Via KaBuM! (Buscapé)' -> 'KaBuM!' | 'Zoom (Zoom)' -> 'Zoom'
        """
        import re
        nome = (nome or '').strip()
        nome = re.sub(r'^via\s+', '', nome, flags=re.IGNORECASE)
        nome = re.sub(r'\s*\([^)]*\)\s*$', '', nome).strip()
        return nome[:200]

    @staticmethod
    def _salvar_sugestoes(presente, sugestoes):
        """Salva as sugestões no banco de dados"""
        # Limpar sugestões antigas
        SugestaoCompra.objects.filter(presente=presente).delete()

        # Salvar novas sugestões (uma por loja)
        lojas_salvas = set()
        for sug in sugestoes:
            loja = IAService._limpar_nome_loja(sug.get('loja', ''))
            url = sug.get('url', '').strip()
            # A IA pode devolver o preco como texto ('R$ 1.371,60', '1371.60')
            preco = converter_preco_decimal(sug.get('preco'))
            titulo = (sug.get('produto') or sug.get('titulo') or '').strip()

            # Validar dados antes de salvar
            if not loja or not url:
                logger.warning(f"Ignorando sugestão da IA com dados vazios: {sug}")
                continue

            # A IA tambem erra o produto: sem titulo que confira com o
            # presente, a sugestao nao entra
            if not resultado_relevante(presente.descricao, titulo):
                logger.info(
                    f"Sugestão da IA descartada por não corresponder ao presente "
                    f"'{presente.descricao}': titulo='{titulo}' loja='{loja}'"
                )
                continue

            if loja.lower() in lojas_salvas:
                continue
            lojas_salvas.add(loja.lower())

            SugestaoCompra.objects.create(
                grupo=presente.grupo,
                presente=presente,
                local_compra=loja,
                titulo_produto=titulo[:300],
                url_compra=url,
                preco_sugerido=preco
            )

        IAService._registrar_historico(presente)
