# Schema Isolado - Múltiplas Apps Django no Supabase

## ✨ TL;DR - Configuração Automática

**O schema `lista_presentes` é criado AUTOMATICAMENTE durante o build do Render!**

Nenhuma ação manual necessária. O script `scripts/ensure_schema.py` é executado automaticamente pelo `build.sh` antes das migrations Django.

**Você só precisa:**
1. Configurar `DATABASE_URL` no Render Dashboard (Supabase Connection Pooler)
2. Deploy! O resto é automático.

---

## 🎯 Problema

Quando você tem **múltiplas aplicações Django** no mesmo banco Supabase, todas compartilham o schema `public`:

```
Supabase Database
├── public/
│   ├── django_migrations      ← App 1 + App 2 + App 3 (CONFLITO!)
│   ├── auth_user              ← App 1 + App 2 + App 3 (CONFLITO!)
│   ├── auth_permission        ← App 1 + App 2 + App 3 (CONFLITO!)
│   └── ...
```

**Resultado:**
```
❌ InconsistentMigrationHistory: Migration admin.0001_initial is applied
   before its dependency presentes.0001_initial on database 'default'
```

Django encontra `django_migrations` de outra app e pensa que as migrações já foram aplicadas, mas as tabelas não existem para a app atual.

---

## ✅ Solução: Schema Isolado

Criar um schema dedicado para cada aplicação Django:

```
Supabase Database
├── public/                    ← Supabase internal
├── gestao_contrato/           ← App 1
│   ├── django_migrations
│   ├── auth_user
│   └── ...
├── lista_presentes/           ← App 2 (esta app)
│   ├── django_migrations
│   ├── auth_user
│   └── ...
└── outra_app/                 ← App 3
    ├── django_migrations
    ├── auth_user
    └── ...
```

**Cada app tem suas próprias tabelas Django, isoladas completamente!**

---

## 📋 Configuração - Totalmente Automática

### ✨ O Build do Render Faz Tudo!

**Você só precisa configurar a `DATABASE_URL`:**

```bash
# Render Dashboard > lista-presentes > Environment
DATABASE_URL=postgresql://postgres.YOUR_PROJECT:YOUR_PASSWORD@aws-1-us-east-2.pooler.supabase.com:6543/postgres
```

**NÃO adicione** `?options=-csearch_path%3D...` - o schema é configurado automaticamente via `settings.py`!

### 🔧 O que Acontece Automaticamente no Build

1. **Script `scripts/ensure_schema.py` é executado** (via `build.sh`)
   - Conecta no Supabase
   - Verifica se schema `lista_presentes` existe
   - Cria se não existir
   - Configura permissões automaticamente

2. **Django executa migrations**
   - Com `search_path=lista_presentes` (via `settings.py`)
   - Cria todas as tabelas no schema isolado
   - Signal `connection_created` garante schema correto em cada conexão

**Resultado:** Schema criado + Tabelas criadas + Isolamento completo - TUDO AUTOMÁTICO!

---

### 🛠️ Migração Manual (Opcional)

Se você já tem tabelas no schema `public` e quer migrá-las para `lista_presentes`:

```bash
# Abrir Supabase SQL Editor
https://app.supabase.com/project/YOUR_PROJECT_ID/sql/new

# Executar script de migração
scripts/create_isolated_schema.sql
```

**O script migra automaticamente:**
- ✅ Cria schema `lista_presentes`
- ✅ Move tabelas existentes de `public` → `lista_presentes`
- ✅ Habilita RLS
- ✅ Configura permissões

**Onde configurar:**
1. Render Dashboard > Environment
2. Editar `DATABASE_URL`
3. Adicionar o parâmetro `options`
4. Save Changes

**URL Encoding:**
```
search_path=lista_presentes
↓
-csearch_path%3Dlista_presentes
```

---

### 3️⃣ Atualizar settings.py (Já Configurado)

O `settings.py` já está configurado para usar schema isolado:

```python
if DATABASE_URL and not USE_SQLITE:
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }

    # Schema Isolado: search_path=lista_presentes
    if 'OPTIONS' not in DATABASES['default']:
        DATABASES['default']['OPTIONS'] = {}

    if 'options' not in DATABASES['default']['OPTIONS']:
        DATABASES['default']['OPTIONS']['options'] = '-c search_path=lista_presentes'
```

**Como funciona:**
- Se DATABASE_URL tem `?options=...` → usa da URL
- Se DATABASE_URL não tem → adiciona automaticamente

---

### 4️⃣ Redeploy no Render

```bash
# Opção 1: Commit vazio (força redeploy)
git commit --allow-empty -m "chore: Force redeploy para schema isolado"
git push origin main

# Opção 2: Render Dashboard
Dashboard > Manual Deploy > Deploy latest commit
```

**Aguardar:** 3-5 minutos

---

### 5️⃣ Verificar Logs

```bash
# Acessar logs
https://dashboard.render.com/web/lista-presentes/logs

# Procurar por:
✅ "Database connection successful!"
✅ "Connected to Supabase PostgreSQL"
✅ "All migrations applied successfully"

# NÃO deve aparecer:
❌ "InconsistentMigrationHistory"
❌ "admin.0001_initial is applied before"
❌ "Using SQLite instead of PostgreSQL"
```

---

## 🔍 Validação

### Verificar Schema no Supabase

```sql
-- SQL Editor
SELECT
    schemaname,
    tablename
FROM pg_tables
WHERE schemaname = 'lista_presentes'
ORDER BY tablename;
```

**Resultado esperado:** ~23 tabelas Django no schema `lista_presentes`

### Verificar search_path no Django

```python
# Render Shell ou local
python manage.py shell

from django.db import connection
cursor = connection.cursor()
cursor.execute("SHOW search_path")
print(cursor.fetchone())
# Resultado esperado: ('lista_presentes',) ou ('lista_presentes', 'public')
```

### Verificar Tabelas Usadas

```python
# Django Shell
from django.db import connection
cursor = connection.cursor()
cursor.execute("""
    SELECT schemaname, tablename
    FROM pg_tables
    WHERE tablename LIKE 'django_%'
    LIMIT 5
""")
for row in cursor.fetchall():
    print(f"{row[0]}.{row[1]}")

# Resultado esperado: lista_presentes.django_migrations, etc.
```

---

## 🔄 Opções de Migração

### Opção A: Migrar Tabelas Existentes ✅

**Quando usar:** Você JÁ TEM dados em produção

**Script:** `scripts/create_isolated_schema.sql` (completo)

**O que faz:**
- Move tabelas de `public` → `lista_presentes`
- Preserva TODOS os dados
- Habilita RLS
- Zero downtime

### Opção B: Começar do Zero

**Quando usar:** Sem dados em produção ou quer resetar

**Script:** Executar apenas seções 1, 3, 4 e 5 de `create_isolated_schema.sql`

**O que faz:**
- Cria schema vazio
- Django cria tabelas do zero
- Habilita RLS
- **PERDE todos os dados!**

---

## 🆘 Troubleshooting

### Erro: "relation does not exist"

**Causa:** Django ainda procura no `public`

**Solução:**
```bash
# Verificar DATABASE_URL tem options
echo $DATABASE_URL
# Deve ter: ?options=-csearch_path%3Dlista_presentes

# Se não tiver, adicionar no Render Dashboard
```

### Erro: "schema lista_presentes does not exist"

**Causa:** Script SQL não foi executado

**Solução:**
1. Abrir Supabase SQL Editor
2. Executar `scripts/create_isolated_schema.sql`
3. Redeploy

### Erro: InconsistentMigrationHistory (ainda)

**Causa:** Tabelas ainda existem em `public`

**Solução:**
```sql
-- Verificar se tabelas Django ainda estão em public
SELECT tablename
FROM pg_tables
WHERE schemaname = 'public'
  AND tablename LIKE 'django_%';

-- Se aparecer tabelas:
-- Opção 1: Deletar (se já migrou)
DROP TABLE public.django_migrations CASCADE;

-- Opção 2: Remover public do search_path
-- DATABASE_URL=...?options=-csearch_path%3Dlista_presentes
-- (NÃO incluir public)
```

### Django Cria Tabelas no public (ainda)

**Causa:** search_path inclui `public`

**Solução:** Garantir que search_path = `lista_presentes` APENAS

```python
# settings.py - verificar
DATABASES['default']['OPTIONS']['options'] = '-c search_path=lista_presentes'
# NÃO: '-c search_path=lista_presentes,public'
```

---

## ✅ Checklist de Migração

- [ ] Script SQL executado no Supabase
- [ ] Schema `lista_presentes` criado
- [ ] Tabelas migradas (ou criadas)
- [ ] RLS habilitado
- [ ] DATABASE_URL atualizada com `?options=...`
- [ ] Redeploy feito
- [ ] Logs verificados (sem erros)
- [ ] Django usando schema correto (`SHOW search_path`)
- [ ] Tabelas em `lista_presentes.` (não `public.`)
- [ ] Aplicação funcionando normalmente

---

## 📊 Benefícios

| Antes (public) | Depois (lista_presentes) |
|----------------|--------------------------|
| ❌ Conflitos entre apps | ✅ Isolamento total |
| ❌ InconsistentMigrationHistory | ✅ Migrações limpas |
| ❌ django_migrations compartilhado | ✅ Cada app seu histórico |
| ❌ Difícil debug | ✅ Fácil identificar origem |
| ❌ 1 app por banco | ✅ Múltiplas apps no mesmo banco |

---

## 🔗 Links

- **Script SQL**: `scripts/create_isolated_schema.sql`
- **Script RLS**: `scripts/enable_rls_supabase.sql` (atualizado para lista_presentes)
- **Settings**: `lista_presentes/settings.py` (já configurado)
- **Supabase SQL Editor**: https://app.supabase.com/project/YOUR_PROJECT_ID/sql/new

---

**Última atualização:** 2026-02-07
**Status:** ✅ Implementado
**Schema:** `lista_presentes`
**Compatibilidade:** Django 4.0+, PostgreSQL 12+
