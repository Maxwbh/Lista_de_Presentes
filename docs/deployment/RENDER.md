# Deploy no Render.com - Guia Completo

## 📋 Configuração

### Aplicação
- **URL**: https://your-app-name.onrender.com
- **Dashboard**: https://dashboard.render.com/web/lista-presentes
- **Branch**: Automático (main/production)

### Database
- **Provider**: Supabase PostgreSQL
- **Armazenamento**: 500 MB Free Tier
- **Connection Pooler**: Ativo (PgBouncer)
- **Backup**: Automático (7 dias)

---

## 🚀 Free Tier - Características e Otimizações

### Limites do Free Tier

**Web Service:**
- RAM: 512 MB
- CPU: Compartilhada
- Inatividade: Desliga após 15 minutos sem uso
- Cold Start: 30-60 segundos
- Horas/mês: 750 horas gratuitas
- SSL: HTTPS automático

### Otimizações Implementadas

#### 1. Gunicorn (`gunicorn.conf.py`)

```python
# Free Tier (512 MB RAM)
workers = 1                # 1 worker
threads = 2                # 2 threads por worker
timeout = 120              # 2 minutos
max_requests = 1000        # Reinicia após 1000 requests
preload_app = True         # Economiza memória
```

**Benefícios:**
- `max_requests`: Previne memory leaks
- `preload_app`: Compartilha código entre workers
- `threads`: Concorrência sem usar muita RAM

#### 2. Build Script (`build.sh`)

```bash
#!/usr/bin/env bash
set -o errexit

# 1. Testar conexão database
python -c "import django; django.setup(); ..."

# 2. Instalar dependências
pip install --upgrade pip
pip install -r requirements.txt

# 3. Coletar static files
python manage.py collectstatic --noinput

# 4. Corrigir histórico de migrações (auto)
python manage.py fix_migration_history

# 5. Aplicar migrações
python manage.py migrate --noinput

# 6. Criar/atualizar admin user
python manage.py shell < scripts/create_or_update_admin.py
```

---

## 🔑 Variáveis de Ambiente

### Obrigatórias

```bash
# Django
SECRET_KEY=<gerado automaticamente>
ALLOWED_HOSTS=.onrender.com,your-app-name.onrender.com

# Database (Supabase)
DATABASE_URL=postgresql://postgres.YOUR_PROJECT_ID:YOUR_PASSWORD_ENCODED@aws-1-us-east-2.pooler.supabase.com:6543/postgres

# GitHub (Auto-create Issues)
GITHUB_TOKEN=<fornecido pelo administrador>
GITHUB_REPO_OWNER=Maxwbh
GITHUB_REPO_NAME=Lista_de_Presentes
GITHUB_AUTO_CREATE_ISSUES=True
```

### Opcionais

```bash
# Debug (apenas desenvolvimento)
DEBUG=False

# Django Admin
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_PASSWORD=<senha forte>
DJANGO_SUPERUSER_EMAIL=admin@example.com
```

**Configurar em:** https://dashboard.render.com/web/lista-presentes/environment

---

## 👤 Criar/Atualizar Admin User

### Durante Deploy (Automático)

O script `scripts/create_or_update_admin.py` é executado automaticamente no `build.sh`:

```python
# Se admin não existe: cria
# Se admin existe: atualiza senha e email
```

### Manualmente (Render Shell)

```bash
# Acessar Shell no Render Dashboard
python manage.py createsuperuser --username admin --email admin@example.com
```

**Credenciais padrão:**
- Username: `admin` (de DJANGO_SUPERUSER_USERNAME)
- Password: (de DJANGO_SUPERUSER_PASSWORD)
- Email: (de DJANGO_SUPERUSER_EMAIL)

**Admin URL:** https://your-app-name.onrender.com/admin/

---

## 🧪 Gerar Dados de Teste

### Via Django Shell (Render Dashboard)

```python
from presentes.tests.factories import *

# Criar 3 usuários
usuarios = UsuarioFactory.create_batch(3)

# Criar 2 grupos
grupo1 = GrupoFactory.create(nome="Família")
grupo2 = GrupoFactory.create(nome="Amigos")

# Adicionar membros aos grupos
GrupoMembroFactory.create(usuario=usuarios[0], grupo=grupo1, e_mantenedor=True)
GrupoMembroFactory.create(usuario=usuarios[1], grupo=grupo1)

# Criar 10 presentes para o grupo1
presentes = PresenteFactory.create_batch(10, usuario=usuarios[0], grupo=grupo1)

# Criar 3 compras
CompraFactory.create(presente=presentes[0], comprador=usuarios[1])
CompraFactory.create(presente=presentes[1], comprador=usuarios[2])

print(f"✅ Criados {Usuario.objects.count()} usuários")
print(f"✅ Criados {Grupo.objects.count()} grupos")
print(f"✅ Criados {Presente.objects.count()} presentes")
print(f"✅ Criadas {Compra.objects.count()} compras")
```

### Via Script Python

```bash
# Criar script populate_data.py
cat > populate_data.py <<'EOF'
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lista_presentes.settings')
django.setup()

from presentes.tests.factories import *

# Sua lógica aqui...
EOF

# Executar no Render Shell
python populate_data.py
```

---

## 🆘 Troubleshooting

### Deploy Failing

#### Erro: "InconsistentMigrationHistory"

**Causa:** Histórico de migrações inconsistente

**Solução (Automática):**
```bash
⚠️  InconsistentMigrationHistory detected!
🔧 Auto-fixing migration history...
✅ Fixed with --fake-initial
```

O `build.sh` corrige automaticamente. Se falhar:

```bash
# Render Shell
python manage.py fix_migration_history --reset
python manage.py migrate --fake-initial
```

#### Erro: "Network is unreachable"

**Causa:** Usando database host errado

**Solução:** Verificar DATABASE_URL usa Connection Pooler:
```
aws-1-us-east-2.pooler.supabase.com:6543  (não db.YOUR_PROJECT_ID:5432)
```

#### Erro: "Using SQLite instead of PostgreSQL"

**Causa:** DATABASE_URL não configurada

**Solução:**
1. Dashboard > Environment
2. Adicionar DATABASE_URL
3. Save Changes
4. Redeploy

### Cold Start (Aplicação Lenta)

**Causa:** Free Tier desliga após 15min de inatividade

**Solução:**
1. Aguardar 30-60s no primeiro acesso
2. Usar serviço keep-alive (opcional): `KEEP_ALIVE.md`
3. Upgrade para Starter+ ($7/mês) para manter sempre ativo

### Build Timeout

**Causa:** Build demora mais de 15 minutos

**Solução:**
```bash
# build.sh - adicionar flag
pip install --no-cache-dir -r requirements.txt
```

### Out of Memory

**Causa:** Gunicorn usando mais de 512 MB

**Solução:** Verificar `gunicorn.conf.py`:
```python
workers = 1  # NÃO aumentar no Free Tier
threads = 2  # OK aumentar até 4
```

### Static Files Não Carregam

**Causa:** `collectstatic` não executou

**Solução:** Verificar `build.sh` tem:
```bash
python manage.py collectstatic --noinput
```

E `settings.py` tem:
```python
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

---

## ✅ Checklist de Deploy

### Antes do Deploy

- [ ] Variáveis de ambiente configuradas
- [ ] DATABASE_URL com Connection Pooler
- [ ] GITHUB_TOKEN configurado
- [ ] SECRET_KEY gerado (automático)
- [ ] ALLOWED_HOSTS configurado

### Após Deploy

- [ ] Build completou com sucesso
- [ ] Migrações aplicadas (verificar logs)
- [ ] Admin user criado/atualizado
- [ ] Site acessível via HTTPS
- [ ] Login funcionando
- [ ] Static files carregando
- [ ] Database conectado (Supabase)

### Verificação Completa

```bash
# 1. Verificar deployment
https://your-app-name.onrender.com/

# 2. Verificar admin
https://your-app-name.onrender.com/admin/

# 3. Verificar logs
https://dashboard.render.com/web/lista-presentes/logs

# 4. Verificar environment
https://dashboard.render.com/web/lista-presentes/environment

# 5. Testar funcionalidades
- [ ] Login com Google
- [ ] Criar presente
- [ ] Ver lista de presentes
- [ ] Trocar de grupo
- [ ] Tema (Purple/Green)
```

---

## 🔧 Comandos Úteis

### Render Dashboard > Shell

```bash
# Acessar Django shell
python manage.py shell

# Ver migrações
python manage.py showmigrations

# Aplicar migrações manualmente
python manage.py migrate

# Criar superuser
python manage.py createsuperuser

# Verificar database
python scripts/check_database_config.py

# Coletar static files
python manage.py collectstatic --noinput

# Ver logs em tempo real
# (usar a interface web: Dashboard > Logs)
```

### Git (Local)

```bash
# Forçar redeploy (commit vazio)
git commit --allow-empty -m "chore: Force redeploy"
git push origin main

# Ver status do deploy
# (usar a interface web: Dashboard > Events)
```

---

## 📊 Monitoramento

### Logs

```bash
# Acessar logs
https://dashboard.render.com/web/lista-presentes/logs

# Filtrar erros
Ctrl+F: "ERROR"
Ctrl+F: "❌"
Ctrl+F: "Traceback"
```

### Métricas (apenas Starter+)

- CPU Usage
- Memory Usage
- Request Count
- Response Time

**Free Tier:** Métricas não disponíveis

---

## 💰 Upgrade

### Quando Fazer Upgrade?

**Considere Starter+ ($7/mês) se:**
- Cold start incomoda usuários (>30s)
- Aplicação fica inativa frequentemente
- Precisa de métricas e monitoramento
- Quer mais RAM (até 2 GB)
- Quer CPU dedicada

### Como Fazer Upgrade

1. Dashboard > Settings
2. Instance Type: Free → Starter
3. Confirm
4. Atualizar `gunicorn.conf.py`:
   ```python
   workers = 4  # Pode aumentar com mais RAM
   ```

---

## 🔗 Links Úteis

- **Site**: https://your-app-name.onrender.com
- **Dashboard**: https://dashboard.render.com/web/lista-presentes
- **Logs**: https://dashboard.render.com/web/lista-presentes/logs
- **Environment**: https://dashboard.render.com/web/lista-presentes/environment
- **Render Docs**: https://render.com/docs
- **Render Status**: https://status.render.com

---

**Última atualização:** 2026-02-07
**Versão:** 1.1.31
