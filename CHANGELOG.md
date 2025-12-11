# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

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
