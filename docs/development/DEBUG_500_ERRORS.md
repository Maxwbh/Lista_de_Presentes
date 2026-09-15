# 🐛 Como Debugar Erros 500 no Render.com

## 🔍 O que é um Erro 500?

Erro 500 (Internal Server Error) significa que o servidor encontrou um problema ao processar sua requisição. Pode ser causado por:

- ❌ Erro no código Python (exception não tratada)
- ❌ Banco de dados não conectado
- ❌ Template não encontrado
- ❌ Variável de ambiente faltando
- ❌ Permissões incorretas
- ❌ Dependências faltando

---

## 📊 PASSO 1: Verificar Logs no Render.com

### Acessar Logs

1. Vá para: https://dashboard.render.com
2. Clique no seu serviço: `lista-presentes`
3. Clique em **"Logs"**

### Procurar por Erros

#### Logs de Erro (vermelho)

Procure por linhas com:
```
ERROR
Traceback (most recent call last)
Exception
ImportError
ModuleNotFoundError
OperationalError
TemplateDoesNotExist
```

#### Exemplo de Log de Erro:

```python
ERROR 2025-11-20 15:58:59 django.request Internal Server Error: /meus-presentes/
Traceback (most recent call last):
  File "/app/presentes/views.py", line 81, in meus_presentes_view
    presentes_list = Presente.objects.filter(usuario=request.user)
  File "django/db/backends/base/base.py", line 259, in __exit__
    connection.close()
django.db.utils.OperationalError: FATAL: password authentication failed for user "lista_user"
```

Neste exemplo, o erro é **conexão com banco de dados**.

---

## 🔧 PASSO 2: Diagnóstico por Tipo de Erro

### Erro: `OperationalError: FATAL: password authentication failed`

**Causa**: DATABASE_URL incorreto ou banco não conectado

**Solução**:
1. Dashboard → Seu serviço → **"Environment"**
2. Verificar `DATABASE_URL`
3. Deve apontar para o banco PostgreSQL
4. Se vazio, editar e selecionar: **"From Database"** → `lista-presentes-db`

---

### Erro: `TemplateDoesNotExist at /meus-presentes/`

**Causa**: Template não encontrado ou nome incorreto

**Solução**:
1. Verificar se os templates foram enviados no build:
   ```
   Build logs: "Copying templates..."
   ```
2. Verificar TEMPLATES em settings.py:
   ```python
   'DIRS': [BASE_DIR / 'templates'],
   ```

---

### Erro: `ModuleNotFoundError: No module named 'presentes'`

**Causa**: App não está em INSTALLED_APPS ou erro de import

**Solução**:
1. Dashboard → **"Environment"** → Verificar `DJANGO_SETTINGS_MODULE`
2. Deve ser: `lista_presentes.settings`
3. Verificar build logs para erros de instalação

---

### Erro: `ImproperlyConfigured: The SECRET_KEY setting must not be empty`

**Causa**: SECRET_KEY não está configurada

**Solução**:
1. Dashboard → **"Environment"**
2. Verificar se `SECRET_KEY` existe
3. Se não, adicionar:
   ```
   SECRET_KEY = [Gerar valor aleatório]
   ```

---

### Erro: `django.core.exceptions.DisallowedHost`

**Causa**: Host não está em ALLOWED_HOSTS

**Solução**:
1. Dashboard → **"Environment"**
2. Editar `ALLOWED_HOSTS`:
   ```
   .onrender.com,lista-presentes-im4b.onrender.com
   ```

---

### Erro: `Worker timeout` ou `WORKER TIMEOUT`

**Causa**: Requisição demorou mais de 120 segundos

**Solução**:
1. Otimizar queries do banco de dados
2. Adicionar cache
3. Reduzir workers:
   ```yaml
   gunicorn --workers 1 ...
   ```

---

### Erro: `Out of memory` ou `SIGKILL`

**Causa**: Aplicação excedeu limite de RAM (~512 MB no free tier)

**Solução**:
1. Reduzir workers para 1:
   ```yaml
   gunicorn --workers 1 --threads 2 ...
   ```
2. Ou fazer upgrade para plano pago

---

## 🔍 PASSO 3: Comandos no Shell para Debug

Acesse: Dashboard → Seu serviço → **"Shell"**

### Testar Imports

```bash
# Testar import do Django
python -c "import django; print(django.get_version())"

# Testar import do WSGI
python -c "from lista_presentes.wsgi import application; print('OK')"

# Testar import dos models
python -c "from presentes.models import Usuario, Presente; print('OK')"
```

### Testar Banco de Dados

```bash
# Verificar conexão
python manage.py check --database default

# Executar query simples
python manage.py shell
>>> from presentes.models import Usuario
>>> Usuario.objects.count()
>>> exit()
```

### Testar Templates

```bash
# Listar templates
find /opt/render/project/src/templates -name "*.html"

# Verificar template específico
cat /opt/render/project/src/templates/presentes/meus_presentes.html | head -20
```

### Verificar Variáveis de Ambiente

```bash
# Listar variáveis importantes
env | grep -E "DJANGO|DATABASE|ALLOWED|DEBUG|SECRET"

# Verificar DJANGO_SETTINGS_MODULE
echo $DJANGO_SETTINGS_MODULE
# Esperado: lista_presentes.settings
```

---

## 📝 PASSO 4: Interpretar Logs com Novo Sistema

Após o commit com logging melhorado, os logs mostrarão:

### Log de Erro Detalhado:

```
ERROR 2025-11-20 16:00:00 error_handlers 500 Internal Server Error: Traceback...
ERROR 2025-11-20 16:00:00 error_handlers Request path: /meus-presentes/
ERROR 2025-11-20 16:00:00 error_handlers Request method: GET
ERROR 2025-11-20 16:00:00 error_handlers User: AnonymousUser
```

### Interpretação:

- **User: AnonymousUser** = Usuário não autenticado
- **Request path: /meus-presentes/** = Tentou acessar página protegida
- **Traceback...** = Detalhes do erro Python

---

## ✅ PASSO 5: Soluções Comuns

### Solução 1: Usuário Não Autenticado Acessando Página Protegida

Se o erro mostra `User: AnonymousUser` e a rota é `/meus-presentes/`:

**Problema**: Usuário não logado tentando acessar página com `@login_required`

**Comportamento Esperado**: Deveria redirecionar para `/login/`

**Causa Provável**: Erro no redirect ou LOGIN_URL incorreto

**Verificar**:
```python
# settings.py
LOGIN_URL = '/login/'  # ✅ Deve estar assim
```

---

### Solução 2: Banco de Dados Não Conectado

**Sintomas**:
```
OperationalError: FATAL: ...
```

**Passos**:
1. Verificar DATABASE_URL aponta para o banco correto
2. Verificar se o banco PostgreSQL está "Available" (verde)
3. Testar conexão no shell: `python manage.py check --database default`

---

### Solução 3: Rebuild Completo

Se nada funcionar:

1. Dashboard → Seu serviço → **"Manual Deploy"**
2. Clique em **"Clear build cache & deploy"**
3. Aguarde 5-10 minutos
4. Verifique os logs novamente

---

## 🎯 Checklist de Debug

Execute na ordem:

- [ ] 1. Acessar logs no dashboard
- [ ] 2. Procurar por "ERROR" ou "Traceback"
- [ ] 3. Identificar tipo de erro (DB, template, import, etc.)
- [ ] 4. Verificar variáveis de ambiente relevantes
- [ ] 5. Testar imports no shell
- [ ] 6. Testar conexão com banco
- [ ] 7. Aplicar solução específica do erro
- [ ] 8. Fazer redeploy se necessário
- [ ] 9. Verificar logs após redeploy
- [ ] 10. Testar aplicação novamente

---

## 📞 Erros Específicos Conhecidos

### Erro ao acessar /meus-presentes/ sem login

**Log**:
```
Request path: /meus-presentes/
User: AnonymousUser
```

**Causa**: Usuário não autenticado tentando acessar página protegida

**Solução**:
1. Acesse primeiro: https://lista-presentes-im4b.onrender.com/login/
2. Faça login
3. Depois acesse /meus-presentes/

**Para criar usuário**:
1. Dashboard → Shell
2. `python manage.py createsuperuser`
3. Seguir instruções

---

### Erro ao fazer login: CSRF verification failed

**Causa**: Cookies não configurados corretamente com SSL

**Solução**: Já corrigido no commit com:
```python
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = False  # Render já faz redirect
```

---

## 🔄 Após Correções

Sempre:

1. ✅ Fazer commit e push
2. ✅ Aguardar redeploy automático (ou manual)
3. ✅ Verificar logs de build: `Build successful 🎉`
4. ✅ Verificar logs de runtime: `Listening at: http://0.0.0.0:10000`
5. ✅ Testar aplicação
6. ✅ Verificar logs novamente se houver erro

---

## 📚 Links Úteis

- **Dashboard**: https://dashboard.render.com
- **Logs**: Dashboard → Seu serviço → Logs
- **Shell**: Dashboard → Seu serviço → Shell
- **Environment**: Dashboard → Seu serviço → Environment
- **Docs Render**: https://render.com/docs/troubleshooting-deploys

---

**Última atualização**: Commit com logging e error handlers customizados
