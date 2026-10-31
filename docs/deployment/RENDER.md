# 🚀 Deploy no Render.com

O app roda no plano **Free** do Render, com banco PostgreSQL no **Supabase** ([SUPABASE.md](../database/SUPABASE.md)). A configuração está em [`render.yaml`](../../render.yaml) (Blueprint), [`build.sh`](../../build.sh) e [`gunicorn.conf.py`](../../gunicorn.conf.py).

- **App:** https://lista-presentes-im4b.onrender.com
- **Deploy automático:** a cada push na branch `main` (`branch: main` no `render.yaml`)
- **Health check:** `/health/`

---

## 📦 Plano Free: limites

| Item | Valor |
|------|-------|
| RAM | 512 MB, CPU compartilhada |
| Horas | 750 horas de instância por mês (somando os serviços da conta) |
| Sleep | Dorme após 15 min sem acesso; o primeiro acesso acorda o serviço (cerca de 1 min) |
| SMTP | Portas bloqueadas: o e-mail sai pela API HTTP da Brevo |
| Shell/SSH | Não disponível no Free: comandos de manutenção rodam no `build.sh` ou localmente apontando para o banco de produção |

Gunicorn (`gunicorn.conf.py`): 1 worker `gthread` com 4 threads, timeout de 120 s, `max_requests` 1000, `preload_app = True`. Ajustável por `WEB_CONCURRENCY`, `GUNICORN_THREADS`, `GUNICORN_TIMEOUT` e `MAX_REQUESTS`. Não aumente os workers no Free.

---

## 🛠️ Criar o serviço

1. No Render: **New → Blueprint** e selecione o repositório (o `render.yaml` cria o web service `lista-presentes`).
   Manualmente, use: Build Command `bash build.sh` e Start Command `gunicorn --config gunicorn.conf.py lista_presentes.wsgi:application`.
2. Preencha as variáveis marcadas como `sync: false` (abaixo) em **Environment**.
3. Faça o deploy e acompanhe os logs do build.

### O que o `build.sh` faz

1. Instala as dependências (`pip install -r requirements.txt`).
2. Compila o Tailwind CSS (`npx tailwindcss` em `theme/static_src` → `theme/static/css/dist/styles.css`).
3. Roda `collectstatic`.
4. Testa a conexão com o banco e **falha se estiver em SQLite** (falta `DATABASE_URL`).
5. Garante o schema `lista_presentes` (`scripts/ensure_schema.py`).
6. Roda `makemigrations` e `migrate --run-syncdb`; se der `InconsistentMigrationHistory`, tenta `--fake-initial` e depois `fix_migration_history --reset`.
7. Roda `fix_admin` (cria/promove o superusuário).

### Arquivos estáticos

Servidos pelo **WhiteNoise** via `STORAGES` do Django 5.1 com `CompressedManifestStaticFilesStorage`: cada versão do CSS/JS ganha nome com hash (ex.: `styles.<hash>.css`), então o navegador não fica com arquivo antigo após o deploy. O antigo `STATICFILES_STORAGE` é ignorado pelo Django 5.1; não o use.

---

## 🔑 Variáveis de ambiente

Já definidas no `render.yaml`: `PYTHON_VERSION=3.11.0`, `DEBUG=false`, `DJANGO_SETTINGS_MODULE`, `SECRET_KEY` (gerada), `ALLOWED_HOSTS`, `SITE_URL`, `GITHUB_REPO_OWNER`, `GITHUB_REPO_NAME`, `GITHUB_AUTO_CREATE_ISSUES`, `WEB_CONCURRENCY=1`, `GUNICORN_TIMEOUT=120`, `MAX_REQUESTS=1000`.

Preencher no Dashboard:

| Variável | Obrigatória | Uso |
|----------|-------------|-----|
| `DATABASE_URL` | ✅ | Supabase (pooler). Não adicione `?options=`: o `search_path` é aplicado pelo código |
| `DJANGO_SUPERUSER_EMAIL`, `DJANGO_SUPERUSER_PASSWORD` | ✅ | Admin criado pelo `fix_admin`. Sem elas, o padrão do comando é uma senha fraca. `RESET_ADMIN_PASSWORD=true` redefine a senha de um admin existente |
| `CRON_TOKEN` | ✅ para os workflows | Mesmo valor no Render e no secret `CRON_TOKEN` do GitHub |
| `GEMINI_API_KEY` | Recomendada | IA principal; `ANTHROPIC_API_KEY` e `OPENAI_API_KEY` são fallback |
| `BREVO_API_KEY`, `DEFAULT_FROM_EMAIL` | Recomendada | E-mail (redefinição de senha, boas-vindas). Remetente verificado na Brevo |
| `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`, `VAPID_ADMIN_EMAIL` | Opcional | Push. Gere com `python manage.py gerar_chaves_vapid` |
| `MERCADOLIVRE_CLIENT_ID`, `MERCADOLIVRE_CLIENT_SECRET` | Opcional | API do Mercado Livre (Redirect URI `{SITE_URL}/integracoes/mercadolivre/callback/`) |
| `GITHUB_TOKEN` | Opcional | Issues automáticas para falhas de imagem |
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` (e demais provedores) | Opcional | Login social ([SOCIAL_LOGIN_CONFIG.md](../features/SOCIAL_LOGIN_CONFIG.md)) |
| `SUPABASE_URL`, `SUPABASE_KEY` | Opcional | Não usadas pelo Django hoje |

Lista completa com padrões: [INSTALACAO.md](../development/INSTALACAO.md#️-variáveis-de-ambiente).

---

## ⏰ Keep-alive e tarefas agendadas

O Render Free não tem cron nativo; as tarefas rodam no GitHub Actions:

| Workflow | Função |
|----------|--------|
| [`keep-alive.yml`](../../.github/workflows/keep-alive.yml) | Ping em `/health/` a cada 14 min **só nas horas de uso** de cada dia da semana (definidas pelo relatório de acessos), para não estourar as 750 h/mês. Fora delas o serviço dorme |
| [`pesquisa-precos.yml`](../../.github/workflows/pesquisa-precos.yml) | Toda segunda às 08:00 UTC chama `POST /api/cron/pesquisar-precos/` (header `X-Cron-Token`). Manual com opção `forcar` |
| [`relatorio-acessos.yml`](../../.github/workflows/relatorio-acessos.yml) | Sob demanda: busca `/api/acessos/resumo/?dias=N` (header `X-Cron-Token`) e publica no resumo da execução. Use para revisar as horas do keep-alive |

Configuração no GitHub (**Settings → Secrets and variables → Actions**):

- Secret `CRON_TOKEN`: **mesmo valor** do `CRON_TOKEN` do Render (sem ele o endpoint responde 503; com valor diferente, 403).
- Variável `RENDER_URL` (opcional): URL base do app; padrão `https://lista-presentes-im4b.onrender.com`.

> ⚠️ Em repositório público, o GitHub desativa workflows agendados após 60 dias sem atividade no repositório. Se o keep-alive ou a pesquisa de preços pararem, reative em **Actions → workflow → Enable workflow** (ou Disable/Enable).

---

## 🆘 Solução de problemas

| Sintoma no log | Causa e solução |
|----------------|-----------------|
| `Using SQLite instead of PostgreSQL!` | `DATABASE_URL` ausente. Adicione em Environment e refaça o deploy |
| `Network is unreachable` | Host direto do Supabase (IPv6). Use o Connection Pooler (`*.pooler.supabase.com`) |
| `password authentication failed` | Senha com caracteres especiais sem URL encoding (`@` → `%40`, `#` → `%23`, `!` → `%21`) |
| `InconsistentMigrationHistory` | O `build.sh` tenta corrigir sozinho. Se persistir, veja [migrations.md](../database/migrations.md) |
| CSS/JS desatualizado ou 404 em estáticos | Confira no log do build a compilação do Tailwind e o `collectstatic`; não defina `STATICFILES_STORAGE` |
| E-mail não chega | Confira `BREVO_API_KEY` e se o remetente de `DEFAULT_FROM_EMAIL` está verificado na Brevo. SMTP não funciona no Free |
| Workflows de cron falham com 403/503 | `CRON_TOKEN` diferente entre Render e GitHub, ou ausente no Render |
| Primeiro acesso lento | Serviço dormindo (fora das horas do keep-alive). Normal no Free |
| Out of memory | Mantenha `WEB_CONCURRENCY=1` |

Para diagnosticar o banco localmente com a URL de produção: `DATABASE_URL=... python scripts/check_database_config.py`. Erros 500: [DEBUG_500_ERRORS.md](../development/DEBUG_500_ERRORS.md).

---

## ✅ Checklist pós-deploy

- [ ] Build concluído, com `Database connection successful` e migrações aplicadas
- [ ] `/health/` responde 200
- [ ] Login (e-mail e, se configurado, Google) e acesso ao `/admin/`
- [ ] CSS carregando com o tema padrão (`emerald_light`)
- [ ] Secret `CRON_TOKEN` igual no GitHub e no Render; workflows agendados habilitados

---

## 🔗 Links

- Dashboard: https://dashboard.render.com/
- Docs do Render: https://render.com/docs · Free: https://render.com/docs/free
- Status: https://status.render.com
