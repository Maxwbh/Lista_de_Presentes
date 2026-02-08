# Supabase PostgreSQL - Configuração Atual

## ✅ Status Atual

**Esta aplicação usa Supabase PostgreSQL com Schema Isolado `lista_presentes`.**

Configuração permite:
- ✅ Múltiplas apps Django no mesmo banco Supabase (isoladas por schema)
- ✅ 500MB Free Tier (vs 256MB Render PostgreSQL)
- ✅ Dashboard web para queries SQL
- ✅ Possibilidade de usar Supabase Storage/Auth/Realtime no futuro

**Schema:** `lista_presentes` (configurado automaticamente via `settings.py`)

---

## 📋 Configuração Supabase

### Vantagens
- ✅ Múltiplas apps Django isoladas no mesmo banco (via schemas)
- ✅ Mais armazenamento: 500 MB (vs 256 MB Render PostgreSQL)
- ✅ Dashboard web para queries SQL
- ✅ Supabase Storage/Auth/Realtime disponíveis

### Schema Isolado
- 📁 **Schema:** `lista_presentes` (configurado automaticamente)
- 🔒 **Isolamento:** Evita conflitos de `django_migrations` entre apps
- ⚙️ **Configuração:** Ver [SCHEMA_ISOLADO.md](SCHEMA_ISOLADO.md)

### Variáveis de Ambiente (Render Dashboard)

```bash
# Database Connection (Connection Pooler - porta 6543)
# IMPORTANTE: Não adicionar ?options= - search_path configurado automaticamente
DATABASE_URL=postgresql://postgres.YOUR_PROJECT_ID:YOUR_PASSWORD_ENCODED@aws-1-us-east-2.pooler.supabase.com:6543/postgres

# Supabase API (Opcional - uso futuro)
SUPABASE_URL=https://YOUR_PROJECT_ID.supabase.co
SUPABASE_KEY=sb_publishable_YOUR_ANON_KEY

# GitHub (Auto-create Issues)
GITHUB_TOKEN=<fornecido pelo administrador>
GITHUB_REPO_OWNER=Maxwbh
GITHUB_REPO_NAME=Lista_de_Presentes
GITHUB_AUTO_CREATE_ISSUES=True
```

**Configurar em:** https://dashboard.render.com/web/lista-presentes/environment

> 💡 **Nota:** O `search_path=lista_presentes` é aplicado automaticamente via `settings.py` (signal `connection_created`)

---

## 🔐 Segurança - Row Level Security (RLS)

### Status

✅ **RLS Habilitado** em todas as 23 tabelas Django:
- Banco de dados protegido contra acesso não autorizado via API PostgREST
- Django funciona normalmente (role `postgres` tem BYPASSRLS)
- Database Linter: 0 erros de segurança

### Script SQL Executado

```sql
-- Habilitar RLS em todas as tabelas Django (schema lista_presentes)
ALTER TABLE lista_presentes.django_migrations ENABLE ROW LEVEL SECURITY;
ALTER TABLE lista_presentes.django_content_type ENABLE ROW LEVEL SECURITY;
ALTER TABLE lista_presentes.auth_permission ENABLE ROW LEVEL SECURITY;
ALTER TABLE lista_presentes.auth_group ENABLE ROW LEVEL SECURITY;
ALTER TABLE lista_presentes.auth_group_permissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE lista_presentes.django_admin_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE lista_presentes.django_session ENABLE ROW LEVEL SECURITY;
ALTER TABLE lista_presentes.django_site ENABLE ROW LEVEL SECURITY;
ALTER TABLE lista_presentes.account_emailaddress ENABLE ROW LEVEL SECURITY;
ALTER TABLE lista_presentes.account_emailconfirmation ENABLE ROW LEVEL SECURITY;
ALTER TABLE lista_presentes.socialaccount_socialaccount ENABLE ROW LEVEL SECURITY;
ALTER TABLE lista_presentes.socialaccount_socialapp ENABLE ROW LEVEL SECURITY;
ALTER TABLE lista_presentes.socialaccount_socialapp_sites ENABLE ROW LEVEL SECURITY;
ALTER TABLE lista_presentes.socialaccount_socialtoken ENABLE ROW LEVEL SECURITY;
ALTER TABLE lista_presentes.presentes_usuario ENABLE ROW LEVEL SECURITY;
ALTER TABLE lista_presentes.presentes_usuario_groups ENABLE ROW LEVEL SECURITY;
ALTER TABLE lista_presentes.presentes_usuario_user_permissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE lista_presentes.presentes_grupo ENABLE ROW LEVEL SECURITY;
ALTER TABLE lista_presentes.presentes_grupomembro ENABLE ROW LEVEL SECURITY;
ALTER TABLE lista_presentes.presentes_presente ENABLE ROW LEVEL SECURITY;
ALTER TABLE lista_presentes.presentes_compra ENABLE ROW LEVEL SECURITY;
ALTER TABLE lista_presentes.presentes_sugestaocompra ENABLE ROW LEVEL SECURITY;
ALTER TABLE lista_presentes.presentes_notificacao ENABLE ROW LEVEL SECURITY;
```

**Script completo:** `scripts/enable_rls_supabase.sql` (já atualizado para schema `lista_presentes`)

### Como Funciona

| Role | BYPASSRLS? | Usado por | Resultado |
|------|------------|-----------|-----------|
| `postgres` | ✅ Sim | Django (DATABASE_URL) | Acesso total |
| `authenticator` | ❌ Não | PostgREST API | Bloqueado (0 rows) |
| `anon` | ❌ Não | API pública | Bloqueado (0 rows) |
| `authenticated` | ❌ Não | API com auth | Bloqueado (0 rows) |

**Resultado:** API Supabase bloqueada, Django funciona normalmente.

---

## 🗂️ Schema Isolado

### Por Que Usar Schema Próprio?

Quando você tem **múltiplas aplicações Django** no mesmo banco Supabase:

```
❌ PROBLEMA (schema public compartilhado):
App 1 → public.django_migrations
App 2 → public.django_migrations  ← CONFLITO!
App 3 → public.django_migrations  ← CONFLITO!

Resultado: InconsistentMigrationHistory
```

```
✅ SOLUÇÃO (schema isolado):
App 1 → gestao_contrato.django_migrations
App 2 → lista_presentes.django_migrations  ← Esta app
App 3 → outra_app.django_migrations

Resultado: Cada app isolada, sem conflitos
```

### Configuração

**DATABASE_URL com search_path:**
```
?options=-csearch_path%3Dlista_presentes
```

**O que faz:**
- Django cria tabelas em `lista_presentes.` ao invés de `public.`
- Evita conflitos com outras apps Django
- Mantém histórico de migrações isolado

**Documentação completa:** [SCHEMA_ISOLADO.md](SCHEMA_ISOLADO.md)

---

## 🎯 Connection Pooler

### Por Que Usar?

**URL Recomendada:** `aws-1-us-east-2.pooler.supabase.com:6543`

```
Django → Render → Internet → Supabase Pooler (PgBouncer) → PostgreSQL
                              ↓
                         ✅ FUNCIONA
```

**Vantagens:**
- ✅ Suporta IPv4 e IPv6
- ✅ Pool de conexões gerenciado (PgBouncer)
- ✅ Menor latência e mais estável
- ✅ Suporta mais conexões simultâneas
- ✅ Compatível com Render Free Tier

### Alternativa (Não Recomendada)

**URL Direta:** `db.YOUR_PROJECT_ID.supabase.co:5432`

```
Django → Render → Internet → Supabase (IPv6) → PostgreSQL
                              ↓
                    ❌ "Network is unreachable"
```

**Problemas:**
- ❌ IPv6 pode não ser roteável no Render Free Tier
- ❌ Conexões diretas podem ser bloqueadas
- ❌ Limites de conexões simultâneas

---

## 🆘 Troubleshooting

### Erro: "password authentication failed"

**Causa:** URL encoding incorreto

**Solução:** Verifique que DATABASE_URL tem `%21%40%23` (não `!@#`)

```bash
# ✅ Correto
postgresql://...senha:YOUR_PASSWORD_ENCODED@...

# ❌ Errado
postgresql://...senha:YOUR_PASSWORD@...
```

### Erro: "Network is unreachable"

**Causa:** Usando host errado

**Solução:** Use Connection Pooler:
```
aws-1-us-east-2.pooler.supabase.com:6543  (não db.YOUR_PROJECT_ID.supabase.co:5432)
```

### Erro: "Using SQLite instead of PostgreSQL"

**Causa:** DATABASE_URL não configurada

**Solução:**
1. Render Dashboard > Environment
2. Adicionar DATABASE_URL
3. Save Changes
4. Aguardar redeploy

### Erro: "permission denied for table"

**Causa:** Role não tem permissões

**Solução:**
```sql
GRANT ALL ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO postgres;
```

### Erro: "InconsistentMigrationHistory"

**Não é erro!** Build.sh corrige automaticamente:
```bash
⚠️  InconsistentMigrationHistory detected!
🔧 Auto-fixing migration history...
✅ Fixed with --fake-initial
```

Se falhar, veja: `migrations.md`

---

## 📊 Comparação: Supabase vs Render PostgreSQL

| Aspecto | Supabase (Atual) | Render PostgreSQL |
|---------|------------------|-------------------|
| **Armazenamento** | ✅ 500 MB | ⚠️ 256 MB |
| **Interface Web** | ✅ Dashboard completo | ❌ CLI apenas |
| **Backup** | ✅ Automático (7 dias) | ❌ Manual |
| **Conectividade** | ✅ Pooler funciona | ✅ Mesma rede |
| **Latência** | ⚠️ 50-100ms | ✅ <1ms |
| **RLS** | ✅ Suportado | ✅ Suportado |
| **Custo** | ✅ Free | ✅ Free |

**Recomendação:** Supabase com Connection Pooler (configuração atual).

---

## 🔍 Verificação

### Teste de Conexão

```bash
# Teste local
export DATABASE_URL="postgresql://..."
python scripts/check_database_config.py
```

**Saída esperada:**
```
✅ DATABASE_URL está definida
✅ Django está usando PostgreSQL ✅
✅ Conectado ao Supabase PostgreSQL ✨
✅ Conexão OK!
```

### Verificar RLS Habilitado

```sql
-- Executar no Supabase SQL Editor
SELECT
    tablename,
    rowsecurity AS rls_enabled
FROM pg_tables
WHERE schemaname = 'public'
  AND tablename LIKE ANY(ARRAY['django_%', 'presentes_%', 'auth_%', 'account_%', 'socialaccount_%'])
ORDER BY tablename;
```

**Resultado esperado:** Todas as linhas com `rls_enabled = true`

### Verificar API Bloqueada

```bash
# Tentar acessar via API (deve retornar vazio)
curl https://YOUR_PROJECT_ID.supabase.co/rest/v1/presentes_usuario \
  -H "apikey: sb_publishable_YOUR_ANON_KEY"
```

**Resultado esperado:** `[]` (lista vazia)

---

## 🔗 Links Úteis

- **Supabase Dashboard**: https://app.supabase.com/project/YOUR_PROJECT_ID
- **Supabase SQL Editor**: https://app.supabase.com/project/YOUR_PROJECT_ID/sql/new
- **Database Linter**: https://app.supabase.com/project/YOUR_PROJECT_ID/database/linter
- **Supabase RLS Docs**: https://supabase.com/docs/guides/auth/row-level-security
- **PostgreSQL RLS Docs**: https://www.postgresql.org/docs/current/ddl-rowsecurity.html

---

**Última atualização:** 2026-02-07
**Versão:** 1.1.31
