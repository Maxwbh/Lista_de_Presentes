# 🛠️ Instalação, configuração e operação

Guia técnico da **Lista de Presentes**: instalação local, configuração, testes, comandos de manutenção e solução de problemas. Para conhecer o projeto, veja o [README](../../README.md). Deploy: [RENDER.md](../deployment/RENDER.md) · Docker: [DOCKER.md](../deployment/DOCKER.md) · Banco: [SUPABASE.md](../database/SUPABASE.md).

---

## 📋 Pré-requisitos

- Python 3.11 ou 3.12 (versões testadas no CI)
- Git
- Opcional: PostgreSQL 15+ (sem ele, o app usa SQLite)
- Opcional: Node.js/npm, só para recompilar o CSS (Tailwind)

Stack: Django 5.1.9, Tailwind CSS 3 + daisyUI 4, WhiteNoise, Gunicorn. Dependências em [`requirements.txt`](../../requirements.txt).

---

## 🚀 Instalação local

```bash
# 1. Clonar
git clone https://github.com/Maxwbh/Lista_de_Presentes.git
cd Lista_de_Presentes

# 2. Ambiente virtual
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 3. Dependências
pip install -r requirements.txt

# 4. Variáveis de ambiente
cp .env.example .env              # edite conforme a seção "Variáveis de ambiente"

# 5. Banco e admin
python manage.py migrate
python manage.py createsuperuser

# 6. (Opcional) Dados de teste
python manage.py populate_test_data --users 5 --gifts-per-user 5

# 7. Servidor
python manage.py runserver
```

Acesse [http://localhost:8000](http://localhost:8000) e o admin em [http://localhost:8000/admin/](http://localhost:8000/admin/).

O `populate_test_data` cria usuários, grupos, presentes, sugestões, histórico de preços, compras e notificações. Todos os usuários de teste têm a senha `senha123`.

Para gerar uma `SECRET_KEY`:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## 🗄️ Banco de dados

A escolha é feita em `lista_presentes/settings.py`:

| Situação | Banco usado |
|----------|-------------|
| Sem `DATABASE_URL` | SQLite em `db.sqlite3` (raiz do projeto) |
| `USE_SQLITE=True` | SQLite em `data/db.sqlite3` (crie a pasta `data/` antes) |
| `DATABASE_URL=postgresql://...` | PostgreSQL |

No PostgreSQL o app usa **somente** o schema `lista_presentes` (o `search_path` é forçado no `settings.py` e no signal `connection_created` de `presentes/apps.py`). O schema precisa existir antes do `migrate`:

```bash
createdb lista_presentes
export DATABASE_URL=postgresql://usuario:senha@localhost:5432/lista_presentes
python scripts/ensure_schema.py    # cria o schema lista_presentes (idempotente)
python manage.py migrate
```

Detalhes do schema isolado: [SCHEMA_ISOLADO.md](../database/SCHEMA_ISOLADO.md).

---

## 🎨 Frontend (Tailwind CSS + daisyUI)

O CSS compilado (`theme/static/css/dist/styles.css`) está no repositório, então o app roda sem Node. Ao alterar classes nos templates ou `theme/static_src/tailwind.config.js`, recompile:

```bash
cd theme/static_src
npm install
npm run build      # ou: npm run dev (modo watch)
```

- Tema padrão: `emerald_light` (definido em `templates/base.html`; os temas ficam em `tailwind.config.js`).
- As cores dos temas do daisyUI 4 são OKLCH: em CSS próprio use `oklch(var(--p))`, não `hsl(var(--p))`.
- No deploy, o `build.sh` recompila o CSS e roda o `collectstatic`.

Mais sobre temas: [TEMAS.md](../features/TEMAS.md).

---

## ⚙️ Variáveis de ambiente

Todas são lidas em `lista_presentes/settings.py` (o `.env` é carregado com `python-dotenv`). Modelo: [`.env.example`](../../.env.example).

### Django e banco

| Variável | Padrão | Observação |
|----------|--------|------------|
| `SECRET_KEY` | chave insegura de desenvolvimento | **Obrigatória em produção** |
| `DEBUG` | `True` | Use `False` em produção (ativa cookies seguros e HSTS) |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Separados por vírgula |
| `DATABASE_URL` | — | PostgreSQL; sem ela usa SQLite |
| `USE_SQLITE` | `False` | Força SQLite mesmo com `DATABASE_URL` |
| `SITE_URL` | `http://localhost:8000` | URL pública, usada em links (issues, e-mails, callback do Mercado Livre) |
| `SUPABASE_URL`, `SUPABASE_KEY` | vazio | Opcionais, não usadas pelo Django hoje |

### Integrações

| Variável | Uso |
|----------|-----|
| `GEMINI_API_KEY`, `GEMINI_MODEL` (padrão `gemini-2.5-flash`) | IA principal das sugestões |
| `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL`, `OPENAI_API_KEY`, `OPENAI_MODEL` | IAs alternativas (fallback) |
| `BREVO_API_KEY`, `DEFAULT_FROM_EMAIL` | E-mail pela API HTTP da Brevo (o Render Free bloqueia SMTP). O remetente precisa estar verificado na Brevo |
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS` | SMTP comum, usado só se `BREVO_API_KEY` estiver vazia. Sem nenhum dos dois, os e-mails vão para o log |
| `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`, `VAPID_ADMIN_EMAIL` | Notificações push. Gere com `python manage.py gerar_chaves_vapid` |
| `MERCADOLIVRE_CLIENT_ID`, `MERCADOLIVRE_CLIENT_SECRET` | API do Mercado Livre. Redirect URI do app: `{SITE_URL}/integracoes/mercadolivre/callback/` |
| `GITHUB_TOKEN`, `GITHUB_REPO_OWNER`, `GITHUB_REPO_NAME`, `GITHUB_AUTO_CREATE_ISSUES` | Criação automática de issues para falhas de download de imagem |
| `CRON_TOKEN` | Protege `/api/cron/pesquisar-precos/` e `/api/acessos/resumo/` (header `X-Cron-Token`). Mesmo valor no servidor e no secret do GitHub |
| `GOOGLE_CLIENT_ID/SECRET`, `FACEBOOK_APP_ID/SECRET`, `LINKEDIN_CLIENT_ID/SECRET`, `APPLE_CLIENT_ID`, `APPLE_CLIENT_SECRET`, `APPLE_KEY_ID`, `APPLE_PRIVATE_KEY` | Login social ([SOCIAL_LOGIN_CONFIG.md](../features/SOCIAL_LOGIN_CONFIG.md)) |

### Admin automático e servidor

| Variável | Uso |
|----------|-----|
| `DJANGO_SUPERUSER_EMAIL`, `DJANGO_SUPERUSER_PASSWORD` | Usadas pelo `python manage.py fix_admin` (rodado no `build.sh` e no `entrypoint.sh`) |
| `RESET_ADMIN_PASSWORD` | `true` força o `fix_admin` a redefinir a senha de um admin existente |
| `WEB_CONCURRENCY`, `GUNICORN_THREADS`, `GUNICORN_TIMEOUT`, `MAX_REQUESTS`, `PORT` | Lidas pelo `gunicorn.conf.py` (padrão: 1 worker, 4 threads, 120 s) |

---

## 📂 Estrutura do projeto

```
Lista_de_Presentes/
├── lista_presentes/        # Projeto Django (settings, urls, wsgi)
├── presentes/              # App principal
│   ├── models.py, views.py, forms.py, urls.py, admin.py, tests.py
│   ├── scrapers.py         # Scrapers por loja (dados do produto pela URL)
│   ├── mercadolivre_api.py # API oficial do Mercado Livre
│   ├── precos.py           # Conversão de preços lidos (sites, APIs, IA) para número
│   ├── pesquisa_precos.py  # Pesquisa semanal de preços (middleware + cron)
│   ├── services.py         # IAService (Gemini, Claude, ChatGPT)
│   ├── github_helper.py    # Issues automáticas no GitHub
│   ├── acessos.py          # Registro de acessos e despertares do servidor
│   ├── emails.py, email_backend.py  # E-mails e backend da Brevo
│   ├── push.py             # Web Push (VAPID)
│   ├── senha.py            # Links de redefinição de senha
│   ├── context_processors.py, adapters.py, templatetags/
│   ├── migrations/
│   └── management/commands/
├── templates/              # base.html, presentes/, emails/, admin/, 404/500
├── theme/                  # Tailwind + daisyUI (static_src/ → static/css/dist/)
├── static/                 # Ícones, JS e CSS extras
├── scripts/                # ensure_schema.py, check_database_config.py, SQL do Supabase
├── docs/                   # Documentação
├── .github/workflows/      # CI, keep-alive, pesquisa de preços, relatório de acessos
├── build.sh                # Build do Render
├── render.yaml             # Blueprint do Render
├── gunicorn.conf.py        # Configuração do Gunicorn
├── Dockerfile, docker-compose*.yml, entrypoint.sh
├── VERSION, version.py     # Versão (ver VERSIONAMENTO.md)
└── requirements.txt
```

---

## 🧪 Testes e CI

```bash
python manage.py test presentes            # testes do app
coverage run --source='.' manage.py test   # com cobertura (pip install coverage)
coverage report
```

O workflow [`tests.yml`](../../.github/workflows/tests.yml) roda em push e PR para `main`:

- Testes em Python 3.11 e 3.12 com PostgreSQL 15, cobertura e checagem de migrações pendentes (`makemigrations --check`).
- Lint: flake8 (erros de sintaxe/nomes indefinidos), black e isort, em modo informativo (`continue-on-error`).
- Segurança: safety e bandit, também informativos.

---

## ⏰ Workflows agendados

| Workflow | Quando | O que faz |
|----------|--------|-----------|
| [`keep-alive.yml`](../../.github/workflows/keep-alive.yml) | A cada 14 min, só em horas de uso definidas por dia da semana | Ping em `/health/` para o Render Free não dormir nesses horários |
| [`pesquisa-precos.yml`](../../.github/workflows/pesquisa-precos.yml) | Segunda, 08:00 UTC, ou manual | `POST /api/cron/pesquisar-precos/` com `X-Cron-Token` |
| [`relatorio-acessos.yml`](../../.github/workflows/relatorio-acessos.yml) | Só manual | `GET /api/acessos/resumo/` com `X-Cron-Token`; usado para revisar as horas do keep-alive |

Requisitos: secret `CRON_TOKEN` no repositório (mesmo valor do servidor) e, opcionalmente, a variável de repositório `RENDER_URL` (padrão `https://lista-presentes-im4b.onrender.com`).

> ⚠️ Em repositório público, o GitHub desativa workflows agendados após 60 dias sem atividade no repositório. Para reativar: **Actions → workflow → Enable workflow** (ou Disable/Enable).

Detalhes do Render Free (750 h/mês, sleep após 15 min) em [RENDER.md](../deployment/RENDER.md#-keep-alive-e-tarefas-agendadas).

---

## 🗂️ Comandos de gerenciamento

| Comando | Função |
|---------|--------|
| `populate_test_data [--users N] [--gifts-per-user N]` | Dados de teste |
| `fix_admin` | Cria/promove o superusuário de `DJANGO_SUPERUSER_EMAIL` |
| `gerar_chaves_vapid` | Gera as chaves VAPID para push |
| `testar_push` | Envia push de teste |
| `pesquisar_precos` | Pesquisa de preços (mesma rotina do endpoint de cron) |
| `analisar_acessos [--dias 30]` | Acessos por hora e sugestão de cron do keep-alive |
| `validar_social` | Verifica a configuração do login social |
| `criar_grupo_padrao`, `migrar_dados_para_grupo` | Setup de grupos ([SETUP_GRUPOS.md](../features/SETUP_GRUPOS.md)) |
| `migrate_images_to_base64` | Migra imagens para base64 ([MIGRACAO_IMAGENS_BASE64.md](../database/MIGRACAO_IMAGENS_BASE64.md)) |
| `limpar_historico_precos` | Limpa o histórico de preços |
| `fix_migration_history`, `force_migrate` | Recuperação de migrações ([migrations.md](../database/migrations.md)) |

Uso: `python manage.py <comando>`. Veja as opções com `python manage.py <comando> --help`.

---

## 🐛 Solução de problemas

- **`no schema has been selected to create in`** (PostgreSQL): o schema `lista_presentes` não existe. Rode `python scripts/ensure_schema.py`.
- **`unable to open database file`** com `USE_SQLITE=True`: crie a pasta `data/`.
- **Diagnóstico do banco:** `python scripts/check_database_config.py`.
- **CSS antigo depois de mudar templates:** recompile o Tailwind (`npm run build` em `theme/static_src`).
- **Erro 500 em produção:** [DEBUG_500_ERRORS.md](DEBUG_500_ERRORS.md).
- **Problemas no Render:** [RENDER.md](../deployment/RENDER.md#-solução-de-problemas).

---

## 📱 PWA

O app pode ser instalado (manifest e service worker via `django-pwa`):

- **Android (Chrome):** Menu → "Instalar app".
- **iOS (Safari):** Compartilhar → "Adicionar à Tela Inicial".
- **Desktop (Chrome/Edge):** ícone de instalação na barra de endereços.

---

## 🔐 Segurança

Com `DEBUG=False`, o `settings.py` ativa cookies de sessão/CSRF seguros, HSTS (1 ano), `X_FRAME_OPTIONS = 'DENY'` e confia no header `X-Forwarded-Proto` do proxy do Render. Em produção: defina `SECRET_KEY` e `DJANGO_SUPERUSER_PASSWORD` fortes e mantenha `DEBUG=False`.
