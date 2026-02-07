# ✅ Configuração Supabase - Lista de Presentes

## ⚠️ ATENÇÃO: Segurança Crítica

**🔴 AÇÃO NECESSÁRIA:** Este banco de dados tem **27 alertas de segurança críticos** relacionados a Row Level Security (RLS).

```
❌ Senhas, tokens e sessões expostos via API Supabase
❌ RLS não habilitado em 23 tabelas Django
❌ Dados sensíveis acessíveis publicamente
```

**📖 Solução:** Veja instruções detalhadas em **[SUPABASE_SECURITY.md](SUPABASE_SECURITY.md)**

**⚡ Quick Fix:** Execute `scripts/enable_rls_supabase.sql` no Supabase SQL Editor

---

## 📋 Configuração Atual

Este projeto está configurado para usar **Supabase PostgreSQL** como banco de dados.

### 🔑 Credenciais

```bash
# Database Connection (Connection Pooler - Recomendado)
DATABASE_URL=postgresql://postgres.szyouijmxhlbavkzibxa:123ewqasdcxz%21%40%23@aws-1-us-east-2.pooler.supabase.com:6543/postgres

# Supabase API (Opcional)
SUPABASE_URL=https://szyouijmxhlbavkzibxa.supabase.co
SUPABASE_KEY=sb_publishable_aswPuvIXjzcejBTyYWObdQ_BpC5l903

# GitHub Integration (Obrigatório)
GITHUB_TOKEN=<use o token fornecido pelo administrador>
GITHUB_REPO_OWNER=Maxwbh
GITHUB_REPO_NAME=Lista_de_Presentes
GITHUB_AUTO_CREATE_ISSUES=True
```

---

## 🎯 Por Que Connection Pooler?

### aws-1-us-east-2.pooler.supabase.com:6543 ✅

```
Django → Render → Internet → Supabase Pooler (IPv4/IPv6) → PostgreSQL
                              ↓
                         FUNCIONA
```

**Vantagens:**
- ✅ Suporta IPv4 e IPv6
- ✅ Pool de conexões gerenciado (PgBouncer)
- ✅ Menor latência
- ✅ Mais estável
- ✅ Suporta mais conexões simultâneas
- ✅ Compatível com Render Free Tier

### db.szyouijmxhlbavkzibxa.supabase.co:5432 ❌

```
Django → Render → Internet → Supabase (IPv6) → PostgreSQL
                              ↓
                    "Network is unreachable"
```

**Problemas:**
- ❌ IPv6 pode não ser roteável no Render Free Tier
- ❌ Conexões diretas podem ser bloqueadas
- ❌ Limites de conexões simultâneas

---

## 📝 Configurar no Render Dashboard

### 1️⃣ Acessar Environment Variables

🔗 https://dashboard.render.com/web/lista-presentes/environment

### 2️⃣ Adicionar Variáveis

#### DATABASE_URL (OBRIGATÓRIA)
```
Key:   DATABASE_URL
Value: postgresql://postgres.szyouijmxhlbavkzibxa:123ewqasdcxz%21%40%23@aws-1-us-east-2.pooler.supabase.com:6543/postgres
```

**⚠️ IMPORTANTE:**
- Use exatamente esta URL (Connection Pooler)
- Senha com URL encoding: `%21%40%23` = `!@#`
- Porta `6543` (não 5432)

#### SUPABASE_URL (OPCIONAL)
```
Key:   SUPABASE_URL
Value: https://szyouijmxhlbavkzibxa.supabase.co
```

#### SUPABASE_KEY (OPCIONAL)
```
Key:   SUPABASE_KEY
Value: sb_publishable_aswPuvIXjzcejBTyYWObdQ_BpC5l903
```

#### GITHUB_TOKEN (OBRIGATÓRIA)
```
Key:   GITHUB_TOKEN
Value: <use o token fornecido pelo administrador>
```

### 3️⃣ Salvar e Aguardar Deploy

1. Clique em **Save Changes**
2. Aguarde deploy automático (3-5 minutos)
3. Verifique logs

---

## ✅ Logs de Sucesso

Quando tudo estiver funcionando, você verá:

```bash
🔧 Render.com Build Script
==========================
✅ DJANGO_SETTINGS_MODULE: lista_presentes.settings

📦 Upgrading pip...
📦 Installing dependencies...
📁 Collecting static files...

🔌 Testing database connection...
✅ Database connection successful!
✅ Connected to Supabase PostgreSQL
✅ Database is ready

🔄 Creating migrations...
⚠️  No migrations to create

🔍 Checking for pending migrations...

🗄️  Running migrations...
⚠️  InconsistentMigrationHistory detected!
🔧 Auto-fixing migration history...
✅ Fixed with --fake-initial

🔄 Retrying migrations after fix...
✅ All migrations applied successfully

👤 Creating/fixing admin user...
✅ Build completed successfully!

==> Your service is live 🎉
```

---

## 🔍 Verificar Configuração

### Teste Local

```bash
# Clone o repositório
git clone https://github.com/Maxwbh/Lista_de_Presentes.git
cd Lista_de_Presentes

# Configure variáveis de ambiente
export DATABASE_URL="postgresql://postgres.szyouijmxhlbavkzibxa:123ewqasdcxz!@#@aws-1-us-east-2.pooler.supabase.com:6543/postgres"
export DJANGO_SETTINGS_MODULE=lista_presentes.settings

# Teste conexão
python scripts/check_database_config.py
```

**Saída Esperada:**
```
✅ DATABASE_URL está definida
✅ Django está usando PostgreSQL ✅
✅ Conectado ao Supabase PostgreSQL ✨
✅ Conexão OK!
✅ Todas as verificações passaram!
```

### Teste no Render

1. Acesse: https://dashboard.render.com/web/lista-presentes/logs
2. Procure por: `✅ Connected to Supabase PostgreSQL`
3. Verifique: `✅ All migrations applied successfully`

---

## 🆘 Troubleshooting

### Erro: "password authentication failed"

**Causa:** URL encoding incorreto

**Solução:** Verifique que DATABASE_URL tem exatamente:
```
%21%40%23
```

Não use:
```
!@#  ← ERRADO (será interpretado incorretamente)
```

### Erro: "Network is unreachable"

**Causa:** Usando host errado (db.szyouijmxhlbavkzibxa.supabase.co)

**Solução:** Use o Connection Pooler:
```
aws-1-us-east-2.pooler.supabase.com:6543
```

### Erro: "Using SQLite instead of PostgreSQL"

**Causa:** DATABASE_URL não foi configurada no Render

**Solução:**
1. Render Dashboard > Environment
2. Adicione DATABASE_URL
3. Save Changes
4. Aguarde redeploy

### Erro: "InconsistentMigrationHistory"

**Não é um erro!** O build.sh corrige automaticamente:
```bash
⚠️  InconsistentMigrationHistory detected!
🔧 Auto-fixing migration history...
✅ Fixed with --fake-initial
```

Se a correção automática falhar, veja: `MIGRATION_FIX.md`

---

## 📊 Comparação: Supabase vs Render PostgreSQL

| Aspecto | Supabase (Atual) | Render PostgreSQL |
|---------|------------------|-------------------|
| **Armazenamento** | ✅ 500 MB | ⚠️ 256 MB |
| **Interface Web** | ✅ Dashboard | ❌ CLI apenas |
| **Backup** | ✅ Automático (7 dias) | ❌ Manual |
| **Conectividade** | ✅ Pooler funciona | ✅ Mesma rede |
| **Latência** | ⚠️ 50-100ms | ✅ <1ms |
| **Custo** | ✅ Free | ✅ Free |

**Recomendação Atual:** Supabase com Connection Pooler funciona bem e oferece mais armazenamento.

---

## 🔗 Links Úteis

- **Supabase Dashboard**: https://app.supabase.com/project/szyouijmxhlbavkzibxa
- **Render Dashboard**: https://dashboard.render.com/web/lista-presentes
- **Site**: https://lista-presentes-1iwb.onrender.com
- **GitHub**: https://github.com/Maxwbh/Lista_de_Presentes

---

## 📚 Documentação Relacionada

- 🔒 **`SUPABASE_SECURITY.md`** - **LEIA PRIMEIRO** - Segurança RLS (27 alertas críticos!)
- `MIGRATION_FIX.md` - Correção de erros de migração
- `USE_RENDER_POSTGRESQL.md` - Alternativa com Render PostgreSQL
- `URGENTE_DATABASE_URL.md` - Guia rápido de configuração
- `scripts/check_database_config.py` - Script de verificação
- `scripts/enable_rls_supabase.sql` - **EXECUTAR URGENTE** - Habilitar RLS

---

**Última atualização:** 2026-02-07
**Status:** ⚠️ Configurado mas **REQUER AÇÃO DE SEGURANÇA**
**Database:** Supabase PostgreSQL (Connection Pooler)
**Segurança:** 🔴 **RLS NÃO HABILITADO** - Execute `enable_rls_supabase.sql`
**Versão:** 1.1.28
