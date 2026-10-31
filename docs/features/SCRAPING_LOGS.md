# 🔍 Extração de Produtos, Logs e Issues Automáticas

Como o sistema lê título, preço e imagem a partir do link de um produto, o que aparece nos logs do Render e quando uma issue é aberta automaticamente no GitHub.

Código: [`presentes/scrapers.py`](../../presentes/scrapers.py), [`presentes/mercadolivre_api.py`](../../presentes/mercadolivre_api.py), [`presentes/precos.py`](../../presentes/precos.py), [`presentes/github_helper.py`](../../presentes/github_helper.py).

---

## 🛍️ Scrapers

A `ScraperFactory` escolhe o scraper pelo domínio da URL:

| Scraper | Domínios | Como lê |
|---------|----------|---------|
| `AmazonScraper` | `amazon.com*`, links curtos `amzn.to`, `a.co`, `amzn.com` | Seletores HTML (título, preço, imagem/`data-a-dynamic-image`) |
| `MercadoLivreScraper` | `mercadolivre.com*`, `mercadolibre.com*`, `meli.la` | **API oficial primeiro**; se ela falhar, a página |
| `KabumScraper` | `kabum.com*` | Seletores HTML |
| `DecathlonScraper` | `decathlon.com*` | JSON-LD (schema.org) da página, com `og:title`/`og:image` de reserva |
| `GenericScraper` | qualquer outro site | Meta tags, JSON-LD e ofertas schema.org embutidas |

Antes da leitura, os **parâmetros de rastreamento** são removidos da URL (`utm_*`, `gclid`, `fbclid`, `gad_source`, `srsltid`).

### Mercado Livre

- O site bloqueia consultas automáticas (página `/gz/account-verification`), por isso a API oficial é o caminho preferido. Requer `MERCADOLIVRE_CLIENT_ID` e `MERCADOLIVRE_CLIENT_SECRET`. O token é obtido por `client_credentials`.
- A API não libera `/items` de anúncios de outros vendedores, mas libera o **catálogo**: `/products/{id}` (nome e fotos) e `/products/{id}/items` (preço).
- Link só de anúncio (`MLB-123-titulo`): o título vem da descrição do anúncio (ou do link) e o produto é procurado no catálogo por esse título.
- **Limite conhecido:** anúncio **fora do catálogo** traz só o título. O scraper preenche `aviso` explicando que preço e foto devem ser preenchidos manualmente, e não é aberta issue.
- Links curtos (`mercadolivre.com/sec/...`, `meli.la`) são expandidos.

### Scraper genérico

- **Título:** `og:title`, `twitter:title` e outras alternativas.
- **Preço:**
  1. meta tags `product:price:amount` / `itemprop="price"`;
  2. dados estruturados: JSON-LD (`Product`/`ProductGroup`, com variantes) e ofertas schema.org embutidas em scripts/atributos, inclusive com URL-encoding (lojas VTEX/deco.cx, ex.: Farm Rio). Só aceita ofertas em `BRL`;
  3. textos com classe `price`/`preco`/`valor`.
- **Moeda diferente de BRL** (meta `product:price:currency` etc.): usa apenas o valor em reais que a página mostra entre parênteses, ex.: `US$ 254,00 (R$ 1.371,60)`.
- **Imagem:** `og:image` ou `twitter:image`.

### Conversão de preço

Todas as leituras usam `converter_preco()` de `presentes/precos.py`, que identifica o separador decimal: com ponto e vírgula, o último é o decimal (`1.371,60`, `1,371.60`); com um só separador, ele é decimal quando tem 1 ou 2 dígitos depois (`254,00`) e de milhar com 3 dígitos (`1.371`).

---

## 🚦 Resultados da extração

`ScraperFactory.extract_product_info(url)` (usada por `/api/extrair-info-produto/` e pela busca de imagem) devolve:

| Situação | `success` / `error_type` | Abre issue? |
|----------|--------------------------|-------------|
| Leitura completa | `True` | Não |
| Leitura incompleta com `aviso` (limite conhecido da loja) | `True`, com `aviso` | **Não** |
| Leitura incompleta, site **não mapeado** (genérico) | `True` | Sim: `[AUTO] Site não mapeado: <domínio>` |
| Leitura incompleta, site **mapeado** | `True` | Sim: `[AUTO] Leitura incompleta em site mapeado: <domínio>` |
| Sem título (`ParsingError`) | `False`, `parsing` | Sim: `[AUTO] Falha ao extrair dados: <domínio>` |
| Bloqueio anti-robô (`BlockedError`) | `False`, `blocked` | **Não** |
| Erro de rede/HTTP (`NetworkError`) | `False`, `network` | Não |

O bloqueio é detectado por redirecionamento para URLs como `/gz/account-verification`, `/captcha` e `/challenge`, ou por títulos de página como "captcha", "bot manager", "just a moment" e "access denied".

---

## 🐛 Issues automáticas

### Configuração (Render → Environment)

```bash
GITHUB_TOKEN=ghp_...                 # token com permissão de criar issues no repositório
GITHUB_REPO_OWNER=Maxwbh             # padrão
GITHUB_REPO_NAME=Lista_de_Presentes  # padrão
GITHUB_AUTO_CREATE_ISSUES=True       # padrão; False desliga a criação
```

Sem `GITHUB_TOKEN`, ou com `GITHUB_AUTO_CREATE_ISSUES=False`, nenhuma issue é criada (o log registra o motivo).

### Tipos de issue

| Título | Quando | Labels |
|--------|--------|--------|
| `[AUTO] Site não mapeado: <domínio>` | Genérico leu de forma incompleta | `auto-generated`, `enhancement`, `new-site-support`, `low-priority` |
| `[AUTO] Leitura incompleta em site mapeado: <domínio>` | Scraper específico leu de forma incompleta (provável mudança de layout) | `auto-generated`, `bug`, `scraping` |
| `[AUTO] Falha ao extrair dados: <domínio>` | Nenhum título extraído | `auto-generated`, `enhancement`, `scraping`, `needs-triage`, `extracao-*` |
| `[AUTO] Falha ao carregar imagem: <presente>` | Falha ao baixar a imagem informada para um presente | `auto-generated`, `bug`, `imagem`, `needs-triage` |

As issues de extração trazem a URL, os dados lidos, o erro e a seção **"Log da Extração"**: as mensagens de log dos módulos `presentes.scrapers` e `presentes.mercadolivre_api` daquela leitura (até 40 linhas).

### Sem duplicatas

- Antes de criar, o sistema procura uma issue **aberta** com label `auto-generated` e **o mesmo título**. Se existir, não cria outra: adiciona um comentário **"Nova ocorrência"** com os detalhes, a menos que a mesma URL já apareça na issue ou nos comentários.
- As issues criadas nos **últimos 10 minutos** ficam guardadas em memória (a listagem do GitHub demora para mostrar uma issue recém-criada). Isso evita issues repetidas em leituras seguidas, como na busca de imagens em lote.

---

## 🖼️ Admin: buscar imagens que faltam

Em **Admin → Presentes**:

- Botão **"Buscar imagens que faltam (N)"**: busca a imagem de todos os presentes sem imagem que têm link e abre a lista filtrada por "Sem imagem".
- Ação **"Buscar imagem no site (link original)"** para os presentes selecionados.
- Filtro **"Por imagem"** (com/sem imagem).
- Coluna **"Última busca de imagem"**: data e resultado (`busca_imagem_resultado`), ex.: "Foto encontrada.", "O site bloqueou a consulta automática." ou o `aviso` da loja.

Lotes grandes rodam em segundo plano: recarregue a página para ver a coluna atualizada. Se o presente estiver sem preço, a busca também preenche o preço lido no site.

---

## 📋 Logs no Render

Render Dashboard → serviço → **Logs**. Mensagens úteis:

| Mensagem | Significado |
|----------|-------------|
| `🛍️ Usando AmazonScraper`, `🛒 Usando MercadoLivreScraper`, `🎮 Usando KabumScraper`, `🏃 Usando DecathlonScraper` | Scraper escolhido |
| `⚠️ SITE NÃO MAPEADO: <domínio>` | Vai usar o scraper genérico |
| `<Loja> - Título: True, Preço: ..., Imagem: ...` | Resumo da leitura |
| `API: ...` | Passos da API do Mercado Livre |
| `Acesso bloqueado ...` | Bloqueio anti-robô (sem issue) |
| `Leitura incompleta por limite conhecido da loja` | `aviso` preenchido (sem issue) |
| `⚠️ ERRO DE PARSING ao extrair dados de: <url>` | Vai tentar abrir issue |
| `✅ Issue #N criada` / `Issue #N ja existe` / `Nova ocorrência registrada na issue #N` | Resultado da issue |

O nível de log padrão é `INFO` (`LOGGING` em `lista_presentes/settings.py`).

### Testar a criação de issue

```python
# python manage.py shell
from presentes.github_helper import criar_issue_falha_scraping
criar_issue_falha_scraping(
    url_produto='https://loja.exemplo.com/produto',
    dados_extraidos={'titulo': None, 'preco': None, 'imagem_url': None},
)
# {'success': True, 'issue_number': ..., 'issue_url': '...'}
```

---

## 🆘 Troubleshooting

- **Issue não foi criada:** confira `GITHUB_TOKEN` (válido e com permissão de issues) e `GITHUB_AUTO_CREATE_ISSUES`. Bloqueios, erros de rede e leituras com `aviso` não abrem issue de propósito. Se já havia issue aberta com o mesmo título, procure o comentário "Nova ocorrência".
- **Mercado Livre sem preço/foto:** veja se as credenciais da API estão configuradas e se o anúncio está no catálogo (a mensagem do `aviso` explica).
- **Preço errado:** verifique a moeda da página; preços fora de BRL só são aceitos pelo valor em reais entre parênteses.
