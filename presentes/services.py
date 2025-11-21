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

            soup = BeautifulSoup(response.content, 'lxml')
            produtos = []

            # Buscar produtos nos resultados
            cards = soup.find_all('div', {'data-testid': 'product-card'})[:max_results]

            for card in cards:
                try:
                    # Extrair nome da loja
                    loja_elem = card.find('span', {'data-testid': 'product-card::store-name'})
                    loja = loja_elem.text.strip() if loja_elem else "Loja desconhecida"

                    # Extrair preço
                    preco_elem = card.find('p', {'data-testid': 'product-card::price'})
                    if preco_elem:
                        preco_text = preco_elem.text.strip()
                        # Remover "R$" e converter para float
                        preco_text = preco_text.replace('R$', '').replace('.', '').replace(',', '.').strip()
                        preco = float(preco_text)
                    else:
                        continue

                    # Extrair URL
                    link_elem = card.find('a', {'data-testid': 'product-card::product'})
                    url_produto = f"https://www.zoom.com.br{link_elem.get('href')}" if link_elem else ""

                    produtos.append({
                        'loja': loja,
                        'preco': preco,
                        'url': url_produto,
                        'fonte': 'Zoom'
                    })
                except Exception as e:
                    logger.warning(f"Erro ao processar produto do Zoom: {str(e)}")
                    continue

            logger.info(f"Encontrados {len(produtos)} produtos no Zoom")
            return produtos

        except Exception as e:
            logger.error(f"Erro ao buscar no Zoom: {str(e)}")
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

            soup = BeautifulSoup(response.content, 'lxml')
            produtos = []

            # Buscar produtos nos resultados (Buscapé tem estrutura diferente)
            cards = soup.find_all('div', class_='SearchCard_ProductCard_Inner__7JhKb')[:max_results]

            for card in cards:
                try:
                    # Extrair nome da loja
                    loja_elem = card.find('span', class_='Text_MobileHeadingS__Zxam2')
                    loja = loja_elem.text.strip() if loja_elem else "Loja desconhecida"

                    # Extrair preço
                    preco_elem = card.find('p', class_='Text_MobileHeadingS__Zxam2')
                    if preco_elem:
                        preco_text = preco_elem.text.strip()
                        # Remover "R$" e converter para float
                        preco_text = preco_text.replace('R$', '').replace('.', '').replace(',', '.').strip()
                        preco = float(preco_text)
                    else:
                        continue

                    # Extrair URL
                    link_elem = card.find('a', class_='Link_')
                    url_produto = link_elem.get('href', '') if link_elem else ""
                    if url_produto and not url_produto.startswith('http'):
                        url_produto = f"https://www.buscape.com.br{url_produto}"

                    produtos.append({
                        'loja': loja,
                        'preco': preco,
                        'url': url_produto,
                        'fonte': 'Buscapé'
                    })
                except Exception as e:
                    logger.warning(f"Erro ao processar produto do Buscapé: {str(e)}")
                    continue

            logger.info(f"Encontrados {len(produtos)} produtos no Buscapé")
            return produtos

        except Exception as e:
            logger.error(f"Erro ao buscar no Buscapé: {str(e)}")
            return []

    @staticmethod
    def buscar_sugestoes_reais(presente):
        """Busca sugestões REAIS nos sites Zoom e Buscapé"""
        try:
            query = presente.descricao
            logger.info(f"Buscando preços reais para: {query}")

            # Buscar em ambos os sites
            produtos_zoom = IAService.buscar_preco_zoom(query, max_results=3)
            produtos_buscape = IAService.buscar_preco_buscape(query, max_results=3)

            # Combinar resultados
            todos_produtos = produtos_zoom + produtos_buscape

            if not todos_produtos:
                logger.warning("Nenhum produto encontrado nos sites")
                return False, "Não foram encontrados produtos nos sites de comparação de preços."

            # Ordenar por preço (menor primeiro)
            todos_produtos.sort(key=lambda x: x['preco'])

            # Pegar os 5 melhores preços
            melhores = todos_produtos[:5]

            # Salvar sugestões
            IAService._salvar_sugestoes(presente, melhores)

            return True, f"Encontradas {len(melhores)} sugestões de lojas reais!"

        except Exception as e:
            logger.error(f"Erro ao buscar sugestões reais: {str(e)}")
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
