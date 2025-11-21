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
                    loja_elem = (
                        card.find('span', {'data-testid': 'product-card::store-name'}) or
                        card.find('span', class_=lambda x: x and 'store' in x.lower() if x else False) or
                        card.find('p', class_=lambda x: x and 'seller' in x.lower() if x else False)
                    )
                    loja = loja_elem.text.strip() if loja_elem else "Zoom"

                    # Extrair preço (múltiplos seletores)
                    preco_elem = (
                        card.find('p', {'data-testid': 'product-card::price'}) or
                        card.find('span', class_=lambda x: x and 'price' in x.lower() if x else False) or
                        card.find('div', class_=lambda x: x and 'price' in x.lower() if x else False)
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
                        logger.debug("Zoom: Preço não encontrado")
                        continue

                    # Extrair URL
                    link_elem = (
                        card.find('a', {'data-testid': 'product-card::product'}) or
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

            # Tentar múltiplos seletores
            cards = (
                soup.find_all('div', class_=lambda x: x and 'ProductCard' in x if x else False) or
                soup.find_all('div', class_=lambda x: x and 'SearchCard' in x if x else False) or
                soup.find_all('article', class_=lambda x: x and 'product' in x.lower() if x else False) or
                soup.find_all('div', {'data-component': lambda x: x and 'product' in x.lower() if x else False}) or
                soup.find_all('div', class_=lambda x: x and 'card' in x.lower() if x else False)
            )

            logger.info(f"Buscapé: Encontrados {len(cards)} cards no HTML")

            # Se não encontrou cards, log debug
            if len(cards) == 0:
                logger.warning("Buscapé: Nenhum card encontrado, salvando HTML para debug...")
                logger.debug(f"Buscapé HTML (primeiros 1000 chars): {str(soup)[:1000]}")

            for i, card in enumerate(cards[:max_results]):
                try:
                    logger.debug(f"Processando card {i+1} do Buscapé")

                    # Extrair nome da loja (múltiplos seletores)
                    loja_elem = (
                        card.find('span', class_=lambda x: x and 'store' in x.lower() if x else False) or
                        card.find('p', class_=lambda x: x and 'seller' in x.lower() if x else False) or
                        card.find('div', class_=lambda x: x and 'merchant' in x.lower() if x else False)
                    )
                    loja = loja_elem.text.strip() if loja_elem else "Buscapé"

                    # Extrair preço (múltiplos seletores)
                    preco_elem = (
                        card.find('p', class_=lambda x: x and 'price' in x.lower() if x else False) or
                        card.find('span', class_=lambda x: x and 'price' in x.lower() if x else False) or
                        card.find('div', class_=lambda x: x and 'price' in x.lower() if x else False)
                    )

                    if preco_elem:
                        preco_text = preco_elem.text.strip()
                        logger.debug(f"Buscapé: Preço encontrado: {preco_text}")
                        # Remover "R$" e converter para float
                        preco_text = preco_text.replace('R$', '').replace('.', '').replace(',', '.').strip()
                        try:
                            preco = float(preco_text)
                        except ValueError:
                            logger.warning(f"Buscapé: Não foi possível converter preço: {preco_text}")
                            continue
                    else:
                        logger.debug("Buscapé: Preço não encontrado")
                        continue

                    # Extrair URL
                    link_elem = card.find('a', href=True)
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
            for produto in todos_produtos[:10]:
                SugestaoCompra.objects.create(
                    presente=presente,
                    local_compra=f"{produto['loja']} ({produto['fonte']})",
                    url_compra=produto['url'],
                    preco_sugerido=produto.get('preco') if produto.get('preco', 0) > 0 else None
                )

            return True, f"Encontradas {len(todos_produtos[:10])} sugestões de IA + Zoom + Buscapé!"

        except Exception as e:
            logger.error(f"Erro ao buscar sugestões: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False, f"Erro ao buscar preços: {str(e)}"

    @staticmethod
    def buscar_sugestoes_claude(presente):
        """Busca sugestões usando Claude AI"""
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        
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
            SugestaoCompra.objects.create(
                presente=presente,
                local_compra=sug['loja'],
                url_compra=sug['url'],
                preco_sugerido=sug.get('preco')
            )
