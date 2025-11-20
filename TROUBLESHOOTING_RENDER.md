# 🔧 Troubleshooting - Deploy no Render.com

## ❌ Erro: `ModuleNotFoundError: No module named 'settings'`

### Causa
O Render.com está tentando importar o módulo `settings` ao invés de `lista_presentes.settings`. Isso acontece porque há uma **variável de ambiente manual no dashboard** que sobrescreve o `render.yaml`.

### Solução 1: Corrigir Variável no Dashboard (Recomendado)

1. **Acesse o Dashboard do Render.com**
   - Vá para: https://dashboard.render.com
   - Selecione seu serviço `lista-presentes`

2. **Encontre a variável DJANGO_SETTINGS_MODULE**
   - Clique na aba **"Environment"**
   - Procure por `DJANGO_SETTINGS_MODULE`

3. **Corrija o valor**
   - Se encontrar a variável com valor `settings`:
     - Clique em **"Edit"**
     - Altere para: `lista_presentes.settings`
     - Clique em **"Save Changes"**

   - Se não encontrar a variável:
     - Isso é estranho, pois o erro indica que ela existe
     - Vá para a **Solução 2**

4. **Force um novo deploy**
   - Clique em **"Manual Deploy"** → **"Deploy latest commit"**

---

### Solução 2: Deletar e Recriar o Serviço (Mais Confiável)

1. **Deletar serviço existente**
   - No dashboard, selecione `lista-presentes`
   - Vá em **"Settings"** → Role até o final
   - Clique em **"Delete Web Service"**
   - Confirme a exclusão

2. **Recriar usando Blueprint**
   - No dashboard, clique em **"New +"** → **"Blueprint"**
   - Conecte ao repositório: `Maxwbh/Lista_de_Presentes`
   - Selecione o branch: `claude/review-wishlist-system-01KfJhmcrfGbvMcnDhbE7pNx`
   - O Render detectará automaticamente o `render.yaml`
   - Clique em **"Apply"**

3. **Aguarde o deploy**
   - O build deve executar corretamente desta vez
   - Verifique os logs para confirmar

---

### Solução 3: Usar Script build.sh (Backup)

Se as soluções anteriores não funcionarem:

1. **Edite o render.yaml no repositório** para usar o script:
   ```yaml
   buildCommand: bash build.sh
   ```

2. **Commit e push**:
   ```bash
   git add build.sh render.yaml
   git commit -m "fix: Usar build.sh para garantir DJANGO_SETTINGS_MODULE correto"
   git push
   ```

3. **Deploy novamente no Render**

---

## ✅ Verificação Pós-Deploy

Após o deploy bem-sucedido:

### 1. Testar a aplicação
   - Acesse: `https://lista-presentes.onrender.com`
   - Deve carregar a página de login

### 2. Criar superusuário
   ```bash
   # No dashboard Render, vá em "Shell" e execute:
   python manage.py createsuperuser
   ```

### 3. Acessar o admin
   - Vá para: `https://lista-presentes.onrender.com/admin/`
   - Faça login com o superusuário criado

---

## 🐛 Outros Erros Comuns

### Erro: `disks are not supported for free tier services`
**Solução**: Já corrigido no `render.yaml` (commit `8fd9fb0`)

### Erro: `Dependency on app with no migrations: presentes`
**Solução**: Já corrigido, migrations criadas (commit `c805800`)

### Erro: `ALLOWED_HOSTS`
**Solução**: Adicione no dashboard:
```
ALLOWED_HOSTS = .onrender.com
```

### Erro: Database connection
**Solução**: Verifique se o banco PostgreSQL foi criado e está conectado:
- Dashboard → Seu serviço → "Environment"
- Verifique se `DATABASE_URL` aponta para o banco correto

---

## 📞 Suporte

Se nenhuma solução funcionar:

1. **Verifique os logs completos**:
   - Dashboard → Seu serviço → "Logs"
   - Copie o erro completo

2. **Verifique estrutura do projeto**:
   ```bash
   ls -la
   # Deve mostrar:
   # - manage.py
   # - lista_presentes/
   # - presentes/
   # - render.yaml
   ```

3. **Verifique o arquivo settings.py**:
   ```bash
   cat lista_presentes/settings.py | head -20
   # Deve começar com:
   # import os
   # from pathlib import Path
   # import dj_database_url
   ```

---

## 📚 Documentação Oficial

- [Render.com Docs - Django](https://render.com/docs/deploy-django)
- [Render.com Docs - Troubleshooting](https://render.com/docs/troubleshooting-deploys)
- [Django Docs - Settings](https://docs.djangoproject.com/en/5.0/topics/settings/)
