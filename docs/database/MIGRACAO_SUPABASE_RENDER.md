# Migração: Supabase → Render PostgreSQL

## 🎯 Por Que Migrar?

### Problema com Supabase (Múltiplas Apps Django)

```
❌ Supabase Database compartilhado:
├── public/
│   ├── django_migrations     ← App 1 + App 2 + App 3 (CONFLITO!)
│   ├── auth_user            ← App 1 + App 2 + App 3 (CONFLITO!)
│   └── ...

Resultado: InconsistentMigrationHistory
Solução: Schema isolado (complexo, requer SQL manual)
```

### Solução com Render PostgreSQL

```
✅ Render PostgreSQL: 1 banco por app (isolamento automático):
├── lista-presentes-db       ← App 1 (isolado)
├── gestao-contrato-db       ← App 2 (isolado)
└── outra-app-db            ← App 3 (isolado)

Resultado: Sem conflitos, setup automático!
```

---

## 🚀 Migração - 3 Passos

### Passo 1: Backup dos Dados (Supabase)

```bash
# Opção A: Via Supabase Dashboard
1. Supabase Dashboard > Database > Backups
2. Download do backup mais recente (.sql)

# Opção B: Via pg_dump
pg_dump "postgresql://postgres.PROJECT:PASSWORD@aws-1-us-east-2.pooler.supabase.com:6543/postgres" > backup.sql
```

**Salvar:** `backup.sql` (guardar com segurança)

---

### Passo 2: Configurar Render PostgreSQL

#### 2.1 Atualizar render.yaml (Já Configurado)

```yaml
# render.yaml - Já está configurado!
databases:
  - name: lista-presentes-db
    databaseName: lista_presentes
    user: lista_presentes_user
    region: oregon
    plan: free
```

**Status:** ✅ Não precisa alterar (já commitado)

#### 2.2 Fazer Push (Render cria banco automaticamente)

```bash
git add render.yaml
git commit -m "feat: Migrar para Render PostgreSQL"
git push origin main
```

**O que acontece:**
1. Render detecta `databases:` no render.yaml
2. Cria banco PostgreSQL automaticamente
3. Injeta DATABASE_URL no web service
4. Deploy executa migrações

**Aguardar:** 3-5 minutos (banco + deploy)

---

### Passo 3: Restaurar Dados (Opcional)

Se você quer MANTER os dados do Supabase:

```bash
# 1. Conectar ao Render Database (via Dashboard)
Render Dashboard > Database > Connect

# 2. Copiar connection string:
DATABASE_URL=postgresql://user:pass@host:5432/db

# 3. Restaurar backup
psql "postgresql://user:pass@host:5432/db" < backup.sql
```

**Alternativa:** Começar do zero (sem dados antigos)

---

## ✅ Verificação

### Checar Logs do Deploy

```bash
Render Dashboard > Web Service > Logs

# Procurar por:
✅ "Database connection successful!"
✅ "All migrations applied successfully"
✅ "Your service is live"

# NÃO deve aparecer:
❌ "InconsistentMigrationHistory"
❌ "Network is unreachable"
```

### Testar Aplicação

```bash
# 1. Acessar site
https://lista-presentes.onrender.com

# 2. Fazer login
# 3. Criar presente
# 4. Verificar funcionalidades
```

---

## 📊 Comparação: Supabase vs Render

| Aspecto | Supabase | Render PostgreSQL |
|---------|----------|-------------------|
| **Isolamento** | ⚠️ Manual (schema isolado) | ✅ Automático (banco por app) |
| **Setup** | ❌ Complexo (SQL manual) | ✅ Simples (render.yaml) |
| **Conflitos** | ⚠️ Requer cuidado | ✅ Impossível |
| **Armazenamento** | ✅ 500 MB | ⚠️ 256 MB |
| **Latência** | ⚠️ 50-100ms | ✅ <1ms |
| **Interface Web** | ✅ Dashboard completo | ❌ CLI apenas |
| **Backup** | ✅ Automático (7 dias) | ❌ Manual |
| **Custo** | ✅ Free | ✅ Free |

**Recomendação:** Render PostgreSQL para simplicidade e isolamento

---

## 🔄 Rollback (Voltar para Supabase)

Se precisar voltar para Supabase:

```yaml
# render.yaml - comentar databases
# databases:
#   - name: lista-presentes-db
#     ...

# Descomentar Supabase config
envVars:
  - key: DATABASE_URL
    sync: false  # Configurar manualmente no Dashboard

# Configurar DATABASE_URL no Dashboard:
DATABASE_URL=postgresql://postgres.PROJECT:PASS@aws-1-us-east-2.pooler.supabase.com:6543/postgres?options=-csearch_path%3Dlista_presentes
```

**Importante:** Lembrar de adicionar `?options=...` para schema isolado!

---

## 🆘 Troubleshooting

### Erro: "relation does not exist"

**Causa:** Banco novo sem dados

**Solução:**
```bash
# Django criará tabelas automaticamente nas migrações
# Se restaurou backup, verificar que restore funcionou:
psql $DATABASE_URL -c "\dt"
```

### Erro: "InconsistentMigrationHistory" (ainda)

**Causa:** Histórico de migrações conflitante

**Solução:**
```bash
# Render Shell
python manage.py migrate --fake-initial
```

### Database não foi criado

**Causa:** `databases:` não está no render.yaml

**Solução:**
1. Verificar render.yaml tem seção `databases:`
2. Git push para reaplicar
3. Aguardar deploy

---

## 📝 Checklist Pós-Migração

- [ ] Render PostgreSQL criado (Dashboard > Databases)
- [ ] DATABASE_URL injetado automaticamente
- [ ] Deploy bem-sucedido (sem erros)
- [ ] Migrações aplicadas (verificar logs)
- [ ] Site acessível
- [ ] Login funcionando
- [ ] Dados restaurados (se aplicável)
- [ ] Sem erros nos logs
- [ ] Performance OK (latência <1ms)

---

## 🔗 Links

- **Render Dashboard**: https://dashboard.render.com
- **Render Databases**: https://dashboard.render.com/databases
- **Render Docs**: https://render.com/docs/databases
- **PostgreSQL Docs**: https://www.postgresql.org/docs/

---

**Última atualização:** 2026-02-07
**Status:** ✅ Migração Simples
**Recomendação:** Render PostgreSQL (isolamento automático)
**Complexidade:** ⭐ Fácil (3 passos, ~10 minutos)
