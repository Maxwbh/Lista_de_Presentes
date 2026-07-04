"""
Helper para integracao com GitHub API
Cria issues automaticamente para problemas de download de imagem
"""
import requests
import logging
from django.conf import settings
from datetime import datetime

logger = logging.getLogger(__name__)


def criar_issue_falha_imagem(presente, url_imagem, erro_descricao, usuario=None):
    """
    Cria uma issue no GitHub para falha ao carregar imagem de presente.
    
    Args:
        presente: Instancia do modelo Presente
        url_imagem: URL da imagem que falhou
        erro_descricao: Descricao do erro
        usuario: Usuario que tentou adicionar (opcional)
    
    Returns:
        dict: Resposta da API do GitHub ou None em caso de falha
    """
    # Verificar se feature esta habilitada
    if not settings.GITHUB_AUTO_CREATE_ISSUES:
        logger.info("GitHub auto-create issues desabilitado")
        return None
    
    # Verificar se token esta configurado
    if not settings.GITHUB_TOKEN:
        logger.warning("GITHUB_TOKEN nao configurado. Issue nao sera criada.")
        return None
    
    try:
        # Preparar dados da issue
        titulo = f"[AUTO] Falha ao carregar imagem: {presente.descricao[:50]}"
        
        # Corpo da issue com detalhes
        corpo = f"""## Falha Automatica ao Carregar Imagem

### Detalhes do Presente
- **ID**: {presente.id}
- **Descricao**: {presente.descricao}
- **Preco**: R$ {presente.preco if presente.preco else 'Nao informado'}
- **URL do Produto**: {presente.url if presente.url else 'Nao informado'}
- **Usuario**: {usuario.email if usuario else 'N/A'}
- **Grupo**: {presente.grupo.nome if presente.grupo else 'Sem grupo'}
- **Data**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Status**: {presente.status}

### URL da Imagem que Falhou
```
{url_imagem}
```

### Erro Reportado
```
{erro_descricao}
```

### Link do Presente
{settings.SITE_URL}/presente/{presente.id}/

### Acoes Sugeridas
- [ ] Verificar se a URL da imagem esta acessivel
- [ ] Verificar se o formato da imagem e suportado
- [ ] Verificar restricoes de CORS ou autenticacao
- [ ] Testar download manual da imagem
- [ ] Implementar tratamento especifico para este tipo de URL

### Informacoes Tecnicas
- **Tipo de erro**: Falha de download de imagem
- **Origem**: Sistema automatico de criacao de presentes
- **Severidade**: Media
- **Categoria**: Bug

---
*Esta issue foi criada automaticamente pelo sistema quando o usuario tentou adicionar um presente com imagem.*
*Versao: {_get_app_version()}*
"""
        
        # Preparar request
        url = f"{settings.GITHUB_API_BASE_URL}/repos/{settings.GITHUB_REPO_OWNER}/{settings.GITHUB_REPO_NAME}/issues"
        
        headers = {
            'Authorization': f'token {settings.GITHUB_TOKEN}',
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json',
        }
        
        payload = {
            'title': titulo,
            'body': corpo,
            'labels': ['auto-generated', 'bug', 'imagem', 'needs-triage'],
        }
        
        # Fazer request
        logger.info(f"Criando issue no GitHub para presente {presente.id}")
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 201:
            issue_data = response.json()
            issue_number = issue_data.get('number')
            issue_url = issue_data.get('html_url')
            
            logger.info(f"Issue #{issue_number} criada com sucesso: {issue_url}")
            
            return {
                'success': True,
                'issue_number': issue_number,
                'issue_url': issue_url,
                'data': issue_data
            }
        else:
            logger.error(
                f"Falha ao criar issue no GitHub. "
                f"Status: {response.status_code}, "
                f"Response: {response.text}"
            )
            return {
                'success': False,
                'error': response.text,
                'status_code': response.status_code
            }
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro de rede ao criar issue no GitHub: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }
    except Exception as e:
        logger.error(f"Erro inesperado ao criar issue no GitHub: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


def criar_issue_falha_scraping(url_produto, dados_extraidos, usuario=None, grupo=None):
    """
    Cria uma issue no GitHub para falha no scraping/extracao de dados de produto.

    Esta funcao e chamada quando o sistema consegue acessar o site (sem erro HTTP),
    mas nao consegue extrair os dados (titulo, preco, imagem) corretamente.

    Args:
        url_produto: URL do produto que falhou ao ser extraida
        dados_extraidos: dict com dados extraidos (pode ter valores None/vazios)
                        Exemplo: {'titulo': 'ABC', 'preco': None, 'imagem_url': None}
        usuario: Usuario que tentou adicionar (opcional)
        grupo: Grupo ao qual o usuario pertence (opcional)

    Returns:
        dict: Resposta da API do GitHub ou None em caso de falha
    """
    # Verificar se feature esta habilitada
    if not settings.GITHUB_AUTO_CREATE_ISSUES:
        logger.info("GitHub auto-create issues desabilitado")
        return None

    # Verificar se token esta configurado
    if not settings.GITHUB_TOKEN:
        logger.warning("GITHUB_TOKEN nao configurado. Issue nao sera criada.")
        return None

    try:
        # Extrair dominio da URL
        from urllib.parse import urlparse
        dominio = urlparse(url_produto).netloc

        # Preparar dados da issue
        titulo = f"[AUTO] Falha ao extrair dados: {dominio}"

        # Analisar quais dados falharam
        dados_falhados = []
        if not dados_extraidos.get('titulo'):
            dados_falhados.append('Título')
        if not dados_extraidos.get('preco'):
            dados_falhados.append('Preço')
        if not dados_extraidos.get('imagem_url'):
            dados_falhados.append('Imagem')

        dados_falhados_str = ', '.join(dados_falhados) if dados_falhados else 'Todos os campos'

        # Corpo da issue com detalhes
        corpo = f"""## Falha Automatica na Extracao de Dados de Produto

### Problema Detectado
O sistema conseguiu acessar a URL do produto (sem erros HTTP), mas **nao conseguiu extrair** os seguintes dados:
**{dados_falhados_str}**

Este tipo de erro indica que:
1. O site mudou sua estrutura HTML
2. O site nao e suportado pelo sistema
3. O template de extracao precisa ser atualizado

### URL do Produto
```
{url_produto}
```

### Dominio
`{dominio}`

### Dados Extraidos (Parcialmente)
"""

        # Adicionar dados extraidos (mesmo que vazios)
        corpo += f"""
- **Titulo**: {dados_extraidos.get('titulo') or '❌ Nao extraido'}
- **Preco**: {f"R$ {dados_extraidos.get('preco')}" if dados_extraidos.get('preco') else '❌ Nao extraido'}
- **Imagem**: {dados_extraidos.get('imagem_url') or '❌ Nao extraida'}

### Contexto do Usuario
- **Usuario**: {usuario.email if usuario else 'N/A'}
- **Grupo**: {grupo.nome if grupo else 'N/A'}
- **Data**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

### Acoes Sugeridas
- [ ] Verificar se o dominio `{dominio}` ja esta implementado em `scrapers.py`
- [ ] Acessar a URL manualmente e inspecionar a estrutura HTML
- [ ] Verificar se o site usa JavaScript para carregar dados (SPA)
- [ ] Implementar scraper especifico para `{dominio}` se for site conhecido
- [ ] Atualizar scraper generico para detectar novos padroes
- [ ] Verificar se o site tem protecao anti-bot (Cloudflare, etc.)

### Informacoes Tecnicas
- **Tipo de erro**: Falha de scraping/parsing (site acessivel)
- **Origem**: Sistema automatico de extracao via URL
- **Severidade**: Media
- **Categoria**: Enhancement/Bug
- **Necessita acao**: Sim - atualizar scrapers

### Como Reproduzir
1. Acessar sistema
2. Adicionar novo presente
3. Inserir URL: `{url_produto}`
4. Tentar extrair dados automaticamente
5. Observar que campos nao sao preenchidos

---
*Esta issue foi criada automaticamente quando o sistema detectou falha na extracao de dados.*
*Versao: {_get_app_version()}*
"""

        # Preparar request
        url = f"{settings.GITHUB_API_BASE_URL}/repos/{settings.GITHUB_REPO_OWNER}/{settings.GITHUB_REPO_NAME}/issues"

        headers = {
            'Authorization': f'token {settings.GITHUB_TOKEN}',
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json',
        }

        # Labels dinamicos baseados em dados falhados
        labels = ['auto-generated', 'enhancement', 'scraping', 'needs-triage']
        if 'Título' in dados_falhados:
            labels.append('extracao-titulo')
        if 'Preço' in dados_falhados:
            labels.append('extracao-preco')
        if 'Imagem' in dados_falhados:
            labels.append('extracao-imagem')

        payload = {
            'title': titulo,
            'body': corpo,
            'labels': labels,
        }

        # Fazer request
        logger.info(f"Criando issue no GitHub para falha de scraping: {dominio}")
        response = requests.post(url, json=payload, headers=headers, timeout=10)

        if response.status_code == 201:
            issue_data = response.json()
            issue_number = issue_data.get('number')
            issue_url = issue_data.get('html_url')

            logger.info(f"Issue #{issue_number} criada com sucesso: {issue_url}")

            return {
                'success': True,
                'issue_number': issue_number,
                'issue_url': issue_url,
                'data': issue_data
            }
        else:
            logger.error(
                f"Falha ao criar issue no GitHub. "
                f"Status: {response.status_code}, "
                f"Response: {response.text}"
            )
            return {
                'success': False,
                'error': response.text,
                'status_code': response.status_code
            }

    except requests.exceptions.RequestException as e:
        logger.error(f"Erro de rede ao criar issue no GitHub: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }
    except Exception as e:
        logger.error(f"Erro inesperado ao criar issue no GitHub: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            'success': False,
            'error': str(e)
        }


def _get_app_version():
    """Retorna a versao do app a partir do arquivo VERSION"""
    try:
        from pathlib import Path
        version_file = Path(settings.BASE_DIR) / 'VERSION'
        if version_file.exists():
            return version_file.read_text().strip()
        return 'unknown'
    except:
        return 'unknown'


def criar_issue_erro_geral(titulo, descricao, contexto=None, labels=None):
    """
    Cria uma issue generica no GitHub.
    
    Args:
        titulo: Titulo da issue
        descricao: Descricao detalhada
        contexto: Dicionario com informacoes adicionais (opcional)
        labels: Lista de labels (opcional)
    
    Returns:
        dict: Resposta da API do GitHub ou None
    """
    if not settings.GITHUB_AUTO_CREATE_ISSUES or not settings.GITHUB_TOKEN:
        return None
    
    try:
        # Preparar corpo
        corpo = f"{descricao}\n\n"
        
        if contexto:
            corpo += "### Contexto Adicional\n"
            for chave, valor in contexto.items():
                corpo += f"- **{chave}**: {valor}\n"
            corpo += "\n"
        
        corpo += f"---\n*Auto-gerado em {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
        corpo += f"*Versao: {_get_app_version()}*"
        
        # Request
        url = f"{settings.GITHUB_API_BASE_URL}/repos/{settings.GITHUB_REPO_OWNER}/{settings.GITHUB_REPO_NAME}/issues"
        
        headers = {
            'Authorization': f'token {settings.GITHUB_TOKEN}',
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json',
        }
        
        payload = {
            'title': titulo,
            'body': corpo,
            'labels': labels or ['auto-generated'],
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 201:
            issue_data = response.json()
            logger.info(f"Issue criada: {issue_data.get('html_url')}")
            return {
                'success': True,
                'issue_number': issue_data.get('number'),
                'issue_url': issue_data.get('html_url'),
                'data': issue_data
            }
        else:
            logger.error(f"Falha ao criar issue: {response.text}")
            return {
                'success': False,
                'error': response.text
            }
    
    except Exception as e:
        logger.error(f"Erro ao criar issue: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }
