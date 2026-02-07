# Sistema de Logging e Issues Automáticas para Scraping

Documentação do sistema de logging aprimorado e geração automática de issues no GitHub para falhas de scraping.

## Visão Geral

O sistema de scraping foi melhorado para:
1. **Logs visíveis no console do Render** com formatação clara
2. **Criação automática de issues no GitHub** quando falhas de parsing ocorrem
3. **Diferenciação entre erros de rede e erros de parsing**

## Tipos de Erro

### 1. NetworkError (Erro de Rede/HTTP)
**O que é**: Problemas ao acessar a URL (404, 500, timeout, conexão falhou, etc.)

**Comportamento**:
- ❌ **NÃO gera issue no GitHub** (são erros temporários/externos)
- ⚠️  Log de warning no console
- Retorna `error_type: 'network'`

**Exemplos**:
- HTTP 404 (página não encontrada)
- HTTP 500 (erro do servidor)
- Timeout (servidor não respondeu)
- Connection refused (servidor offline)

**Log no Console**:
```
================================================================================
⚠️  ERRO DE REDE ao acessar: https://amazon.com.br/produto/12345
   Status HTTP: 404
   Erro: Erro HTTP 404: Not Found
================================================================================
```

### 2. ParsingError (Erro de Extração de Dados)
**O que é**: Site acessível mas dados não podem ser extraídos (título, preço, imagem)

**Comportamento**:
- ✅ **GERA issue no GitHub automaticamente**
- ❌ Log de erro no console
- Retorna `error_type: 'parsing'`
- Issue criada com labels: `auto-generated`, `enhancement`, `scraping`

**Exemplos**:
- Site mudou estrutura HTML
- Site não suportado pelo sistema
- Scraper desatualizado
- Site protegido (captcha, anti-bot)

**Log no Console**:
```
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
❌ ERRO CRÍTICO DE SCRAPING - AMAZON
   URL: https://amazon.com.br/produto/12345
   Título: Não extraído ❌
   Preço: Não extraído
   Imagem: Não extraída

   ⚠️  ATENÇÃO: Issue será criada automaticamente no GitHub
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

================================================================================
⚠️  ERRO DE PARSING ao extrair dados de: https://amazon.com.br/produto/12345
   Erro: Nao foi possivel extrair titulo da Amazon. Dados parciais: preco=None, imagem=False

   ℹ️  Tentando criar issue no GitHub automaticamente...
================================================================================
✅ Issue #123 criada: https://github.com/Maxwbh/Lista_de_Presentes/issues/123
```

## Logs de Sucesso

### Amazon
```
================================================================================
🛍️  AMAZON SCRAPING - URL: https://amazon.com.br/produto/12345...
   📝 Título:  ✅ Extraído - Produto XYZ Incrível e Maravilhoso...
   💰 Preço:   ✅ Extraído - R$ 199.90
   🖼️  Imagem:  ✅ Extraída
================================================================================
```

### Mercado Livre
```
================================================================================
🛒 MERCADO LIVRE SCRAPING - URL: https://mercadolivre.com.br/MLB-12345...
   📝 Título:  ✅ Extraído - Produto ABC...
   💰 Preço:   ✅ Extraído - R$ 299.90
   🖼️  Imagem:  ⚠️  Não encontrada
================================================================================
```

### Kabum
```
================================================================================
🎮 KABUM SCRAPING - URL: https://kabum.com.br/produto/12345...
   📝 Título:  ✅ Extraído - Placa de Vídeo...
   💰 Preço:   ⚠️  Não encontrado
   🖼️  Imagem:  ✅ Extraída
================================================================================
```

### Generic (Site Desconhecido)
```
================================================================================
🌐 SCRAPING GENÉRICO - URL: https://loja-desconhecida.com.br/produto...
   📝 Título:  ✅ Extraído - Produto Teste...
   💰 Preço:   ✅ Extraído - R$ 99.99
   🖼️  Imagem:  ✅ Extraída
================================================================================
```

## Issues Automáticas no GitHub

### Requisitos

As seguintes variáveis de ambiente devem estar configuradas:

```bash
# Render Dashboard > Environment Variables
GITHUB_TOKEN=ghp_...                           # Token de acesso pessoal
GITHUB_REPO_OWNER=Maxwbh                       # Dono do repositório
GITHUB_REPO_NAME=Lista_de_Presentes            # Nome do repositório
GITHUB_AUTO_CREATE_ISSUES=True                 # Habilitar auto-criação
```

### Estrutura da Issue Criada

**Título**:
```
[AUTO] Falha ao extrair dados: amazon.com.br
```

**Labels**:
- `auto-generated` - Issue criada automaticamente
- `enhancement` - Melhoria necessária
- `scraping` - Relacionado a scraping
- `needs-triage` - Precisa análise
- `extracao-titulo` - Se título falhou
- `extracao-preco` - Se preço falhou
- `extracao-imagem` - Se imagem falhou

**Corpo da Issue**:
```markdown
## Falha Automatica na Extracao de Dados de Produto

### Problema Detectado
O sistema conseguiu acessar a URL do produto (sem erros HTTP), mas **nao conseguiu extrair** os seguintes dados:
**Título, Preço**

Este tipo de erro indica que:
1. O site mudou sua estrutura HTML
2. O site nao e suportado pelo sistema
3. O template de extracao precisa ser atualizado

### URL do Produto
```
https://amazon.com.br/produto/12345
```

### Dominio
`amazon.com.br`

### Dados Extraidos (Parcialmente)
- **Titulo**: ❌ Nao extraido
- **Preco**: ❌ Nao extraido
- **Imagem**: ✅ https://m.media-amazon.com/images/...

### Contexto do Usuario
- **Usuario**: N/A
- **Grupo**: N/A
- **Data**: 2026-02-03 17:30:00

### Acoes Sugeridas
- [ ] Verificar se o dominio `amazon.com.br` ja esta implementado em `scrapers.py`
- [ ] Acessar a URL manualmente e inspecionar a estrutura HTML
- [ ] Verificar se o site usa JavaScript para carregar dados (SPA)
- [ ] Implementar scraper especifico para `amazon.com.br` se for site conhecido
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
3. Inserir URL: `https://amazon.com.br/produto/12345`
4. Tentar extrair dados automaticamente
5. Observar que campos nao sao preenchidos

---
*Esta issue foi criada automaticamente quando o sistema detectou falha na extracao de dados.*
*Versao: 1.1.13*
```

## Configuração do GitHub Token

### 1. Criar Token no GitHub

1. Acesse: https://github.com/settings/tokens
2. Clique em "Generate new token" > "Classic"
3. Nome: `Lista de Presentes - Auto Issues`
4. Expiration: `No expiration` (ou 90 dias)
5. Scopes necessários:
   - ✅ `repo` (acesso completo a repositórios privados/públicos)
     - ✅ `repo:status`
     - ✅ `repo_deployment`
     - ✅ `public_repo`
     - ✅ `repo:invite`
     - ✅ `security_events`
6. Clique em "Generate token"
7. **COPIE O TOKEN** (você não verá novamente!)

### 2. Adicionar no Render

1. Dashboard do Render > Service > Environment
2. Adicionar variável: `GITHUB_TOKEN`
3. Valor: Cole o token copiado
4. Save Changes
5. Redeploy (manual ou aguardar próximo deploy)

### 3. Testar

```python
# Via Render Shell ou localmente
python manage.py shell

from presentes.github_helper import criar_issue_falha_scraping

result = criar_issue_falha_scraping(
    url_produto='https://amazon.com.br/teste',
    dados_extraidos={'titulo': None, 'preco': None, 'imagem_url': None},
)

print(result)
# Deve retornar: {'success': True, 'issue_number': 123, 'issue_url': '...'}
```

## Desabilitar Issues Automáticas

Para desabilitar temporariamente (sem remover token):

```bash
# Render Dashboard > Environment
GITHUB_AUTO_CREATE_ISSUES=False
```

## Monitoramento no Render

### Ver Logs em Tempo Real

1. Render Dashboard > Service > Logs
2. Procurar por:
   - `🛍️` - Scraping Amazon
   - `🛒` - Scraping Mercado Livre
   - `🎮` - Scraping Kabum
   - `🌐` - Scraping Genérico
   - `✅` - Sucesso
   - `❌` - Erro crítico
   - `⚠️` - Warning

### Filtrar Logs

```bash
# Apenas sucessos
grep "✅" logs.txt

# Apenas erros críticos
grep "❌ ERRO CRÍTICO" logs.txt

# Apenas parsing errors
grep "ERRO DE PARSING" logs.txt

# Issues criadas
grep "Issue #" logs.txt
```

## Análise de Problemas

### Issue Criada Mas Não Devia

**Causa**: `GITHUB_AUTO_CREATE_ISSUES=True` está ativo

**Solução**:
1. Desabilitar: `GITHUB_AUTO_CREATE_ISSUES=False`
2. Ou remover `GITHUB_TOKEN`

### Issue Não Criada Mas Devia

**Causa Possível 1**: Token inválido/expirado
```bash
# Verificar logs
grep "GITHUB_TOKEN nao configurado" logs.txt
grep "Falha ao criar issue" logs.txt
```

**Solução**: Gerar novo token e atualizar `GITHUB_TOKEN`

**Causa Possível 2**: Feature desabilitada
```bash
# Verificar
echo $GITHUB_AUTO_CREATE_ISSUES  # Deve ser "True"
```

**Solução**: `GITHUB_AUTO_CREATE_ISSUES=True`

**Causa Possível 3**: NetworkError (não deve gerar issue)
```bash
# Verificar se foi erro de rede (404, 500, timeout)
grep "ERRO DE REDE" logs.txt
```

**Solução**: NetworkErrors são esperados e não geram issues

### Logs Não Aparecem

**Causa**: Nível de log configurado incorretamente

**Solução**: Verificar `settings.py`:
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',  # Deve ser INFO ou DEBUG
        },
    },
    'loggers': {
        'presentes': {
            'handlers': ['console'],
            'level': 'INFO',  # Deve ser INFO ou DEBUG
        },
    },
}
```

## Estatísticas

Para análise de problemas, use os logs:

```bash
# Quantas falhas de scraping hoje?
grep "ERRO CRÍTICO DE SCRAPING" logs.txt | wc -l

# Quais sites falharam mais?
grep "ERRO CRÍTICO DE SCRAPING" logs.txt | grep -oP "(?<=SCRAPING - )[A-Z]+" | sort | uniq -c

# Quantas issues foram criadas?
grep "Issue #[0-9]+ criada" logs.txt | wc -l

# Taxa de sucesso por site
grep -c "AMAZON.*✅ Extraído" logs.txt
```

## Changelog

### v1.1.14 (2026-02-03)
- ✨ Logs formatados com emojis e separadores visuais
- ✨ Diferenciação clara entre NetworkError e ParsingError
- ✨ Integração automática com criação de issues no GitHub
- ✨ Logs de erro crítico bem visíveis no console do Render
- ✨ Informação de criação de issue nos logs
- 📝 Documentação completa do sistema de logging

## Contato

Dúvidas ou problemas:
- Maxwell Oliveira (@maxwbh)
- maxwbh@gmail.com

## Referências

- [Scrapers Implementation](presentes/scrapers.py)
- [GitHub Helper](presentes/github_helper.py)
- [Django Logging](https://docs.djangoproject.com/en/4.2/topics/logging/)
