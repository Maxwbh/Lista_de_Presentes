# ✅ Checklist Rápido - Configuração Supabase no Render

## 🎯 Antes de Começar

- [ ] Você está usando **Render Free Tier**
- [ ] Você tem acesso ao **Render Dashboard**: https://dashboard.render.com
- [ ] Você tem as credenciais do **Supabase** (abaixo)

---

## 🔑 Credenciais do Supabase

```bash
SUPABASE_URL=https://szyouijmxhlbavkzibxa.supabase.co
SUPABASE_KEY=sb_publishable_aswPuvIXjzcejBTyYWObdQ_BpC5l903
DATABASE_URL=postgresql://postgres:123ewqasdcxz%21%40%23@db.szyouijmxhlbavkzibxa.supabase.co:5432/postgres
```

⚠️ **ATENÇÃO**: Note o URL encoding na senha (`%21%40%23` = `!@#`)

---

## 📝 Passos no Render Dashboard

### 1️⃣ Acessar o Serviço

- [ ] Abrir https://dashboard.render.com
- [ ] Clicar em **lista-presentes**
- [ ] Ir para aba **Environment**

### 2️⃣ Remover DATABASE_URL Antiga (se existir)

- [ ] Procurar por `DATABASE_URL`
- [ ] Se existir (apontando para Render PostgreSQL):
  - [ ] Clicar nos 3 pontos (...)
  - [ ] Clicar em **Delete**
  - [ ] Confirmar

### 3️⃣ Adicionar Variáveis do Supabase

Clicar em **Add Environment Variable** 3 vezes e adicionar:

#### Variável 1: DATABASE_URL (OBRIGATÓRIA)
```
Key:   DATABASE_URL
Value: postgresql://postgres:123ewqasdcxz%21%40%23@db.szyouijmxhlbavkzibxa.supabase.co:5432/postgres
```
- [ ] Adicionada

#### Variável 2: SUPABASE_URL (OPCIONAL)
```
Key:   SUPABASE_URL
Value: https://szyouijmxhlbavkzibxa.supabase.co
```
- [ ] Adicionada

#### Variável 3: SUPABASE_KEY (OPCIONAL)
```
Key:   SUPABASE_KEY
Value: sb_publishable_aswPuvIXjzcejBTyYWObdQ_BpC5l903
```
- [ ] Adicionada

### 4️⃣ Salvar e Deploy

- [ ] Clicar em **Save Changes**
- [ ] Aguardar deploy automático (3-5 minutos)

---

## 🔍 Verificar Logs do Deploy

### 5️⃣ Acompanhar o Build

- [ ] Ir para aba **Logs**
- [ ] Procurar por estas mensagens de sucesso:

```
✅ Database connection successful!
✅ Connected to Supabase PostgreSQL
✅ Database is ready
🔄 Creating migrations...
🗄️  Running migrations...
✅ All migrations applied successfully
✅ Build completed successfully!
```

### 6️⃣ Verificar Erros (se houver)

Se aparecer erro, verificar:

#### ❌ "password authentication failed"
**Solução**: Verifique se copiou a DATABASE_URL corretamente (com `%21%40%23`)

#### ❌ "could not connect to server"
**Solução**:
1. Verifique se o Supabase está online: https://status.supabase.com
2. Teste a conexão localmente: `python scripts/test_supabase_connection.py`

#### ❌ "too many connections"
**Solução**: Use connection pooling na porta 6543:
```
postgresql://postgres:123ewqasdcxz%21%40%23@db.szyouijmxhlbavkzibxa.supabase.co:6543/postgres
```

---

## 🧪 Testar a Aplicação

### 7️⃣ Acessar o Site

- [ ] Clicar no link do site no topo do Dashboard
- [ ] Site abre sem erros

### 8️⃣ Testar Funcionalidades

- [ ] **Login**: Fazer login funciona
- [ ] **Dashboard**: Cards de estatísticas aparecem
- [ ] **Meus Presentes**: Lista de presentes carrega
- [ ] **Adicionar Presente**: Consegue adicionar novo presente
- [ ] **Ver Usuários**: Lista de usuários aparece

---

## 🗄️ Verificar no Supabase Dashboard

### 9️⃣ Acessar Supabase

- [ ] Abrir https://app.supabase.com
- [ ] Fazer login
- [ ] Selecionar projeto: **szyouijmxhlbavkzibxa**

### 🔟 Verificar Tabelas

- [ ] Menu lateral: **Table Editor**
- [ ] Ver tabelas criadas:
  - [ ] `auth_user`
  - [ ] `presentes_usuario`
  - [ ] `presentes_presente`
  - [ ] `presentes_grupo`
  - [ ] Outras tabelas do Django

### 1️⃣1️⃣ Verificar Dados

- [ ] Clicar em `presentes_usuario`
- [ ] Ver dados dos usuários
- [ ] Verificar se dados foram migrados corretamente

---

## 🧹 Limpeza (Opcional)

### 1️⃣2️⃣ Remover PostgreSQL do Render

**⚠️ SOMENTE FAÇA ISSO DEPOIS QUE TUDO ESTIVER FUNCIONANDO!**

Se você tinha um banco PostgreSQL gerenciado pelo Render:

- [ ] **ANTES**: Fazer backup dos dados (se necessário)
- [ ] No Dashboard, ir para **Databases**
- [ ] Clicar em `lista-presentes-db`
- [ ] Clicar nos 3 pontos (...)
- [ ] Clicar em **Delete Database**
- [ ] Digitar o nome do banco para confirmar
- [ ] Clicar em **Delete**

**Benefícios**:
- ✅ Libera recursos no Render Free Tier
- ✅ Evita confusão entre bancos
- ✅ Supabase é mais robusto

---

## 🎉 Checklist Final

Tudo funcionando? Marque todos:

- [ ] ✅ DATABASE_URL configurada
- [ ] ✅ SUPABASE_URL configurada (opcional)
- [ ] ✅ SUPABASE_KEY configurada (opcional)
- [ ] ✅ Deploy concluído sem erros
- [ ] ✅ Logs mostram "Connected to Supabase PostgreSQL"
- [ ] ✅ Site acessível e funcionando
- [ ] ✅ Login funciona
- [ ] ✅ Dados aparecem corretamente
- [ ] ✅ Tabelas visíveis no Supabase
- [ ] ✅ PostgreSQL antigo removido (opcional)

---

## 📊 Vantagens que Você Ganhou

Agora você tem:

- ✅ **500 MB de armazenamento** (vs 256 MB Render Free)
- ✅ **Backup automático** (7 dias de retenção)
- ✅ **Interface web** para gerenciar dados
- ✅ **API REST automática** para todas as tabelas
- ✅ **Não expira** por inatividade
- ✅ **Monitoring** e logs em tempo real
- ✅ **Extensões PostgreSQL** disponíveis

---

## 🆘 Precisa de Ajuda?

### Documentação Detalhada
📖 Ver arquivo: `RENDER_SUPABASE_SETUP.md`

### Script de Teste
🔧 Testar conexão localmente:
```bash
python scripts/test_supabase_connection.py
```

### Logs do Render
📋 Ver logs em tempo real:
```
https://dashboard.render.com > lista-presentes > Logs
```

### Logs do Supabase
📊 Ver logs do PostgreSQL:
```
https://app.supabase.com/project/szyouijmxhlbavkzibxa > Logs > Postgres Logs
```

---

## ⏱️ Tempo Estimado

- Configuração no Render: **2-3 minutos**
- Deploy automático: **3-5 minutos**
- Verificação e testes: **2-3 minutos**
- **Total**: ~10 minutos

---

## 🚀 Próximos Passos

Após concluir este checklist:

1. **Explorar Supabase Dashboard**
   - Table Editor para visualizar dados
   - SQL Editor para queries personalizadas
   - Monitoring para acompanhar uso

2. **Configurar Backups**
   - Backups automáticos já estão ativos (7 dias)
   - Para backups manuais, use pg_dump

3. **Habilitar Extensões** (opcional)
   ```sql
   -- No SQL Editor
   CREATE EXTENSION IF NOT EXISTS "postgis";
   CREATE EXTENSION IF NOT EXISTS "pg_cron";
   ```

4. **Configurar Alertas** (opcional)
   - Settings > Database > Monitoring
   - Alertas para uso de disco, conexões, etc.

---

**Última atualização**: 2026-02-06
**Versão do projeto**: 1.1.18
**Tier**: Render Free + Supabase Free
