# 🔒 Segurança Supabase - Row Level Security (RLS)

## ⚠️ Problema Detectado

O **Supabase Database Linter** detectou **27 erros de segurança críticos** nas tabelas Django:

### Erros RLS (23 tabelas)
```
❌ RLS Disabled in Public - Table 'public.django_migrations' is public, but RLS has not been enabled
❌ RLS Disabled in Public - Table 'public.presentes_usuario' is public, but RLS has not been enabled
❌ RLS Disabled in Public - Table 'public.django_session' is public, but RLS has not been enabled
... (20 mais)
```

### Colunas Sensíveis Expostas (4 tabelas)
```
❌ Table 'public.presentes_usuario' contains: password
❌ Table 'public.django_session' contains: session_key
❌ Table 'public.socialaccount_socialapp' contains: secret
❌ Table 'public.socialaccount_socialtoken' contains: token
```

---

## 🎯 Por Que Isso Acontece?

### Supabase vs Django

O **Supabase** expõe automaticamente o schema `public` via **PostgREST API**:

```
Internet → PostgREST API → public.* (TODAS as tabelas acessíveis!)
```

Sem **Row Level Security (RLS)**, qualquer pessoa pode fazer:

```bash
# ❌ RISCO: Acessar todos os usuários com senhas
curl https://szyouijmxhlbavkzibxa.supabase.co/rest/v1/presentes_usuario \
  -H "apikey: sb_publishable_aswPuvIXjzcejBTyYWObdQ_BpC5l903"

# ❌ RISCO: Acessar todas as sessões ativas
curl https://szyouijmxhlbavkzibxa.supabase.co/rest/v1/django_session \
  -H "apikey: sb_publishable_aswPuvIXjzcejBTyYWObdQ_BpC5l903"

# ❌ RISCO: Acessar todos os tokens OAuth
curl https://szyouijmxhlbavkzibxa.supabase.co/rest/v1/socialaccount_socialtoken \
  -H "apikey: sb_publishable_aswPuvIXjzcejBTyYWObdQ_BpC5l903"
```

### Django vs Supabase API

Este é um **Django app**, não um app nativo Supabase:

| Aspecto | Django (Atual) | Supabase API (Não usado) |
|---------|----------------|--------------------------|
| **Acesso aos dados** | Views Django | PostgREST API |
| **Autenticação** | Django Auth | Supabase Auth |
| **Autorização** | Django Permissions | RLS Policies |
| **Roteamento** | URLs Django | API REST automática |
| **Segurança** | Middleware Django | RLS |

**Conclusão:** Não precisamos da API PostgREST, apenas da conexão PostgreSQL!

---

## ✅ Solução Recomendada

### Opção 1: Habilitar RLS (RECOMENDADO)

Habilitar RLS em todas as tabelas **bloqueia a API** mas **mantém Django funcionando**:

#### 1️⃣ Executar Script SQL

```bash
# Abrir Supabase Dashboard
🔗 https://app.supabase.com/project/szyouijmxhlbavkzibxa/sql/new

# Copiar e colar o conteúdo de:
scripts/enable_rls_supabase.sql

# Executar (Run)
```

#### 2️⃣ Verificar Resultado

Após executar, o Database Linter mostrará:
```
✅ 0 security issues found!
```

#### 3️⃣ Como Funciona

```sql
-- Habilita RLS em todas as tabelas
ALTER TABLE public.presentes_usuario ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.django_session ENABLE ROW LEVEL SECURITY;
-- ... (todas as tabelas)

-- Sem políticas RLS = BLOQUEIA API
-- Django continua funcionando (role 'postgres' tem BYPASSRLS)
```

**Resultado:**
- ✅ Django funciona normalmente
- ✅ API PostgREST bloqueada (retorna 0 rows)
- ✅ Senhas e tokens protegidos
- ✅ 0 erros de segurança

---

### Opção 2: Desabilitar PostgREST API

Se você tem **certeza absoluta** que não usa a Supabase API:

#### 1️⃣ Supabase Dashboard

```
Settings > API Settings > PostgREST
[ ] Enable PostgREST (desmarcar)
```

#### 2️⃣ Vantagens/Desvantagens

**Vantagens:**
- ✅ API completamente desabilitada
- ✅ Não precisa de RLS
- ✅ Menor superfície de ataque

**Desvantagens:**
- ❌ Não pode usar Supabase JS Client
- ❌ Não pode usar Realtime
- ❌ Não pode usar Edge Functions com DB

**⚠️ CUIDADO:** Isso desabilita TODA a API Supabase, incluindo funcionalidades futuras.

---

### Opção 3: Mover para Schema Privado

Mover todas as tabelas Django para um schema privado não exposto pela API:

```sql
-- Criar schema privado
CREATE SCHEMA django;

-- Mover todas as tabelas
ALTER TABLE public.presentes_usuario SET SCHEMA django;
ALTER TABLE public.django_session SET SCHEMA django;
-- ... (todas as tabelas)

-- Atualizar search_path
ALTER DATABASE postgres SET search_path TO django, public;
```

**Desvantagens:**
- ⚠️ Complexo de implementar
- ⚠️ Precisa atualizar migrações Django
- ⚠️ Pode quebrar coisas

**NÃO RECOMENDADO** para este projeto.

---

## 📊 Comparação de Soluções

| Solução | Complexidade | Django OK? | API Bloqueada? | Recomendação |
|---------|--------------|------------|----------------|--------------|
| **RLS habilitado** | ⭐ Fácil | ✅ Sim | ✅ Sim | ✅ **RECOMENDADO** |
| **Desabilitar API** | ⭐ Fácil | ✅ Sim | ✅ Sim | ⚠️ Muito restritivo |
| **Schema privado** | ⭐⭐⭐ Difícil | ⚠️ Requer mudanças | ✅ Sim | ❌ Não vale a pena |

---

## 🔍 Verificar Segurança

### Teste 1: Verificar RLS Habilitado

```sql
-- Executar no Supabase SQL Editor
SELECT
    tablename,
    rowsecurity AS rls_enabled
FROM pg_tables
WHERE schemaname = 'public'
  AND (
    tablename LIKE 'django_%'
    OR tablename LIKE 'presentes_%'
    OR tablename LIKE 'auth_%'
    OR tablename LIKE 'account_%'
    OR tablename LIKE 'socialaccount_%'
  )
ORDER BY tablename;
```

**Resultado esperado:** Todas as linhas com `rls_enabled = true`

### Teste 2: Verificar API Bloqueada

```bash
# Tentar acessar usuários (deve retornar vazio)
curl https://szyouijmxhlbavkzibxa.supabase.co/rest/v1/presentes_usuario \
  -H "apikey: sb_publishable_aswPuvIXjzcejBTyYWObdQ_BpC5l903" \
  -H "Content-Type: application/json"
```

**Resultado esperado:** `[]` (lista vazia, não erro)

### Teste 3: Verificar Django Funcionando

```bash
# Acessar aplicação Django
curl https://lista-presentes-1iwb.onrender.com/

# Fazer login
# Criar presente
# Etc.
```

**Resultado esperado:** Tudo funciona normalmente

---

## 📚 Como RLS Funciona

### Sem RLS (INSEGURO)

```
API Request → PostgREST → SELECT * FROM presentes_usuario → ALL ROWS ❌
Django Request → PostgreSQL → SELECT * FROM presentes_usuario → ALL ROWS ✅
```

### Com RLS + Sem Políticas (SEGURO)

```
API Request → PostgREST → SELECT * FROM presentes_usuario → 0 ROWS (bloqueado) ✅
Django Request → PostgreSQL (role 'postgres' BYPASSRLS) → ALL ROWS ✅
```

### Roles PostgreSQL

| Role | BYPASSRLS? | Usado por |
|------|------------|-----------|
| `postgres` | ✅ Sim | Django (DATABASE_URL) |
| `authenticator` | ❌ Não | PostgREST API |
| `anon` | ❌ Não | API pública |
| `authenticated` | ❌ Não | API com auth |

**Por isso Django continua funcionando!** 🎉

---

## 🚀 Próximos Passos

### 1️⃣ URGENTE: Executar Script RLS

```bash
1. Abrir: https://app.supabase.com/project/szyouijmxhlbavkzibxa/sql/new
2. Copiar: scripts/enable_rls_supabase.sql
3. Colar no SQL Editor
4. Executar (Run)
5. Verificar: Database Linter (0 erros)
```

### 2️⃣ Verificar Aplicação Django

```bash
# Acessar site
https://lista-presentes-1iwb.onrender.com/

# Testar:
- Login ✅
- Criar presente ✅
- Ver lista ✅
- Logout ✅
```

### 3️⃣ Documentar

Adicionar ao `README.md`:
```markdown
## Segurança Supabase

Este projeto usa Supabase PostgreSQL com Row Level Security (RLS) habilitado.
Veja SUPABASE_SECURITY.md para detalhes.
```

---

## 🆘 Troubleshooting

### Erro: "permission denied for table presentes_usuario"

**Causa:** Role Django não tem permissões

**Solução:**
```sql
-- Dar permissões para role postgres
GRANT ALL ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO postgres;
```

### Erro: "new row violates row-level security policy"

**Causa:** Django está usando role sem BYPASSRLS

**Solução:** Verificar DATABASE_URL usa `postgres` user (não `authenticator`)

### API retorna erro ao invés de lista vazia

**Causa:** Erro na configuração RLS

**Solução:** Verificar que RLS está habilitado mas SEM políticas

---

## 🔗 Links Úteis

- **Supabase RLS Docs**: https://supabase.com/docs/guides/auth/row-level-security
- **Database Linter**: https://supabase.com/docs/guides/database/database-linter
- **PostgREST Docs**: https://postgrest.org/en/stable/auth.html
- **PostgreSQL RLS**: https://www.postgresql.org/docs/current/ddl-rowsecurity.html

---

**Última atualização:** 2026-02-07
**Status:** ⚠️ **AÇÃO NECESSÁRIA** - RLS precisa ser habilitado
**Severidade:** 🔴 **CRÍTICA** - Senhas e tokens expostos via API
**Solução:** Executar `scripts/enable_rls_supabase.sql` no Supabase Dashboard
