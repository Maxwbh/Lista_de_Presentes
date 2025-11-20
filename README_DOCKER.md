# 🐳 Guia de Deploy - Docker & Render.com

## 📋 Sumário

- [Pré-requisitos](#pré-requisitos)
- [Instalação Local com Docker](#instalação-local-com-docker)
- [Deploy no Render.com](#deploy-no-rendercom)
- [Configuração de Variáveis de Ambiente](#configuração-de-variáveis-de-ambiente)
- [Troubleshooting](#troubleshooting)

---

## 🔧 Pré-requisitos

### Para Desenvolvimento Local:
- **Docker** (versão 20.10+)
- **Docker Compose** (versão 2.0+)
- **Git**

### Para Deploy no Render.com:
- Conta no [Render.com](https://render.com) (plano free disponível)
- Repositório Git (GitHub, GitLab, ou Bitbucket)
- Chaves de API (opcional):
  - Claude AI (Anthropic)
  - ChatGPT (OpenAI)
  - Gemini (Google)

---

## 🏠 Instalação Local com Docker

### Passo 1: Clonar o Repositório

```bash
git clone https://github.com/seu-usuario/Lista_de_Presentes.git
cd Lista_de_Presentes
```

### Passo 2: Configurar Variáveis de Ambiente

```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar com suas chaves de API (opcional)
nano .env
```

### Passo 3: Iniciar com Docker Compose

```bash
# Build e start dos containers
docker-compose up --build

# Ou em background (detached mode)
docker-compose up -d --build
```

### Passo 4: Acessar a Aplicação

Abra seu navegador em: **http://localhost:8000**

### Comandos Úteis

```bash
# Ver logs
docker-compose logs -f web

# Parar containers
docker-compose down

# Parar e remover volumes (limpa banco de dados)
docker-compose down -v

# Executar comandos Django
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py shell

# Executar migrations
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate

# Rebuild após mudanças no código
docker-compose up --build
```

---

## ☁️ Deploy no Render.com

### Método 1: Deploy Automático com render.yaml (Recomendado)

#### Passo 1: Preparar o Repositório

```bash
# Certifique-se de que todos os arquivos estão commitados
git add .
git commit -m "Preparar para deploy no Render.com"
git push origin main
```

#### Passo 2: Criar Conta no Render.com

1. Acesse [render.com](https://render.com)
2. Clique em "Get Started" ou "Sign Up"
3. Conecte sua conta GitHub/GitLab/Bitbucket

#### Passo 3: Criar novo Web Service

1. No dashboard, clique em **"New +"** → **"Blueprint"**
2. Selecione seu repositório `Lista_de_Presentes`
3. Render detectará automaticamente o arquivo `render.yaml`
4. Clique em **"Apply"**

#### Passo 4: Configurar Variáveis de Ambiente

No dashboard do Render, vá em:
1. **Environment** → **Environment Variables**
2. Adicione as chaves de API:

```
ANTHROPIC_API_KEY = sua-chave-claude
OPENAI_API_KEY = sua-chave-openai
GEMINI_API_KEY = sua-chave-gemini
```

#### Passo 5: Aguardar Deploy

- O Render irá automaticamente:
  - ✅ Criar banco PostgreSQL
  - ✅ Build da aplicação
  - ✅ Executar migrations
  - ✅ Coletar arquivos estáticos
  - ✅ Criar superusuário (se configurado)

**Deploy leva ~5-10 minutos**

#### Passo 6: Acessar Aplicação

Sua URL será algo como:
```
https://lista-presentes.onrender.com
```

---

### Método 2: Deploy Manual

Se preferir não usar o `render.yaml`:

#### 1. Criar Web Service Manualmente

1. Dashboard → **"New +"** → **"Web Service"**
2. Conecte seu repositório
3. Configure:
   - **Name:** `lista-presentes`
   - **Region:** Oregon (ou mais próximo)
   - **Branch:** `main`
   - **Build Command:**
     ```bash
     pip install --upgrade pip && pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate --noinput
     ```
   - **Start Command:**
     ```bash
     gunicorn --bind 0.0.0.0:$PORT --workers 3 --timeout 120 lista_presentes.wsgi:application
     ```

#### 2. Criar PostgreSQL Database

1. Dashboard → **"New +"** → **"PostgreSQL"**
2. Configure:
   - **Name:** `lista-presentes-db`
   - **Database:** `lista_presentes`
   - **User:** `lista_presentes_user`
   - **Region:** Oregon (mesma do web service)
   - **Plan:** Free

#### 3. Conectar Database ao Web Service

1. No Web Service, vá em **Environment**
2. Adicione variável:
   ```
   DATABASE_URL = [copiar Internal Database URL do PostgreSQL]
   ```

#### 4. Adicionar Outras Variáveis

```bash
SECRET_KEY = [gerar em https://djecrety.ir/]
DEBUG = false
ALLOWED_HOSTS = .onrender.com
ANTHROPIC_API_KEY = sua-chave
OPENAI_API_KEY = sua-chave
GEMINI_API_KEY = sua-chave
```

---

## ⚠️ Limitações do Plano Free do Render.com

O plano **free** do Render.com tem algumas limitações importantes:

### 🔴 Sem Disco Persistente
- **Não suporta armazenamento permanente de arquivos**
- Arquivos estáticos (CSS/JS) são servidos pelo **WhiteNoise** ✅ (já configurado)
- **Uploads de imagens** dos usuários **não são persistidos** entre deploys

### 💡 Soluções para Upload de Imagens:

#### Opção 1: Serviço Externo (Recomendado para Free)
```python
# Use serviços gratuitos de CDN:
# - Cloudinary (10 GB grátis)
# - ImgBB (ilimitado)
# - Amazon S3 (12 meses grátis)
# - Backblaze B2 (10 GB grátis)
```

#### Opção 2: Upgrade para Plano Pago
```
Render.com Starter Plan ($7/mês):
✅ Disco persistente (1 GB incluído)
✅ Mais CPU e memória
✅ Sem sleep automático
```

### 🌐 Outras Limitações do Free:
- **Sleep automático** após 15 minutos de inatividade (primeiro acesso pode demorar ~30s)
- **750 horas/mês** de uptime (suficiente para 1 serviço 24/7)
- **Banco PostgreSQL Free**: 1 GB de armazenamento (suficiente para ~10.000 presentes)

### ✅ O que Funciona no Free:
- ✅ Django + PostgreSQL
- ✅ Arquivos estáticos (CSS, JS, imagens do projeto)
- ✅ Migrations automáticas
- ✅ SSL/HTTPS gratuito
- ✅ Deploy automático via Git
- ✅ Superusuário criado automaticamente

---

## 🔐 Configuração de Variáveis de Ambiente

### Variáveis Obrigatórias

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `SECRET_KEY` | Chave secreta Django | `django-insecure-xyz123...` |
| `DATABASE_URL` | URL do banco (automático no Render) | `postgresql://user:pass@host/db` |
| `ALLOWED_HOSTS` | Hosts permitidos | `.onrender.com,localhost` |

### Variáveis Opcionais (APIs de IA)

| Variável | Descrição | Onde Obter |
|----------|-----------|------------|
| `ANTHROPIC_API_KEY` | Claude AI | [console.anthropic.com](https://console.anthropic.com) |
| `OPENAI_API_KEY` | ChatGPT | [platform.openai.com](https://platform.openai.com) |
| `GEMINI_API_KEY` | Google Gemini | [makersuite.google.com](https://makersuite.google.com) |

### Variáveis de Desenvolvimento

| Variável | Produção | Desenvolvimento |
|----------|----------|-----------------|
| `DEBUG` | `false` | `true` |
| `SECRET_KEY` | Gerar nova | Qualquer string |

---

## 🚀 Fluxo de Deploy Automático

Após configuração inicial, cada `git push` para `main` irá:

1. ✅ Trigger deploy automático no Render
2. ✅ Build da aplicação
3. ✅ Executar migrations
4. ✅ Coletar statics
5. ✅ Restart do serviço

**⚡ Deploy leva ~3-5 minutos**

---

## 📊 Monitoramento no Render.com

### Logs

```bash
# Via Dashboard
Settings → Logs → View Logs

# Via Render CLI (opcional)
render logs -s lista-presentes
```

### Métricas

- CPU Usage
- Memory Usage
- Request Count
- Response Time
- Error Rate

Disponíveis em: **Dashboard → Metrics**

---

## 🎯 Criar Superusuário

### No Render.com

**Opção 1: Automático (recomendado)**

Configure no `render.yaml`:
```yaml
- key: CREATE_SUPERUSER
  value: true
- key: DJANGO_SUPERUSER_EMAIL
  value: admin@example.com
- key: DJANGO_SUPERUSER_PASSWORD
  generateValue: true
```

Render criará automaticamente no primeiro deploy.

**Opção 2: Manual via Shell**

1. Dashboard → **Shell**
2. Execute:
```bash
python manage.py createsuperuser
```

### No Docker Local

```bash
docker-compose exec web python manage.py createsuperuser
```

---

## 🔒 Segurança em Produção

### ✅ Configurações Automáticas (quando DEBUG=False)

O `settings.py` ativa automaticamente:

- ✅ `SECURE_SSL_REDIRECT` - Força HTTPS
- ✅ `SESSION_COOKIE_SECURE` - Cookies apenas HTTPS
- ✅ `CSRF_COOKIE_SECURE` - CSRF apenas HTTPS
- ✅ `SECURE_BROWSER_XSS_FILTER` - Proteção XSS
- ✅ `SECURE_CONTENT_TYPE_NOSNIFF` - Proteção MIME
- ✅ `X_FRAME_OPTIONS` - Proteção Clickjacking
- ✅ `HSTS` - HTTP Strict Transport Security

### ⚠️ Checklist de Segurança

- [ ] `DEBUG = false` em produção
- [ ] `SECRET_KEY` única e segura
- [ ] Chaves de API em variáveis de ambiente
- [ ] `ALLOWED_HOSTS` configurado corretamente
- [ ] Backup regular do banco de dados
- [ ] Monitoramento de logs ativo

---

## 🐛 Troubleshooting

### Problema: "DisallowedHost at /"

**Causa:** `ALLOWED_HOSTS` não inclui o domínio

**Solução:**
```bash
# No Render, adicione em Environment:
ALLOWED_HOSTS = .onrender.com,seu-dominio.com
```

### Problema: "Static files não carregam"

**Causa:** `collectstatic` não foi executado

**Solução:**
```bash
# Local Docker
docker-compose exec web python manage.py collectstatic --noinput

# Render
# Build Command deve incluir:
python manage.py collectstatic --noinput
```

### Problema: "No module named 'dotenv'"

**Causa:** `python-dotenv` não instalado

**Solução:**
```bash
pip install python-dotenv
# Ou rebuild container Docker
docker-compose up --build
```

### Problema: "Database connection failed"

**Causa:** `DATABASE_URL` incorreto ou banco não acessível

**Solução:**
```bash
# Verificar variável
echo $DATABASE_URL

# Testar conexão (Render Shell)
python manage.py dbshell
```

### Problema: "502 Bad Gateway no Render"

**Causas possíveis:**
1. Build falhou
2. Start command incorreto
3. Porta $PORT não está sendo usada

**Soluções:**
```bash
# Ver logs de build
Dashboard → Logs

# Verificar start command
gunicorn --bind 0.0.0.0:$PORT lista_presentes.wsgi:application

# Check health
Dashboard → Events
```

### Problema: "Out of memory no Render (plan free)"

**Causa:** Plan free tem limite de 512MB RAM

**Soluções:**
1. Reduzir workers do Gunicorn:
   ```bash
   gunicorn --workers 1 ...  # ao invés de 3
   ```

2. Upgrade para plan Starter ($7/mês)

### Problema: "IA APIs não funcionam"

**Verificar:**

```bash
# 1. Chaves estão definidas?
Dashboard → Environment → Environment Variables

# 2. Chaves são válidas?
# Testar no Shell do Render:
python manage.py shell
>>> import os
>>> print(os.getenv('ANTHROPIC_API_KEY'))
```

---

## 📱 PWA (Progressive Web App)

### Instalar no Celular

1. Acesse a URL no navegador mobile
2. **Android:** Menu → "Adicionar à tela inicial"
3. **iOS:** Compartilhar → "Adicionar à Tela de Início"

### Ícones PWA

Coloque ícones em `static/icons/`:
- `icon-192x192.png` - Ícone pequeno
- `icon-512x512.png` - Ícone grande

---

## 🔄 Backup e Restore

### Backup do Banco (Render)

```bash
# Via Render Dashboard
Database → Backups → Create Backup

# Via pg_dump (local)
pg_dump -h [HOST] -U [USER] -d [DB] > backup.sql
```

### Restore

```bash
# Via psql
psql -h [HOST] -U [USER] -d [DB] < backup.sql
```

---

## 💰 Custos no Render.com

### Plan Free (Recomendado para Testes)

- ✅ 750 horas/mês (suficiente para 1 app)
- ✅ PostgreSQL 256MB
- ✅ 1GB bandwidth/mês
- ✅ SSL automático
- ⚠️ App "dorme" após 15min inativo
- ⚠️ Cold start de ~30s

### Plan Starter ($7/mês)

- ✅ Sempre ativo
- ✅ PostgreSQL 1GB
- ✅ 100GB bandwidth
- ✅ Melhor performance

---

## 📞 Suporte

### Documentação Oficial

- **Render:** [render.com/docs](https://render.com/docs)
- **Django:** [docs.djangoproject.com](https://docs.djangoproject.com)
- **Docker:** [docs.docker.com](https://docs.docker.com)

### Issues do Projeto

[GitHub Issues](https://github.com/seu-usuario/Lista_de_Presentes/issues)

---

## ✅ Checklist de Deploy

- [ ] Código commitado no Git
- [ ] `render.yaml` configurado
- [ ] `.env.example` atualizado
- [ ] `requirements.txt` completo
- [ ] Conta Render.com criada
- [ ] Repositório conectado
- [ ] Database PostgreSQL criada
- [ ] Variáveis de ambiente definidas
- [ ] Deploy executado com sucesso
- [ ] Migrations aplicadas
- [ ] Superusuário criado
- [ ] Site acessível via HTTPS
- [ ] PWA testado no mobile
- [ ] Backup configurado

---

**🎉 Pronto! Seu sistema está no ar!**

Acesse: `https://seu-app.onrender.com`
