# Guia Completo: Render Free Tier

Este documento explica como a aplicação está otimizada para o **Render Free Tier** e suas limitações.

## Características do Free Tier

### Web Service (Aplicação Django)
- **RAM**: 512 MB
- **CPU**: Compartilhada
- **Inatividade**: Desliga após 15 minutos sem uso
- **Cold Start**: 30-60 segundos para acordar
- **Horas/mês**: 750 horas gratuitas
- **Builds**: Ilimitados
- **SSL**: Incluído (HTTPS automático)

### Database (PostgreSQL)
- **Armazenamento**: 1 GB
- **RAM**: Compartilhada
- **Expira**: 90 dias após criação (requer recriação)
- **Backups**: Não incluídos
- **Conexões**: Limitadas

## Otimizações Implementadas

### 1. Gunicorn Otimizado (`gunicorn.conf.py`)

#### Free Tier (512 MB RAM)
```python
workers = 1                # 1 worker (poucos recursos)
threads = 2                # 2 threads por worker
timeout = 120              # 2 minutos
max_requests = 1000        # Reinicia após 1000 requests
preload_app = True         # Carrega app antes de fork
```

#### Starter+ (2 GB+ RAM)
```python
workers = 4                # 4 workers (mais recursos)
threads = 2                # 2 threads por worker
timeout = 120              # 2 minutos
max_requests = 1000        # Reinicia após 1000 requests
```

**Benefícios:**
- `max_requests`: Previne memory leaks reiniciando workers
- `preload_app`: Economiza memória compartilhando código
- `threads`: Permite concorrência sem usar muita RAM

### 2. Variáveis de Ambiente

```yaml
WEB_CONCURRENCY: 1        # Workers (Free: 1, Starter+: 2-4)
GUNICORN_TIMEOUT: 120     # Timeout em segundos
MAX_REQUESTS: 1000        # Requests antes de reiniciar worker
```

Altere `WEB_CONCURRENCY` no dashboard do Render ao fazer upgrade:
- Free: `1`
- Starter (512 MB): `1-2`
- Standard (2 GB): `2-4`
- Pro (4 GB): `4-8`

### 3. Build Script Otimizado

```bash
# Coleta estáticos (usa whitenoise em produção)
python manage.py collectstatic --noinput

# Cria e aplica migrações
python manage.py makemigrations --noinput
python manage.py migrate --run-syncdb --noinput

# Verifica migrações aplicadas
python manage.py showmigrations
```

## Limitações e Soluções

### ⚠️ Limitação 1: Cold Start (Inatividade)

**Problema:** Após 15 minutos sem requests, o serviço desliga.
- Primeiro acesso após inatividade: 30-60 segundos para carregar

**Soluções:**

**Opção 1: Cron Job Externo (Recomendado)**
```bash
# Usar serviço gratuito como cron-job.org ou UptimeRobot
# Fazer request para /health/ a cada 10-14 minutos
GET https://seu-app.onrender.com/health/
```

**Opção 2: GitHub Actions**
```yaml
# .github/workflows/keep-alive.yml
name: Keep Alive
on:
  schedule:
    - cron: '*/10 * * * *'  # A cada 10 minutos
jobs:
  keep-alive:
    runs-on: ubuntu-latest
    steps:
      - run: curl https://seu-app.onrender.com/health/
```

**Opção 3: Upgrade para Starter ($7/mês)**
- Serviço sempre ativo
- Sem cold starts

### ⚠️ Limitação 2: 512 MB de RAM

**Problema:** RAM limitada pode causar crashes com muitas requests simultâneas.

**Soluções:**

**1. Usar 1 Worker + Threads**
✅ Já configurado em `gunicorn.conf.py`

**2. Limitar Uploads**
```python
# settings.py
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5 MB
```

**3. Usar Cache Externo**
```python
# Usar Redis para cache (se necessário)
# Render oferece Redis grátis também
```

**4. Monitorar Memória**
```bash
# Via Render Shell
free -h
ps aux
```

### ⚠️ Limitação 3: Database Expira em 90 Dias

**Problema:** PostgreSQL Free expira após 90 dias.

**Soluções:**

**Opção 1: Backup Manual Regular**
```bash
# A cada 30 dias, fazer backup via Render Shell
pg_dump $DATABASE_URL > backup.sql

# Ou usar comando Django
python manage.py dumpdata > backup.json
```

**Opção 2: Recriar Database (Antes de Expirar)**
```bash
# 1. Fazer backup dos dados
python manage.py dumpdata > backup.json

# 2. Criar novo database no Render
# 3. Atualizar DATABASE_URL
# 4. Rodar migrations
python manage.py migrate

# 5. Restaurar dados
python manage.py loaddata backup.json
```

**Opção 3: Upgrade para Starter DB ($7/mês)**
- Sem expiração
- Backups automáticos
- 10 GB de armazenamento

### ⚠️ Limitação 4: CPU Compartilhada

**Problema:** CPU compartilhada pode ser lenta em picos de uso.

**Soluções:**

**1. Otimizar Queries**
```python
# Usar select_related e prefetch_related
usuarios = Usuario.objects.select_related('grupo_ativo').all()

# Adicionar índices
class Meta:
    indexes = [
        models.Index(fields=['email']),
    ]
```

**2. Cache de Queries**
```python
from django.core.cache import cache

def get_usuarios():
    usuarios = cache.get('usuarios_list')
    if not usuarios:
        usuarios = Usuario.objects.all()
        cache.set('usuarios_list', usuarios, 300)  # 5 min
    return usuarios
```

**3. Async Tasks (Celery)**
```python
# Para tarefas pesadas, usar Celery com Redis
# Exemplo: processamento de imagens, emails, etc.
```

## Monitoramento

### Verificar Status

**1. Dashboard do Render**
- Métricas de CPU e RAM
- Logs em tempo real
- Número de requests

**2. Health Check**
```bash
curl https://seu-app.onrender.com/health/
```

**3. Logs**
```bash
# Via Render Dashboard
# Ou via CLI
render logs -s lista-presentes
```

### Alertas

Configure alertas no Render Dashboard:
- CPU > 80%
- RAM > 80%
- Crashes
- Deploy falhou

## Upgrade Path

### Quando Fazer Upgrade?

**Sinais de que precisa upgrade:**
- ❌ Crashes frequentes por falta de RAM
- ❌ Usuários reclamam de lentidão
- ❌ Cold starts incomodam muito
- ❌ Database fica expirando (90 dias)
- ❌ Mais de 750 horas/mês de uso

### Planos Disponíveis

**Starter ($7/mês cada)**
- Web: 512 MB RAM, sempre ativo
- DB: 10 GB, sem expiração, backups

**Standard ($25/mês Web)**
- 2 GB RAM
- 2-4 workers recomendados
- CPU dedicada

**Pro ($85/mês Web)**
- 4 GB RAM
- 4-8 workers recomendados
- CPU dedicada
- Mais rápido

### Como Fazer Upgrade

**1. Via Dashboard**
```
Render Dashboard > Service > Settings > Instance Type
```

**2. Ajustar WEB_CONCURRENCY**
```yaml
# Starter (512 MB)
WEB_CONCURRENCY: 1-2

# Standard (2 GB)
WEB_CONCURRENCY: 2-4

# Pro (4 GB)
WEB_CONCURRENCY: 4-8
```

**3. Ajustar gunicorn.conf.py (Opcional)**
```python
# Calcular workers automaticamente
import multiprocessing
workers = (2 * multiprocessing.cpu_count()) + 1
```

## Checklist de Deploy

### Antes do Deploy

- [x] `render.yaml` configurado com `plan: free`
- [x] `gunicorn.conf.py` otimizado (1 worker, 2 threads)
- [x] `WEB_CONCURRENCY=1` configurado
- [x] `build.sh` executa migrações
- [x] `ALLOWED_HOSTS` inclui `.onrender.com`
- [x] `DEBUG=false` em produção
- [x] `SECRET_KEY` gerado automaticamente
- [x] APIs keys configuradas (se necessário)

### Após o Deploy

- [ ] Teste de health check: `curl https://seu-app.onrender.com/health/`
- [ ] Teste de login e funcionalidades
- [ ] Verificar logs no dashboard
- [ ] Configurar keep-alive (cron job)
- [ ] Configurar alertas
- [ ] Documentar credenciais de admin

## Custos Estimados

### Free Tier (Atual)
- Web Service: **$0/mês**
- Database: **$0/mês** (expira em 90 dias)
- **Total: $0/mês**

### Starter (Recomendado para Produção)
- Web Service: **$7/mês**
- Database: **$7/mês**
- **Total: $14/mês**

### Standard (Para Mais Usuários)
- Web Service: **$25/mês**
- Database: **$7/mês**
- **Total: $32/mês**

## Dicas de Economia

1. **Use Free enquanto possível** - Perfeito para desenvolvimento e testes
2. **Keep Alive Manual** - Use cron jobs gratuitos externos
3. **Otimize Código** - Queries eficientes economizam recursos
4. **Cache Agressivo** - Reduz carga no servidor
5. **Monitore Uso** - Só faça upgrade quando realmente necessário

## Troubleshooting Free Tier

### Problema: "Out of Memory"
**Solução:** Reduzir workers para 1, otimizar código, upgrade

### Problema: "Service Unavailable"
**Solução:** Cold start (espere 30s) ou serviço caiu (verificar logs)

### Problema: Database Connection Failed
**Solução:** Database expirou (90 dias), recriar database

### Problema: Muito Lento
**Solução:** Cold start, CPU compartilhada ocupada, upgrade

## Contato

Dúvidas ou problemas:
- Maxwell Oliveira (@maxwbh)
- maxwbh@gmail.com

## Links Úteis

- [Render Free Tier](https://render.com/docs/free)
- [Gunicorn Documentation](https://docs.gunicorn.org/)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/)
- [UptimeRobot (Keep Alive)](https://uptimerobot.com/)
