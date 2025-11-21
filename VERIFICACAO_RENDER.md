# 🔧 Guia de Verificação - Deploy Render.com

## 📊 Informações do Deploy

- **URL**: https://lista-presentes-0hbp.onrender.com
- **Porta**: 10000
- **Status Atual**: 503 Service Unavailable

---

## ✅ Checklist de Verificação no Dashboard

### 1. **Verificar Logs do Deploy**

Acesse: https://dashboard.render.com → Seu serviço → **"Logs"**

#### Logs de Build (devem mostrar):
```
✅ Build completed successfully!
✅ Uploaded in XX.Xs
✅ Build successful 🎉
```

#### Logs de Runtime (procurar por erros):
```bash
# Esperado (sucesso):
[INFO] Starting gunicorn XX.X.X
[INFO] Listening at: http://0.0.0.0:10000
[INFO] Using worker: sync
[INFO] Booting worker with pid: XXXX

# Erros comuns a procurar:
- ImportError
- ModuleNotFoundError
- django.core.exceptions.ImproperlyConfigured
- gunicorn.errors.HaltServer
- Worker timeout
- Out of memory
```

---

### 2. **Verificar Variáveis de Ambiente**

Acesse: Dashboard → Seu serviço → **"Environment"**

#### Variáveis Obrigatórias:

| Variável | Valor Esperado | Status |
|----------|----------------|--------|
| `DJANGO_SETTINGS_MODULE` | `lista_presentes.settings` | ⚠️ **Verificar** |
| `SECRET_KEY` | (gerado automaticamente) | ✅ |
| `DEBUG` | `false` | ✅ |
| `ALLOWED_HOSTS` | `.onrender.com,lista-presentes-0hbp.onrender.com` | ⚠️ **Verificar** |
| `DATABASE_URL` | `postgresql://...` (do banco) | ⚠️ **Verificar** |
| `PORT` | `10000` (automático) | ✅ |

#### Verificações Importantes:

**a) DJANGO_SETTINGS_MODULE**
- [ ] Verifique se está como `lista_presentes.settings`
- [ ] Se estiver como `settings`, **EDITE** para `lista_presentes.settings`

**b) ALLOWED_HOSTS**
- [ ] Deve conter `.onrender.com` OU seu domínio específico
- [ ] **Sugestão**: `lista-presentes-0hbp.onrender.com,.onrender.com`

**c) DATABASE_URL**
- [ ] Deve apontar para o banco PostgreSQL criado
- [ ] Formato: `postgresql://usuario:senha@host:5432/database`
- [ ] Verificar se o banco está conectado (veja seção 3)

---

### 3. **Verificar Conexão com Banco de Dados**

Acesse: Dashboard → Seu serviço → **"Environment"** → **DATABASE_URL**

#### Verificar se o banco existe:
- Dashboard → **"PostgreSQL"** → `lista-presentes-db`
- Status deve ser: **"Available"** (verde)

#### Se DATABASE_URL estiver vazio ou incorreto:
1. Vá em **"Environment"**
2. Encontre `DATABASE_URL`
3. Clique em **"Edit"**
4. Selecione: **"From Database"** → `lista-presentes-db` → **"Internal Database URL"**
5. Salve

---

### 4. **Verificar Health Check**

Acesse: Dashboard → Seu serviço → **"Settings"** → **"Health Check Path"**

- [ ] Deve estar configurado como: `/health/`
- [ ] Se estiver diferente, edite para `/health/`

---

### 5. **Verificar Port Binding**

No dashboard, verifique os logs de runtime:

#### Procurar por:
```
Listening at: http://0.0.0.0:10000
```

#### Se não aparecer:
- Gunicorn não está iniciando corretamente
- Veja os erros nos logs (seção 1)

---

### 6. **Verificar Recursos (Plano Free)**

O plano **free** tem limitações:

| Recurso | Limite | Status |
|---------|--------|--------|
| RAM | ~512 MB | ⚠️ Pode causar crashes |
| CPU | Compartilhado | ⚠️ Pode ser lento |
| Workers | Máx 2 recomendado | ✅ Configurado |
| Sleep | 15 min inatividade | ⚠️ Primeiro acesso lento |

#### Se houver erro de memória nos logs:
```
Worker (pid:XXXX) was sent SIGKILL! Perhaps out of memory?
```

**Solução**: Reduzir workers no `render.yaml`:
```yaml
gunicorn --workers 1 ...
```

---

## 🐛 Troubleshooting por Tipo de Erro

### Erro 503 (Service Unavailable)

**Causas Possíveis**:

1. **Gunicorn não está rodando**
   - Verifique logs de runtime
   - Procure por erros Python

2. **Worker timeout**
   - Gunicorn mata workers que demoram >120s
   - Verifique logs: `WORKER TIMEOUT`

3. **Falta de memória**
   - Plano free tem pouca RAM
   - Reduza workers para 1

4. **Erro no código Python**
   - Verifique logs de import errors
   - Teste localmente primeiro

---

### Erro 502 (Bad Gateway)

**Causas Possíveis**:

1. **Gunicorn crashou**
   - Verifique logs para stack trace

2. **Porta incorreta**
   - Gunicorn deve usar `$PORT` (10000)

---

### Erro 404 (Not Found)

**Causas Possíveis**:

1. **URLs não configuradas**
   - ✅ Já corrigido no commit `2332538`

2. **Health check path incorreto**
   - Verificar se está `/health/`

---

## 🔍 Comandos de Verificação no Shell

Acesse: Dashboard → Seu serviço → **"Shell"**

### Testar importação do Django:
```bash
python -c "import django; print(django.get_version())"
# Esperado: 5.0
```

### Testar importação do WSGI:
```bash
python -c "from lista_presentes.wsgi import application; print('OK')"
# Esperado: OK
```

### Testar conexão com banco:
```bash
python manage.py check --database default
# Esperado: System check identified no issues
```

### Listar variáveis de ambiente:
```bash
env | grep -E "DJANGO|DATABASE|ALLOWED|DEBUG|SECRET"
```

### Testar migrations:
```bash
python manage.py showmigrations
# Esperado: [X] 0001_initial
```

---

## 🚀 Soluções Rápidas

### Solução 1: Redeployar

1. Dashboard → Seu serviço → **"Manual Deploy"**
2. Clique em **"Clear build cache & deploy"**
3. Aguarde 5-10 minutos

---

### Solução 2: Verificar e Corrigir Variáveis

1. Dashboard → **"Environment"**
2. Editar `DJANGO_SETTINGS_MODULE`: `lista_presentes.settings`
3. Editar `ALLOWED_HOSTS`: `lista-presentes-0hbp.onrender.com,.onrender.com`
4. Salvar e aguardar redeploy automático

---

### Solução 3: Reduzir Workers (se problema de memória)

**No dashboard**, adicionar variável de ambiente:

```
GUNICORN_CMD_ARGS = --workers=1 --threads=2 --timeout=120
```

Ou editar `render.yaml` localmente:
```yaml
gunicorn --bind 0.0.0.0:$PORT --workers 1 --timeout 120 ...
```

---

### Solução 4: Deletar e Recriar Serviço

Se nada funcionar:

1. Dashboard → Seu serviço → **"Settings"** → Role até o final
2. **"Delete Web Service"** → Confirme
3. Dashboard → **"New +"** → **"Blueprint"**
4. Repositório: `Maxwbh/Lista_de_Presentes`
5. Branch: `claude/review-wishlist-system-01KfJhmcrfGbvMcnDhbE7pNx`
6. **"Apply"**

---

## 📋 Checklist de Verificação Completa

Execute na ordem:

- [ ] 1. Verificar logs de build (deve ter sucesso)
- [ ] 2. Verificar logs de runtime (procurar erros)
- [ ] 3. Verificar `DJANGO_SETTINGS_MODULE` = `lista_presentes.settings`
- [ ] 4. Verificar `ALLOWED_HOSTS` inclui seu domínio
- [ ] 5. Verificar `DATABASE_URL` conectado ao banco
- [ ] 6. Verificar banco PostgreSQL está "Available"
- [ ] 7. Verificar health check path = `/health/`
- [ ] 8. Verificar logs mostram "Listening at: http://0.0.0.0:10000"
- [ ] 9. Testar importação WSGI no shell
- [ ] 10. Testar conexão com banco no shell

---

## 📞 Informações Adicionais

### Status Esperado após Correção:

```bash
# Health check
curl https://lista-presentes-0hbp.onrender.com/health/
# Resposta: OK (status 200)

# Login page
curl https://lista-presentes-0hbp.onrender.com/
# Resposta: HTML da página de login (status 200)
```

### Comandos Úteis no Shell:

```bash
# Ver configurações carregadas
python manage.py diffsettings

# Criar superuser
python manage.py createsuperuser

# Executar migrations
python manage.py migrate

# Coletar statics
python manage.py collectstatic --noinput

# Verificar sistema
python manage.py check
```

---

## 🎯 Resultado Esperado

Após correções, o serviço deve:

1. ✅ Build com sucesso
2. ✅ Gunicorn iniciando na porta 10000
3. ✅ Health check `/health/` retornando 200
4. ✅ Página de login acessível em `/`
5. ✅ Admin acessível em `/admin/`
6. ✅ PWA instalável no celular

---

**Última atualização**: Commit `2332538` - URLs e health check configurados
