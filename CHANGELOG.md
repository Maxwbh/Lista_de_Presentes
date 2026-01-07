# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [1.1.3] - 2025-01-07

### Adicionado - Sistema de Auto-Versionamento e Atribuição de Commits

**Automação Completa de Versionamento**
- 🔧 Pre-commit hook que incrementa automaticamente o número da versão em CADA commit
- 📦 Versão no arquivo `VERSION` atualizada automaticamente (PATCH +1)
- 🚫 Hook força atualização da versão mesmo se desenvolvedor esquecer
- ✅ Detecção inteligente: se VERSION já foi manualmente atualizado, não incrementa novamente
- 👤 Todos os commits automaticamente atribuídos a @Maxwbh (Maxwell da Silva Oliveira)
- 🔐 Configuração de autor e committer em TODOS os commits via hook

**Como Funciona**
1. Desenvolvedor faz alterações e executa `git commit`
2. Pre-commit hook intercepta o commit ANTES de ser criado
3. Hook lê versão atual do arquivo `VERSION` (ex: 1.1.2)
4. Hook incrementa PATCH automaticamente (1.1.2 → 1.1.3)
5. Hook atualiza arquivo `VERSION` com nova versão
6. Hook adiciona `VERSION` ao staging automaticamente
7. Hook configura autor como Maxwell da Silva Oliveira
8. Commit é criado com versão atualizada e autor correto

**Detecção Inteligente de Atualização Manual**
- Se desenvolvedor já atualizou `VERSION` manualmente (arquivo staged), hook NÃO incrementa
- Evita dupla incrementação (1.1.2 → 1.1.4 indevidamente)
- Mensagem clara no console: "VERSION file already staged (manual update detected)"
- Perfeito para releases MAJOR ou MINOR onde dev quer controle total

**Configuração Git Automática**
- `core.hooksPath` configurado para `.githooks/` (hooks customizados)
- `user.name` definido como "Maxwell da Silva Oliveira"
- `user.email` definido como "maxwbh@gmail.com"
- Configurações aplicadas no repositório local

**Benefícios**
- 🎯 ZERO esquecimentos de atualização de versão
- 📈 Histórico de versões sempre correto e rastreável
- 👥 Atribuição consistente de commits
- 🔄 Workflow Git simplificado (sem passos manuais)
- 📊 Cada commit = incremento de versão (changelog preciso)
- 🚀 Ideal para deploys automáticos baseados em versão

**Transparência**
- Hook exibe mensagens claras durante execução:
  - "📦 Current version: X.Y.Z"
  - "✅ Version auto-incremented: X.Y.Z → X.Y.Z+1"
  - "👤 Commit author: Maxwell da Silva Oliveira"
  - "✅ Pre-commit hook completed successfully"

### Arquivos Adicionados
- `.githooks/pre-commit`: Pre-commit hook executável com lógica de auto-versionamento

### Arquivos Configurados
- Git configurado para usar `.githooks/` ao invés de `.git/hooks/`
- Autor padrão configurado no repositório

### Segurança
- Hook não pode ser ignorado acidentalmente (configurado via core.hooksPath)
- Desenvolvedor ainda pode usar `--no-verify` se necessário (casos excepcionais)
- Arquivo VERSION sempre em sync com commits

### Versionamento
- Incremento automático apenas em PATCH (terceiro número)
- Para MAJOR ou MINOR: desenvolvedor atualiza VERSION manualmente antes do commit
- Semantic Versioning totalmente respeitado

### Compatibilidade
- Bash script compatível com Linux, macOS e Windows (Git Bash)
- Requer Git 2.9+ para core.hooksPath
- Hook testado e funcional em ambiente Linux

### Requisitos para Desenvolvedores
- Nenhum! Sistema totalmente automático
- (Opcional) Para releases MAJOR/MINOR: atualizar VERSION manualmente antes do commit

## [1.1.2] - 2025-12-30

### Adicionado - Auto-criação de GitHub Issues para Falhas de Scraping/Extração

**Funcionalidade Inteligente**
- 🤖 Sistema automatico diferencia entre erros de rede e falhas de scraping
- ✅ **Erros de rede/HTTP (404, 500, timeout)**: Apenas informa o usuario (comportamento normal)
- 🐛 **Falhas de scraping/parsing**: Cria issue automatica no GitHub para investigacao
- 📊 Deteccao inteligente de quando site esta acessivel mas dados nao podem ser extraidos
- 🔍 Indicador claro de qual dado falhou: Titulo, Preco ou Imagem

**Quando GitHub Issues SÃO Criadas**
- Site acessivel (200 OK) MAS titulo nao pode ser extraido
- Site acessivel MAS estrutura HTML nao reconhecida
- Site novo/desconhecido que precisa de scraper especifico
- Site conhecido que mudou estrutura HTML
- Template de extracao precisa ser atualizado

**Quando GitHub Issues NÃO SÃO Criadas**
- Erro 404 (pagina nao encontrada)
- Erro 500 (erro interno do servidor)
- Timeout de conexao
- Erro de DNS/conexao
- Site fora do ar temporariamente
- Qualquer erro de rede/HTTP

**Dados Incluidos na Issue de Scraping**
- URL completa do produto
- Dominio detectado
- Quais dados falharam (Titulo, Preco, Imagem)
- Dados extraidos parcialmente (se houver)
- Usuario que tentou adicionar
- Grupo ao qual pertence
- Data e hora da tentativa
- Sugestoes de acoes para resolver
- Como reproduzir o erro

**Labels Dinamicas nas Issues**
- `auto-generated`: Issue criada automaticamente
- `enhancement`: Melhoria no sistema de scraping
- `scraping`: Relacionado a extracao de dados
- `needs-triage`: Precisa ser revisada
- `extracao-titulo`: Se titulo nao foi extraido
- `extracao-preco`: Se preco nao foi extraido
- `extracao-imagem`: Se imagem nao foi extraida

### Arquivos Adicionados
- **Excecoes customizadas em `scrapers.py`**:
  - `ScrapingError`: Excecao base para erros de scraping
  - `NetworkError`: Erros de rede/HTTP (NAO gera issue)
  - `ParsingError`: Erros de parsing/extracao (GERA issue)

### Arquivos Modificados
- `presentes/github_helper.py`:
  - Nova funcao `criar_issue_falha_scraping()`: Cria issues especificas para falhas de scraping
  - Analisa quais dados falharam e gera labels dinamicas
  - Corpo da issue com sugestoes de resolucao

- `presentes/scrapers.py`:
  - `BaseScraper.get_soup()`: Lanca `NetworkError` para erros HTTP/rede
  - `AmazonScraper.extract()`: Lanca `ParsingError` se titulo nao extraido
  - `MercadoLivreScraper.extract()`: Lanca `ParsingError` se titulo nao extraido
  - `KabumScraper.extract()`: Lanca `ParsingError` se titulo nao extraido
  - `GenericScraper.extract()`: Lanca `ParsingError` se titulo nao extraido
  - `ScraperFactory.extract_product_info()`: Retorna dict com tipo de erro e dados parciais

- `presentes/views.py`:
  - `extrair_info_produto_view()`: Diferencia erros de rede vs parsing
  - Cria issue automatica apenas para falhas de parsing
  - Retorna mensagem clara com link para issue criada

### Comportamento
- **Erro de rede**: Usuario ve mensagem "Nao foi possivel acessar o site: [erro]"
- **Erro de parsing**: Usuario ve "Nao foi possivel extrair as informacoes desta pagina. Uma issue #123 foi criada automaticamente para investigacao."
- **Transparencia total**: Link direto para issue criada no GitHub

### Beneficios
- 🎯 Identificacao automatica de sites que precisam de suporte
- 📈 Rastreamento de falhas de scraping para melhoria continua
- 🔧 Dados suficientes para desenvolvedores implementarem solucoes
- 👥 Usuarios sabem que problema esta sendo investigado
- ⚡ Nao gera ruido com erros temporarios de rede

### Performance
- Operacao nao-bloqueante: falha na criacao de issue nao afeta usuario
- Timeout de 10 segundos em requisicoes ao GitHub
- Deteccao rapida de tipo de erro

### UX (User Experience)
- Mensagens claras e distintas para cada tipo de erro
- Link direto para acompanhar investigacao
- Sistema continua funcionando normalmente (preenchimento manual)
- Feedback automatico sobre problemas de scraping

## [1.1.1] - 2025-12-30

### Adicionado - Auto-criação de GitHub Issues para Falhas de Download de Imagem

**Funcionalidade Automatica**
- 🤖 Sistema automatico de criacao de issues no GitHub quando imagens de presentes nao podem ser carregadas
- ⚠️ Presente e salvo normalmente (sem imagem) mesmo quando download falha
- 📋 Issue criada automaticamente com todos os detalhes do presente
- 🔔 Usuario recebe notificacao com link direto para a issue criada no GitHub
- 🏷️ Issues automaticamente marcadas com labels: `auto-generated`, `bug`, `imagem`, `needs-triage`

**Dados Incluidos na Issue Automatica**
- ID do presente
- Descricao completa
- Preco (se informado)
- URL do produto (se informado)
- URL da imagem que falhou ao carregar
- Usuario que tentou adicionar o presente
- Grupo ao qual o presente pertence
- Data e hora da tentativa
- Status do presente
- Descricao detalhada do erro
- Link direto para o presente no sistema
- Checklist de acoes sugeridas para resolucao
- Versao do aplicativo

**Configuracao**
- Requer variaveis de ambiente:
  - `GITHUB_TOKEN`: Personal Access Token do GitHub (permissoes de repo)
  - `GITHUB_REPO_OWNER`: Dono do repositorio (default: Maxwbh)
  - `GITHUB_REPO_NAME`: Nome do repositorio (default: Lista_de_Presentes)
  - `GITHUB_AUTO_CREATE_ISSUES`: True/False para habilitar/desabilitar (default: True)
  - `SITE_URL`: URL base do site para links nas issues
- Funcionalidade pode ser desabilitada sem afetar o funcionamento do app
- Falhas na criacao de issues nao impedem a criacao do presente

### Arquivos Adicionados
- `presentes/github_helper.py`: Modulo de integracao com GitHub API
  - `criar_issue_falha_imagem()`: Criacao de issues para falhas de imagem
  - `criar_issue_erro_geral()`: Criacao de issues genericas
  - `_get_app_version()`: Helper para incluir versao nas issues

### Arquivos Alterados
- `lista_presentes/settings.py`: Configuracoes de integracao com GitHub
- `presentes/views.py`: `adicionar_presente_view()` atualizada para chamar criacao de issues

### Seguranca
- Token de acesso armazenado em variavel de ambiente (nunca no codigo)
- Timeout de 10 segundos em requisicoes ao GitHub (nao bloqueia o app)
- Tratamento de erros completo (rede, autenticacao, API)
- Logging detalhado de todas as operacoes

### Performance
- Operacao nao-bloqueante: falhas nao afetam criacao do presente
- Timeout configurado para evitar travamentos
- Requisicoes assincronas via requests

### UX (User Experience)
- Usuario informado claramente quando imagem nao pode ser carregada
- Link direto para issue criada (transparencia)
- Presente continua funcional mesmo sem imagem
- Processo transparente e automatico

## [1.1.0] - 2025-12-11

### NOVO RECURSO PRINCIPAL: Sistema de Grupos

#### Funcionalidades Implementadas

**1. Criacao e Gerenciamento de Grupos**
- Qualquer usuario autenticado pode criar um novo grupo
- Criador automaticamente se torna Mantenedor (administrador) do grupo
- Grupos possuem: nome, descricao opcional, e imagem opcional
- Cada grupo gera automaticamente um link de convite unico e permanente
- Suporte a imagens de grupo via URL (mesmo sistema dos presentes)

**2. Sistema de Convite**
- Link de convite exclusivo por grupo (formato: /grupos/convite/{codigo}/)
- Usuarios clicam no link e sao adicionados automaticamente ao grupo
- Login obrigatorio antes de entrar no grupo (redirect automatico)
- Verificacao para evitar duplicatas

**3. Selecao de Grupo Ativo**
- TODO usuario DEVE selecionar um "Grupo Ativo" para usar o aplicativo
- Troca rapida de grupo a qualquer momento
- Sistema lembra o ultimo grupo ativo do usuario
- Bloqueio de acesso ao conteudo sem grupo ativo selecionado

**4. Filtragem Global por Grupo - 100% DOS DADOS**
- TODOS os dados sao filtrados pelo Grupo Ativo selecionado:
  - Lista de usuarios (apenas membros do grupo)
  - Presentes (do grupo ativo)
  - Compras realizadas (do grupo)
  - Notificacoes (do grupo)
  - Sugestoes de precos (do grupo)
  - Dashboard (estatisticas do grupo)
- Impossivel visualizar ou interagir com dados de outros grupos

**5. Gerenciamento de Membros**
- Listar todos os membros do grupo
- Remover membros (apenas mantenedores)
- Promover/Rebaixar mantenedores (apenas mantenedores)
- Usuarios podem sair do grupo voluntariamente
- Protecao: ultimo mantenedor nao pode sair sem promover outro
- Remocao automatica do grupo ativo se usuario for removido

**6. Permissoes e Regras**
- Mantenedor: pode editar grupo, gerenciar membros, ativar/desativar grupo
- Membro comum: apenas visualizacao, sem permissoes de alteracao
- Mantenedores podem promover outros membros a mantenedor
- Grupos desativados nao aceitam novos membros

### Adicionado

#### Models (Database)
- Grupo: nome, descricao, codigo_convite (unico), ativo, data_criacao, imagens
- GrupoMembro: relacionamento grupo-usuario com permissoes (e_mantenedor)
- Usuario.grupo_ativo: ForeignKey para Grupo (grupo atualmente selecionado)
- Todos os models principais agora tem campo grupo:
  - Presente.grupo
  - Compra.grupo
  - Notificacao.grupo
  - SugestaoCompra.grupo
- Indexes otimizados para queries por grupo

#### Views
- grupos_lista_view: Lista grupos do usuario e permite selecao
- criar_grupo_view: Criacao de novos grupos
- editar_grupo_view: Edicao de grupos (apenas mantenedores)
- ativar_grupo_view: Define grupo ativo do usuario
- gerenciar_membros_view: Gestao de membros do grupo
- remover_membro_view: Remove membro do grupo
- toggle_mantenedor_view: Alterna status de mantenedor
- toggle_ativo_grupo_view: Ativa/desativa grupo
- sair_grupo_view: Usuario sai do grupo
- convite_grupo_view: Aceita convite via link
- servir_imagem_grupo_view: Serve imagens dos grupos

#### Decorator
- @requer_grupo_ativo: Decorator que forca selecao de grupo ativo
- Aplicado a TODAS as views principais do aplicativo
- Redireciona para selecao de grupo se usuario nao tiver grupo ativo

#### Forms
- GrupoForm: Formulario para criacao/edicao de grupos

#### Admin
- GrupoAdmin: Interface admin para grupos
- GrupoMembroAdmin: Interface admin para membros
- UsuarioAdmin atualizado com campo grupo_ativo

### Alterado

#### Views Existentes - Filtragem por Grupo
Todas as views principais foram atualizadas para filtrar por grupo ativo:
- dashboard_view, meus_presentes_view, adicionar_presente_view
- editar_presente_view, deletar_presente_view, buscar_sugestoes_ia_view
- ver_sugestoes_view, lista_usuarios_view (APENAS membros do grupo ativo)
- presentes_usuario_view, marcar_comprado_view, notificacoes_view
- notificacoes_nao_lidas_json

#### Services
- IAService.buscar_sugestoes_reais: Sugestoes agora incluem grupo
- Todas as criacoes de SugestaoCompra agora incluem o campo grupo

### Seguranca
- Isolamento completo de dados entre grupos
- Verificacao de permissoes em todas as operacoes
- Impossivel acessar dados de grupos aos quais o usuario nao pertence
- Mantenedores nao podem se auto-remover se forem os ultimos
- Links de convite unicos e permanentes (secrets.token_urlsafe)

### Banco de Dados
- 3 novas tabelas: Grupo, GrupoMembro, e campo grupo_ativo em Usuario
- 4 campos grupo adicionados: Presente, Compra, Notificacao, SugestaoCompra
- Multiplos indexes criados para otimizacao de queries
- MIGRACAO NECESSARIA: Execute `python manage.py makemigrations` e `python manage.py migrate`

### Performance
- Queries otimizadas com select_related e prefetch_related
- Indexes em todos os campos grupo para filtragem rapida
- Uso de select_for_update em operacoes criticas (compra de presentes)

### BREAKING CHANGES
- Dados existentes: Presentes, Compras, Notificacoes e Sugestoes existentes terao grupo=NULL apos migracao
- Usuarios: Precisarao criar ou entrar em um grupo para continuar usando o aplicativo
- Acesso obrigatorio: Todas as views principais agora requerem grupo ativo

### Migration Path
1. Executar migrations: `python manage.py makemigrations && python manage.py migrate`
2. Criar um grupo padrao (opcional): via admin ou interface
3. Associar dados existentes a um grupo (via admin ou script de migracao)
4. Usuarios devem criar/entrar em grupos na proxima visita

## [1.0.5] - 2025-11-29

### Corrigido - CRÍTICO
- 🔴 Contraste de campos de formulário no tema claro (ILEGÍVEIS antes desta correção)
- 📝 `.form-control` e `.form-select` agora usam fundo branco (0.8 opacity) com texto escuro
- 📝 Placeholders com cor cinza adequada (rgba(108, 117, 125, 0.7))
- 🏷️ Labels (`.form-label`) com cor escura (#2c3e50) e negrito - eliminado text-shadow
- 💬 Modais (`.modal-content`, `.modal-body`) com texto escuro no tema claro
- 💬 `.modal-header` e `.modal-footer` com backgrounds verdes claros
- ⚠️ Alerts com backgrounds opacos (0.95) e cores escuras no tema claro
  - success: #155724 em fundo verde claro
  - danger: #721c24 em fundo vermelho claro
  - info: #0c5460 em fundo azul claro
  - warning: #856404 em fundo amarelo claro

### Alterado
- 🎨 Todos os elementos de formulário agora diferenciam tema claro vs escuro
- 🎨 Forms no claro: background branco opaco, bordas verdes, texto escuro
- 🎨 Forms no escuro: background translúcido, bordas douradas, texto claro
- 🎨 Modais no claro: background quase opaco (0.95), texto escuro
- 🎨 Modais no escuro: background translúcido, texto claro (mantido)
- ⚠️ Alerts com font-weight 500 para melhor legibilidade

### Acessibilidade
- ✅ Razão de contraste WCAG AAA alcançada em campos de formulário
- ✅ Labels totalmente legíveis sem sombras
- ✅ Placeholders com contraste adequado
- ✅ Modais completamente legíveis
- ✅ Alerts com alto contraste

### Problema Reportado
**Usuário**: "O contraste dos campos de digitação está ilegível, tudo com tom branco sem contraste para leitura. (Opcional) label com sombra, difícil leitura"

**Causa**: Estilos de formulário estavam configurados apenas para tema escuro (texto branco em todos os temas)

**Solução**: Separação completa de estilos por tema com alto contraste

## [1.0.4] - 2025-11-29

### Corrigido
- 🎨 Contraste de texto no tema claro melhorado drasticamente
- 🎨 Background do tema claro agora usa gradiente verde claro (ao invés de escuro)
- 📝 Texto em `.usuario-stats-inline` agora usa cor escura (#2c3e50) com background glassmorphism
- 📝 Headings (h1-h6) agora usam verde escuro no tema claro (melhor legibilidade)
- 📝 `.card-body` e `.card-text` com cores escuras no tema claro
- 📝 `.text-muted` com contraste adequado em ambos os temas
- 🔗 Links com cores apropriadas para cada tema
- 🌈 Flocos de neve visíveis em ambos os temas

### Alterado
- 🎨 Glassmorphism agora diferencia tema claro vs escuro
- 🎨 Background claro: gradiente verde suave (#e8f5e9 → #a5d6a7)
- 🎨 Background escuro: gradiente verde escuro (mantido)
- 📱 Stats inline com background glassmorphism sutil para melhor legibilidade

### Acessibilidade
- ✅ Razão de contraste WCAG AA alcançada no tema claro
- ✅ Textos legíveis em fundos glassmorphism
- ✅ Ícones com cores destacadas (--christmas-green-light)

## [1.0.3] - 2025-11-29

### Adicionado
- 🐳 Docker Compose File Watch para hot-reload automático
- 📦 Configuração Docker otimizada para recursos mínimos (512MB-1GB RAM)
- 🔹 `docker-compose.minimal.yml` - PostgreSQL otimizado
- 🔹 `docker-compose.sqlite.yml` - Ultra leve com SQLite (~300MB RAM)
- 🔹 `Dockerfile.minimal` - Imagem Alpine (~150MB vs ~900MB)
- 📚 `DOCKER-MINIMAL.md` - Documentação para ambientes com poucos recursos
- 📚 `docs/deployment/docker.md` - Guia completo Docker
- 🎯 Suporte a variável `USE_SQLITE` para forçar SQLite
- ⚙️ PostgreSQL com configurações de memória mínima (256MB)
- 🔄 Sync automático de código, templates e static files

### Alterado
- 🔧 `docker-compose.yml` atualizado com seção `develop.watch`
- 🔧 `docker-compose.dev.yml` otimizado para desenvolvimento
- 🗃️ `settings.py` com suporte explícito a `USE_SQLITE`
- 📝 `DOCKER.md` expandido com comandos e troubleshooting
- ⚡ Gunicorn configurado com `--reload` para hot-reload

### Corrigido
- 🐛 Encoding UTF-8 em `lista_presentes/__init__.py`
- 🔧 Branch corrigida no `render.yaml`

### Performance
- ⚡ Uso de RAM reduzido em 60% (ultra leve)
- ⚡ Tamanho da imagem Docker reduzido em 83% (Alpine)
- ⚡ Hot-reload em ~2 segundos (vs rebuild manual de 2-3 minutos)

## [1.0.2] - 2025-11-29

### Adicionado
- ✨ Tema Glassmorphism com tons de verde natalino
- 🎨 Efeitos de vidro fosco translúcido com `backdrop-filter: blur()`
- ❄️ Animações de flocos de neve caindo
- ✨ Estrelas piscantes no background
- 🎄 Ornamentos decorativos animados (árvore, presente, sino, estrela)
- 🎨 Paleta de cores verde natalino + dourado
- 🔄 Background gradiente animado
- 🎁 Efeito de partículas mágicas ao clicar em botões
- 📦 Sistema de versionamento profissional (VERSION file + `__version__`)
- 📚 CHANGELOG.md seguindo padrão Keep a Changelog
- 📦 Suporte para instalação via PIP (setup.py + pyproject.toml)
- 🚀 Configuração aprimorada para deployment no Render
- 📖 CONTRIBUTING.md com guia de contribuição
- 🌐 Suporte para `prefers-reduced-motion` (acessibilidade)

### Alterado
- 🎨 Tema claro atualizado com efeitos glassmorphism
- 🌙 Tema escuro aprimorado com glassmorphism e blur
- 📱 Cards, navbar, modais e formulários com efeito de vidro
- 🔄 Transições suaves aprimoradas entre temas
- 📝 README.md expandido com informações sobre instalação via PIP
- 🎯 Configuração do git author para @maxwbh
- 📦 Metadados do projeto atualizados

### Corrigido
- 🐛 Compatibilidade de cores entre modo claro e escuro
- 🎨 Contraste de texto em elementos glassmorphism
- 📱 Responsividade em dispositivos móveis

## [1.0.1] - 2025-11-28

### Adicionado
- 🔑 Sistema de recuperação de senha
- 📧 Fluxo completo de reset de senha via email
- 🎨 Melhorias de UX em formulários
- ⚡ Validações aprimoradas de entrada de dados

### Alterado
- 🔒 Segurança aprimorada em autenticação
- 📝 Mensagens de erro mais claras
- 🎨 Layout de formulários melhorado

### Corrigido
- 🐛 Bug em validação de email
- 🔧 Correção em redirecionamentos após login

## [1.0.0] - 2025-11-20

### Adicionado - Lançamento Inicial
- 🎁 Sistema completo de gerenciamento de listas de presentes
- 👥 Autenticação e registro de usuários
- 🎄 CRUD completo de presentes (Create, Read, Update, Delete)
- 🛒 Sistema de compra de presentes
- 🔔 Notificações em tempo real
- 💰 Busca e comparação de preços automática
- 🔍 Filtros avançados (preço, usuário, status)
- 📊 Dashboard com estatísticas
- 🎨 Temas claro e escuro
- 📱 Progressive Web App (PWA) - instalável
- 🔄 Service Worker para funcionamento offline
- 🌐 Auto-extração de produtos via URL
- 🏪 Integração com lojas (Amazon, Mercado Livre, Kabum)
- 🤖 Sugestões de compra com IA (Claude, ChatGPT, Gemini)
- 🖼️ Upload e armazenamento de imagens em base64
- 🎯 Sistema de notificações com badge
- 📈 Keep-Alive automático com GitHub Actions
- 🐳 Suporte para Docker
- 🚀 Deploy automático no Render.com
- 📚 Documentação completa e profissional
- 🧪 Comando para popular dados de teste
- 🔐 Segurança: CSRF, XSS, SQL injection protection
- ⚡ Otimizações de performance (índices, paginação, cache)
- 🌍 Interface em Português (pt-BR)
- 📱 Design responsivo (mobile-first)
- ♿ Acessibilidade (ARIA labels, navegação por teclado)

### Tecnologias Utilizadas
- **Backend**: Django 5.0, Python 3.11+
- **Banco de Dados**: PostgreSQL 15+ / SQLite (dev)
- **Frontend**: Bootstrap 5.3, JavaScript ES6+
- **APIs**: Anthropic Claude AI, OpenAI ChatGPT, Google Gemini
- **Web Scraping**: BeautifulSoup4
- **Imagens**: Pillow
- **Servidor**: Gunicorn
- **Arquivos Estáticos**: WhiteNoise
- **PWA**: django-pwa, Service Workers
- **Deploy**: Render.com, Docker

## Como Contribuir

Leia nosso [CONTRIBUTING.md](CONTRIBUTING.md) para saber como contribuir com este projeto.

## Versionamento

Este projeto usa [Semantic Versioning](https://semver.org/lang/pt-BR/):
- **MAJOR**: Mudanças incompatíveis na API
- **MINOR**: Novas funcionalidades (compatíveis)
- **PATCH**: Correções de bugs

## Autor

**Maxwell da Silva Oliveira**
- 💼 Empresa: M&S do Brasil LTDA
- 📧 Email: maxwbh@gmail.com
- 💻 GitHub: [@Maxwbh](https://github.com/Maxwbh)
- 💼 LinkedIn: [linkedin.com/in/maxwbh](https://www.linkedin.com/in/maxwbh)

---

**Legenda de Emojis:**
- ✨ Novo recurso
- 🎨 Melhorias de UI/UX
- 🐛 Correção de bug
- 🔒 Segurança
- ⚡ Performance
- 📝 Documentação
- 🔧 Configuração
- 🚀 Deploy
- 📦 Dependências
- ♿ Acessibilidade
