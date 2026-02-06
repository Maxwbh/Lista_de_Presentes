# 🗄️ Configuração do Supabase PostgreSQL

Este documento descreve como configurar o Supabase como banco de dados PostgreSQL para o projeto Lista de Presentes.

## 📋 Índice

- [Por que Supabase?](#por-que-supabase)
- [Configuração no Render](#configuração-no-render)
- [Migração de Dados](#migração-de-dados)
- [Conexão Local](#conexão-local)
- [Recursos Adicionais](#recursos-adicionais)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Por que Supabase?

### Vantagens sobre Render PostgreSQL Free

| Recurso | Supabase Free | Render PostgreSQL Free |
|---------|---------------|------------------------|
| **Armazenamento** | 500 MB | 256 MB |
| **Backup Automático** | ✅ Sim (7 dias) | ❌ Não |
| **Interface Web** | ✅ Table Editor | ❌ Apenas CLI |
| **API REST** | ✅ Automática | ❌ Não |
| **Realtime** | ✅ Subscriptions | ❌ Não |
| **Storage** | ✅ 1 GB grátis | ❌ Não |
| **Authentication** | ✅ Integrado | ❌ Não |
| **Região** | Múltiplas opções | Oregon/Ohio |
| **Expira?** | ❌ Não expira | ⚠️ 90 dias sem uso |

### Recursos Extras do Supabase

1. **Table Editor**: Interface visual para gerenciar dados
2. **SQL Editor**: Execute queries diretamente no browser
3. **Database Backups**: Restaure para qualquer ponto nos últimos 7 dias
4. **Monitoring**: Veja métricas de uso e performance
5. **Logs**: Acompanhe queries e erros em tempo real
6. **Extensions**: PostGIS, pg_cron, e outras extensões PostgreSQL

---

## ⚙️ Configuração no Render

### Passo 1: Obter Credenciais do Supabase

Você já tem as credenciais do projeto:

```bash
# URL do Projeto Supabase
SUPABASE_URL=https://szyouijmxhlbavkzibxa.supabase.co

# Chave Pública (anon/public key)
SUPABASE_KEY=sb_publishable_aswPuvIXjzcejBTyYWObdQ_BpC5l903

# Connection String PostgreSQL
DATABASE_URL=postgresql://postgres:123ewqasdcxz!@#@db.szyouijmxhlbavkzibxa.supabase.co:5432/postgres
```

### Passo 2: Configurar no Dashboard do Render

1. **Acesse o Dashboard do Render**
   - Vá para https://dashboard.render.com
   - Selecione seu serviço `lista-presentes`

2. **Navegue até Environment**
   - Clique na aba "Environment" no menu lateral

3. **Adicione as Variáveis de Ambiente**

   Adicione ou atualize as seguintes variáveis:

   ```bash
   # OBRIGATÓRIO - Connection String do PostgreSQL
   DATABASE_URL=postgresql://postgres:123ewqasdcxz!@#@db.szyouijmxhlbavkzibxa.supabase.co:5432/postgres

   # OPCIONAL - Para uso futuro com Supabase SDK
   SUPABASE_URL=https://szyouijmxhlbavkzibxa.supabase.co
   SUPABASE_KEY=sb_publishable_aswPuvIXjzcejBTyYWObdQ_BpC5l903
   ```

4. **Salve e Faça Deploy**
   - Clique em "Save Changes"
   - O Render irá fazer deploy automático

### Passo 3: Executar Migrações

O script `build.sh` já está configurado para executar migrações automaticamente durante o deploy:

```bash
echo "🔄 Creating migrations..."
python manage.py makemigrations --noinput

echo "🗄️  Running migrations..."
python manage.py migrate --noinput --run-syncdb

echo "✅ Verifying migrations..."
python manage.py showmigrations
```

---

## 🔄 Migração de Dados

### Opção 1: Exportar do Render e Importar no Supabase (Recomendado)

Se você já tem dados no PostgreSQL do Render:

```bash
# 1. Exportar dados do Render (execute localmente)
pg_dump $OLD_DATABASE_URL > backup.sql

# 2. Importar no Supabase
psql "postgresql://postgres:123ewqasdcxz!@#@db.szyouijmxhlbavkzibxa.supabase.co:5432/postgres" < backup.sql
```

### Opção 2: Começar do Zero

Se você não tem dados importantes:

1. **Deletar Banco Antigo do Render** (opcional)
   - Vá para Dashboard > Database
   - Delete `lista-presentes-db`
   - Isso libera recursos no Render

2. **Deploy Automático**
   - Faça push para o branch master
   - As migrações serão executadas automaticamente
   - Um banco novo será criado no Supabase

### Opção 3: Usar Django para Migrar

```bash
# 1. Exportar fixtures do banco antigo
python manage.py dumpdata --natural-foreign --natural-primary \
  -e contenttypes -e auth.Permission > data.json

# 2. Atualizar DATABASE_URL para Supabase

# 3. Importar fixtures no Supabase
python manage.py loaddata data.json
```

---

## 💻 Conexão Local

### Usando Docker (Recomendado)

Para desenvolvimento local, você pode usar Docker:

```bash
# docker-compose.yml
version: '3.8'
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: lista_presentes
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

```bash
# .env local
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/lista_presentes
```

### Conectar ao Supabase Diretamente

Você também pode conectar ao Supabase do ambiente local:

```bash
# .env
DATABASE_URL=postgresql://postgres:123ewqasdcxz!@#@db.szyouijmxhlbavkzibxa.supabase.co:5432/postgres
```

⚠️ **Cuidado**: Use isso apenas para testes. Não execute migrações destrutivas no banco de produção!

---

## 🚀 Recursos Adicionais do Supabase

### 1. Table Editor

Acesse visualmente suas tabelas:

1. Vá para https://app.supabase.com
2. Selecione seu projeto
3. Menu "Table Editor"
4. Visualize e edite dados diretamente

### 2. SQL Editor

Execute queries SQL customizadas:

1. Menu "SQL Editor"
2. Execute queries personalizadas
3. Salve queries frequentes
4. Veja resultados formatados

### 3. Backups Automáticos

```sql
-- Restaurar para um ponto específico no tempo
-- Disponível no Dashboard > Database > Backups
```

### 4. Monitoring

Acompanhe métricas:

- Conexões ativas
- Tamanho do banco
- Queries por segundo
- CPU e Memória

### 5. Extensions PostgreSQL

Extensões já habilitadas:

- `uuid-ossp`: Geração de UUIDs
- `pgcrypto`: Funções de criptografia
- `pg_stat_statements`: Estatísticas de queries

Para habilitar mais extensões:

```sql
-- SQL Editor
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pg_cron;
```

---

## 🔧 Troubleshooting

### Erro: "password authentication failed"

**Problema**: Senha incorreta na connection string

**Solução**: Verifique a senha. Caracteres especiais devem ser URL-encoded:
```
! → %21
@ → %40
# → %23
```

Exemplo correto:
```
postgresql://postgres:123ewqasdcxz%21%40%23@db.szyouijmxhlbavkzibxa.supabase.co:5432/postgres
```

### Erro: "too many connections"

**Problema**: Limite de conexões simultâneas atingido

**Solução 1**: Ajustar pool de conexões no settings.py
```python
DATABASES = {
    'default': dj_database_url.config(
        default=DATABASE_URL,
        conn_max_age=60,  # Reduzir de 600 para 60
    )
}
```

**Solução 2**: Usar PgBouncer (Supabase tem built-in)
```
# Use a porta 6543 ao invés de 5432
postgresql://postgres:senha@db.xxxxx.supabase.co:6543/postgres
```

### Erro: "relation does not exist"

**Problema**: Tabelas não foram criadas

**Solução**: Execute migrações manualmente
```bash
# No Render Shell ou localmente
python manage.py migrate --run-syncdb
```

### Migrações não aplicadas automaticamente

**Problema**: build.sh não executou migrações

**Solução**: Force execução
```bash
# Via Render Shell
python manage.py migrate --noinput
python manage.py showmigrations
```

### Performance lenta

**Problema**: Conexão lenta entre Render e Supabase

**Solução**: Escolher região próxima
- Render Oregon → Supabase US West
- Render Ohio → Supabase US East
- Render Frankfurt → Supabase EU Central

Altere a região no Supabase Dashboard > Settings > General

---

## 📚 Recursos Úteis

- [Documentação Supabase](https://supabase.com/docs)
- [Supabase Python Client](https://github.com/supabase-community/supabase-py)
- [PostgreSQL Connection Pooling](https://supabase.com/docs/guides/database/connecting-to-postgres#connection-pooler)
- [Supabase CLI](https://supabase.com/docs/guides/cli)

---

## ✅ Checklist de Migração

- [ ] Obter credenciais do Supabase
- [ ] Adicionar DATABASE_URL no Render Dashboard
- [ ] Adicionar SUPABASE_URL no Render Dashboard (opcional)
- [ ] Adicionar SUPABASE_KEY no Render Dashboard (opcional)
- [ ] Fazer backup do banco antigo (se tiver dados)
- [ ] Deploy no Render
- [ ] Verificar que migrações foram aplicadas
- [ ] Testar aplicação
- [ ] Importar dados antigos (se necessário)
- [ ] Deletar banco PostgreSQL do Render (opcional)
- [ ] Atualizar documentação interna

---

## 🎉 Conclusão

Agora você está usando Supabase como banco de dados PostgreSQL! Aproveite os recursos extras:

- ✅ Mais armazenamento (500MB vs 256MB)
- ✅ Interface web para gerenciar dados
- ✅ Backups automáticos
- ✅ API REST automática
- ✅ Sem expiração por inatividade

**Credenciais do Projeto:**
- URL: https://szyouijmxhlbavkzibxa.supabase.co
- Dashboard: https://app.supabase.com

Para dúvidas ou problemas, consulte a [documentação oficial do Supabase](https://supabase.com/docs).
