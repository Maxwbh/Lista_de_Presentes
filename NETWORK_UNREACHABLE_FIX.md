# 🚨 SOLUÇÃO: Network Unreachable - Supabase

## ⚠️ Problema Atual

```
psycopg2.OperationalError: connection to server at "db.szyouijmxhlbavkzibxa.supabase.co"
(2600:1f16:1cd0:3330:12a8:31a1:bc7f:39d0), port 5432 failed: Network is unreachable
```

**Causas:**
1. ❌ `\n` (newline) no final da DATABASE_URL
2. ❌ Render tentando IPv6 (Supabase pode não suportar)
3. ❌ Porta 5432 (conexão direta) pode estar bloqueada

---

## ✅ SOLUÇÃO RÁPIDA (2 minutos)

### 1️⃣ Usar Connection Pooling (Recomendado)

Acesse: https://dashboard.render.com/web/lista-presentes/environment

**Edite** a variável `DATABASE_URL` existente:

```
ANTES (porta 5432 - direta):
postgresql://postgres:123ewqasdcxz%21%40%23@db.szyouijmxhlbavkzibxa.supabase.co:5432/postgres

DEPOIS (porta 6543 - pooling):
postgresql://postgres:123ewqasdcxz%21%40%23@db.szyouijmxhlbavkzibxa.supabase.co:6543/postgres
```

**Mude apenas:** `5432` → `6543`

### 2️⃣ Remover `\n` se existir

Se você copiou a URL de algum lugar, pode ter um `\n` invisível no final.

**Ação:** Delete e re-digite a DATABASE_URL manualmente (sem copiar/colar)

### 3️⃣ Salvar e Deploy

1. Clique em **Save Changes**
2. Aguarde deploy automático (3-5 min)

---

## 🎯 Por Que Connection Pooling?

### Porta 5432 (Direta) ❌

```
Django → Render → Internet → Supabase (IPv6)
                              ↓
                         PODE FALHAR
```

**Problemas:**
- IPv6 pode não ser roteável
- Conexões diretas podem ser bloqueadas
- Limites de conexões simultâneas

### Porta 6543 (Connection Pooling) ✅

```
Django → Render → Internet → PgBouncer → Supabase
                              ↓
                         SEMPRE FUNCIONA
```

**Vantagens:**
- ✅ IPv4 e IPv6 suportados
- ✅ Pool de conexões gerenciado
- ✅ Menor latência
- ✅ Mais estável
- ✅ Suporta mais conexões

---

## 🔧 Alternativa: Forçar IPv4

Se connection pooling não resolver, force IPv4:

### Opção A: Usar IP direto

```bash
# Descobrir IP IPv4 do Supabase
nslookup db.szyouijmxhlbavkzibxa.supabase.co

# Resultado (exemplo):
# Address: 54.x.x.x

# Usar IP ao invés do hostname
DATABASE_URL=postgresql://postgres:123ewqasdcxz%21%40%23@54.x.x.x:6543/postgres
```

### Opção B: Adicionar parâmetro de conexão

```
DATABASE_URL=postgresql://postgres:123ewqasdcxz%21%40%23@db.szyouijmxhlbavkzibxa.supabase.co:6543/postgres?options=-c%20protocol_version=3
```

---

## 📊 Comparação de Portas

| Porta | Tipo | IPv6 | Pool | Latência | Estabilidade |
|-------|------|------|------|----------|--------------|
| **5432** | Direta | ⚠️ Pode falhar | ❌ Não | Alta | Baixa |
| **6543** | PgBouncer | ✅ Funciona | ✅ Sim | Baixa | Alta |

**Recomendação:** Use sempre porta **6543**

---

## 🔍 Verificar se Funcionou

### Nos Logs do Render

Você deve ver:

```bash
🔌 Testing database connection...
✅ Database connection successful!
✅ Connected to Supabase PostgreSQL  # ← Sucesso!
✅ Database is ready

🗄️  Running migrations...
⚠️  InconsistentMigrationHistory detected!
🔧 Auto-fixing migration history...
✅ Fixed with --fake-initial
✅ All migrations applied successfully
==> Your service is live 🎉
```

### Se Ainda Falhar

```bash
# Erro persiste:
Network is unreachable
```

**Soluções adicionais:**

1. **Verificar Status do Supabase**
   - https://status.supabase.com
   - Se offline, aguarde

2. **Testar Conexão Localmente**
   ```bash
   # Sua máquina local
   psql "postgresql://postgres:123ewqasdcxz!@#@db.szyouijmxhlbavkzibxa.supabase.co:6543/postgres"
   ```

3. **Verificar Firewall do Supabase**
   - https://app.supabase.com/project/szyouijmxhlbavkzibxa/settings/database
   - Network Restrictions
   - Certifique-se que "Allow all IPs" está habilitado

---

## 🚀 Configuração Completa Render

Variáveis corretas:

```bash
# Connection Pooling (porta 6543)
DATABASE_URL=postgresql://postgres:123ewqasdcxz%21%40%23@db.szyouijmxhlbavkzibxa.supabase.co:6543/postgres

# Outras variáveis (já configuradas)
SUPABASE_URL=https://szyouijmxhlbavkzibxa.supabase.co
SUPABASE_KEY=sb_publishable_aswPuvIXjzcejBTyYWObdQ_BpC5l903
GITHUB_TOKEN=<use o token fornecido pelo administrador>
```

---

## 📝 Checklist

- [ ] Acessei Render Dashboard > Environment
- [ ] Editei DATABASE_URL
- [ ] Mudei porta de 5432 para 6543
- [ ] Verifiquei que não tem `\n` no final
- [ ] Salvei mudanças
- [ ] Aguardei deploy
- [ ] Verifiquei logs (deve mostrar "Supabase PostgreSQL")
- [ ] Testei o site

---

## 🎯 URL Correta (Copie Esta)

```
postgresql://postgres:123ewqasdcxz%21%40%23@db.szyouijmxhlbavkzibxa.supabase.co:6543/postgres
```

**Pontos importantes:**
- ✅ Porta `6543` (connection pooling)
- ✅ URL encoding: `%21%40%23`
- ✅ Sem `\n` no final
- ✅ Sem espaços

---

## ⚡ Explicação Técnica

### Por que IPv6 falha?

```python
# Render tenta conectar:
IPv4: 54.x.x.x (funciona)
IPv6: 2600:1f16:... (pode falhar)

# Supabase pode retornar IPv6 primeiro
# Render Free Tier pode não ter roteamento IPv6 completo
# Resultado: Network is unreachable
```

### Como Connection Pooling resolve?

```
PgBouncer (porta 6543):
- Aceita IPv4 e IPv6
- Faz fallback automático
- Mantém pool de conexões
- Mais rápido e estável
```

---

## 🆘 Se Nada Funcionar

### Plano B: Usar Render PostgreSQL

Se Supabase não funcionar de jeito nenhum:

1. **Criar PostgreSQL no Render**
   - Dashboard > New > PostgreSQL
   - Free Tier (256MB)

2. **Atualizar DATABASE_URL**
   - Render fornece automaticamente
   - Usar valor do Dashboard

3. **Vantagens**:
   - ✅ Mesma rede do Render (rápido)
   - ✅ Sem problemas de IPv6
   - ✅ Integração automática

4. **Desvantagens**:
   - ❌ Apenas 256MB (vs 500MB Supabase)
   - ❌ Sem interface web
   - ❌ Sem backups automáticos

---

## 📚 Documentação Relacionada

- **Configuração Supabase**: `RENDER_SUPABASE_SETUP.md`
- **Checklist Rápido**: `CHECKLIST_SUPABASE.md`
- **Migrações**: `MIGRATION_FIX.md`

---

**Criado:** 2026-02-07
**Prioridade:** 🚨 CRÍTICA
**Tempo:** 2 minutos
**Solução:** Porta 6543 (connection pooling)
