import anthropic
import openai
import requests
import json
import logging
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
from django.conf import settings
from .models import SugestaoCompra

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
                        preco_text = preco_text.replace('R$', '').replace('.', '').replace(',', '.').strip()
                        try:
                            preco = float(preco_text)
                        except ValueError:
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
                        preco_text = preco_text.replace('R$', '').replace('.', '').replace(',', '.').strip()
                        # Remover espaços e outros caracteres não numéricos
                        preco_text = ''.join(c for c in preco_text if c.isdigit() or c == '.')
                        try:
                            preco = float(preco_text)
                        except ValueError:
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
            query = presente.descricao
            logger.info(f"Buscando preços com IA + Zoom + Buscapé para: {query}")

            todos_produtos = []

            # 1. Buscar com IA Claude (mais confiável)
            try:
                logger.info("Tentando buscar com IA Claude...")
                sucesso_ia, mensagem_ia = IAService.buscar_sugestoes_claude(presente)
                if sucesso_ia:
                    logger.info(f"IA Claude: {mensagem_ia}")
                    # IA já salvou as sugestões, vamos pegá-las
                    sugestoes_ia = SugestaoCompra.objects.filter(presente=presente)
                    for sug in sugestoes_ia:
                        todos_produtos.append({
                            'loja': sug.local_compra,
                            'preco': float(sug.preco_sugerido) if sug.preco_sugerido else 0.0,
                            'url': sug.url_compra or '',
                            'fonte': 'IA Claude'
                        })
                    logger.info(f"Adicionados {len(sugestoes_ia)} produtos da IA")
            except Exception as e:
                logger.error(f"Erro ao buscar com IA: {str(e)}")

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
                return False, "Não foram encontrados produtos nas fontes de busca."

            # Ordenar por preço (menor primeiro), ignorando preços zerados
            todos_produtos_com_preco = [p for p in todos_produtos if p.get('preco', 0) > 0]
            if todos_produtos_com_preco:
                todos_produtos_com_preco.sort(key=lambda x: x['preco'])
                # Pegar os melhores preços primeiro, depois os sem preço
                todos_produtos_sem_preco = [p for p in todos_produtos if p.get('preco', 0) == 0]
                todos_produtos = todos_produtos_com_preco + todos_produtos_sem_preco

            # Limpar sugestões antigas e salvar novas (se não foram salvas pela IA)
            SugestaoCompra.objects.filter(presente=presente).delete()

            # Salvar até 10 melhores sugestões
            sugestoes_salvas = 0
            for produto in todos_produtos[:10]:
                loja_nome = produto.get('loja', '').strip()
                loja_fonte = produto.get('fonte', '').strip()
                url = produto.get('url', '').strip()
                preco = produto.get('preco') if produto.get('preco', 0) > 0 else None

                # Validar dados antes de salvar
                if not loja_nome:
                    logger.warning(f"Ignorando sugestão sem nome de loja: {produto}")
                    continue

                if not url:
                    logger.warning(f"Ignorando sugestão sem URL: {produto}")
                    continue

                # Formatar nome da loja com fonte
                loja_completo = f"{loja_nome} ({loja_fonte})" if loja_fonte else loja_nome

                logger.info(f"Salvando sugestão: loja='{loja_completo}', url='{url}', preco={preco}")

                SugestaoCompra.objects.create(
                    presente=presente,
                    local_compra=loja_completo,
                    url_compra=url,
                    preco_sugerido=preco
                )
                sugestoes_salvas += 1

            return True, f"Encontradas {sugestoes_salvas} sugestões válidas de IA + Zoom + Buscapé!"

        except Exception as e:
            logger.error(f"Erro ao buscar sugestões: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False, f"Erro ao buscar preços: {str(e)}"

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
                return False, f"Erro ao configurar IA Claude: {str(e2)}"
        
        prompt = f"""
        Encontre 5 lojas online no Brasil que vendem o seguinte produto: {presente.descricao}
        Preço estimado: R$ {presente.preco if presente.preco else 'Não informado'}
        
        Retorne APENAS um JSON válido no seguinte formato:
        {{
            "sugestoes": [
                {{
                    "loja": "Nome da Loja",
                    "url": "https://www.loja.com.br/produto",
                    "preco": 199.90
                }}
            ]
        }}
        
        Busque por lojas reais e conhecidas como Amazon, Mercado Livre, Magazine Luiza, Americanas, etc.
        """
        
        try:
            message = client.messages.create(
                model="claude-sonnet-4-20250514",
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
                {{"loja": "Nome", "url": "URL", "preco": 199.90}}
            ]
        }}
        """
        
        try:
            response = openai.chat.completions.create(
                model="gpt-4",
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
        """Busca sugestões usando Google Gemini"""
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key={settings.GEMINI_API_KEY}"
        
        prompt = f"""
        Encontre 5 lojas online no Brasil que vendem: {presente.descricao}
        Retorne em formato JSON com loja, url e preco.
        """
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        
        try:
            response = requests.post(url, json=payload)
            dados = response.json()
            texto = dados['candidates'][0]['content']['parts'][0]['text']
            texto = texto.replace('```json', '').replace('```', '').strip()
            sugestoes = json.loads(texto)
            
            IAService._salvar_sugestoes(presente, sugestoes['sugestoes'])
            return True, "Sugestões encontradas com sucesso!"
            
        except Exception as e:
            return False, f"Erro ao buscar sugestões: {str(e)}"
    
    @staticmethod
    def _salvar_sugestoes(presente, sugestoes):
        """Salva as sugestões no banco de dados"""
        # Limpar sugestões antigas
        SugestaoCompra.objects.filter(presente=presente).delete()

        # Salvar novas sugestões
        for sug in sugestoes:
            loja = sug.get('loja', '').strip()
            url = sug.get('url', '').strip()
            preco = sug.get('preco')

            # Validar dados antes de salvar
            if not loja or not url:
                logger.warning(f"Ignorando sugestão da IA com dados vazios: {sug}")
                continue

            SugestaoCompra.objects.create(
                presente=presente,
                local_compra=loja,
                url_compra=url,
                preco_sugerido=preco
            )
