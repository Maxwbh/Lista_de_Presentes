# 🚀 Configuração do Supabase no Render - Guia Completo

Este guia fornece instruções passo-a-passo para configurar o Supabase PostgreSQL no Render.com.

## 📋 Credenciais do Projeto

```bash
# URL do Projeto Supabase
SUPABASE_URL=https://szyouijmxhlbavkzibxa.supabase.co

# Chave Pública do Supabase
SUPABASE_KEY=sb_publishable_aswPuvIXjzcejBTyYWObdQ_BpC5l903

# Connection String PostgreSQL (COM URL ENCODING)
DATABASE_URL=postgresql://postgres:123ewqasdcxz%21%40%23@db.szyouijmxhlbavkzibxa.supabase.co:6543/postgres
```

⚠️ **IMPORTANTE**: A senha contém caracteres especiais (`!@#`) que foram convertidos para URL encoding:
- `!` → `%21`
- `@` → `%40`
- `#` → `%23`

---

## 🎯 Passo 1: Acessar o Dashboard do Render

1. Abra seu navegador e acesse: https://dashboard.render.com
2. Faça login com sua conta
3. Localize o serviço **lista-presentes** na lista de serviços

---

## ⚙️ Passo 2: Configurar Variáveis de Ambiente

### 2.1 Navegar até Environment

1. Clique no serviço **lista-presentes**
2. No menu lateral, clique em **Environment**
3. Role até a seção "Environment Variables"

### 2.2 Remover Variável DATABASE_URL Antiga (se existir)

Se você já tem uma variável `DATABASE_URL` configurada (apontando para o PostgreSQL do Render):

1. Localize a variável `DATABASE_URL`
2. Clique no ícone de **três pontos** (...) ao lado
3. Selecione **Delete**
4. Confirme a exclusão

### 2.3 Adicionar Novas Variáveis

Clique em **Add Environment Variable** e adicione cada uma das seguintes variáveis:

#### Variável 1: DATABASE_URL (OBRIGATÓRIA)

```
Key:   DATABASE_URL
Value: postgresql://postgres:123ewqasdcxz%21%40%23@db.szyouijmxhlbavkzibxa.supabase.co:6543/postgres
```

#### Variável 2: SUPABASE_URL (OPCIONAL)

```
Key:   SUPABASE_URL
Value: https://szyouijmxhlbavkzibxa.supabase.co
```

#### Variável 3: SUPABASE_KEY (OPCIONAL)

```
Key:   SUPABASE_KEY
Value: sb_publishable_aswPuvIXjzcejBTyYWObdQ_BpC5l903
```

### 2.4 Salvar Alterações

1. Clique em **Save Changes** no topo da página
2. O Render irá automaticamente iniciar um novo deploy

---

## 🗄️ Passo 3: Remover PostgreSQL do Render (Opcional)

Se você tinha um banco PostgreSQL gerenciado pelo Render e não precisa mais dele:

### 3.1 Fazer Backup dos Dados (IMPORTANTE!)

**Antes de deletar**, faça backup dos dados:

```bash
# Execute localmente (substitua com sua DATABASE_URL antiga do Render)
pg_dump "sua-database-url-antiga-do-render" > backup_render.sql
```

### 3.2 Deletar o Database

1. No Dashboard do Render, vá para a seção **Databases**
2. Localize `lista-presentes-db`
3. Clique nos três pontos (...)
4. Selecione **Delete Database**
5. Digite o nome do database para confirmar
6. Clique em **Delete**

⚠️ **ATENÇÃO**: Esta ação é **irreversível**! Certifique-se de ter o backup!

---

## 🔄 Passo 4: Verificar o Deploy

### 4.1 Acompanhar Logs

1. No serviço **lista-presentes**, clique na aba **Logs**
2. Você verá o processo de build e deploy
3. Procure por estas mensagens importantes:

```
🔄 Creating migrations...
✓ No migrations to create

🗄️  Running migrations...
✓ Migrations applied successfully

✅ Verifying migrations...
✓ All migrations applied successfully
```

### 4.2 Verificar Erros Comuns

Se você ver erros, verifique:

#### Erro: "password authentication failed"

**Causa**: URL encoding incorreto na senha

**Solução**: Verifique se a DATABASE_URL está exatamente como:
```
postgresql://postgres:123ewqasdcxz%21%40%23@db.szyouijmxhlbavkzibxa.supabase.co:6543/postgres
```

#### Erro: "no pg_hba.conf entry for host"

**Causa**: IP não permitido no Supabase

**Solução**:
1. Acesse https://app.supabase.com/project/szyouijmxhlbavkzibxa/settings/database
2. Em "Connection Pooling" ou "Network Restrictions", certifique-se de que "Allow all IPs" está habilitado
3. Ou adicione os IPs do Render (consulte documentação do Render para IPs)

#### Erro: "too many connections"

**Causa**: Muitas conexões simultâneas

**Solução**: Use connection pooling na porta 6543:
```
postgresql://postgres:123ewqasdcxz%21%40%23@db.szyouijmxhlbavkzibxa.supabase.co:6543/postgres
```

---

## 🧪 Passo 5: Testar a Aplicação

### 5.1 Acessar a Aplicação

1. Clique no link da aplicação no topo do Dashboard (algo como `https://lista-presentes-xxx.onrender.com`)
2. Tente fazer login
3. Navegue pelas páginas

### 5.2 Testar Funcionalidades Críticas

- [ ] **Login**: Faça login com uma conta existente ou crie uma nova
- [ ] **Dashboard**: Verifique se os cards de estatísticas aparecem
- [ ] **Meus Presentes**: Liste seus presentes
- [ ] **Adicionar Presente**: Crie um novo presente
- [ ] **Ver Usuários**: Liste outros usuários
- [ ] **Grupos**: Verifique grupos e membros

### 5.3 Verificar Logs de Erro

Se algo não funcionar:

1. Vá para **Logs** no Dashboard do Render
2. Procure por mensagens de erro em vermelho
3. Copie a mensagem de erro completa

---

## 📊 Passo 6: Migrar Dados do Render para Supabase (Se Necessário)

Se você tinha dados importantes no PostgreSQL antigo do Render:

### Opção A: Importar via pg_restore (Recomendado)

```bash
# 1. No seu computador local, com o backup feito no Passo 3.1
psql "postgresql://postgres:123ewqasdcxz!@#@db.szyouijmxhlbavkzibxa.supabase.co:6543/postgres" < backup_render.sql
```

### Opção B: Via Supabase SQL Editor

1. Acesse https://app.supabase.com/project/szyouijmxhlbavkzibxa
2. Vá para **SQL Editor**
3. Clique em **New Query**
4. Cole o conteúdo do arquivo `backup_render.sql`
5. Clique em **Run**

### Opção C: Via Django Fixtures

```bash
# 1. Conectar ao banco ANTIGO do Render (localmente)
export DATABASE_URL="sua-url-antiga-do-render"
python manage.py dumpdata --natural-foreign --natural-primary \
  -e contenttypes -e auth.Permission > fixtures.json

# 2. Conectar ao Supabase
export DATABASE_URL="postgresql://postgres:123ewqasdcxz!@#@db.szyouijmxhlbavkzibxa.supabase.co:6543/postgres"
python manage.py migrate
python manage.py loaddata fixtures.json
```

---

## 🔍 Passo 7: Verificar no Supabase Dashboard

### 7.1 Acessar Supabase

1. Acesse https://app.supabase.com
2. Faça login
3. Selecione o projeto (szyouijmxhlbavkzibxa)

### 7.2 Verificar Tabelas

1. Menu lateral: **Table Editor**
2. Você deve ver tabelas como:
   - `auth_user`
   - `presentes_usuario`
   - `presentes_presente`
   - `presentes_grupo`
   - etc.

### 7.3 Verificar Dados

1. Clique em qualquer tabela (ex: `presentes_usuario`)
2. Você verá os dados em formato de planilha
3. Verifique se os dados foram migrados corretamente

### 7.4 Monitorar Conexões

1. Menu lateral: **Database**
2. Aba **Connection Pooling**
3. Veja conexões ativas e uso de recursos

---

## ✅ Checklist Final

Após completar todos os passos, verifique:

- [ ] DATABASE_URL configurada no Render apontando para Supabase
- [ ] SUPABASE_URL configurada no Render (opcional)
- [ ] SUPABASE_KEY configurada no Render (opcional)
- [ ] Deploy concluído com sucesso (sem erros nos logs)
- [ ] Migrações aplicadas (veja nos logs do build)
- [ ] Aplicação acessível e funcionando
- [ ] Login funcionando
- [ ] Dados exibidos corretamente
- [ ] Tabelas visíveis no Supabase Dashboard
- [ ] Backup do banco antigo salvo (se aplicável)
- [ ] PostgreSQL do Render deletado (opcional, economiza recursos)

---

## 🎉 Próximos Passos

Agora que o Supabase está configurado, você pode:

### 1. Explorar Recursos do Supabase

**Table Editor**: Edite dados diretamente
```
https://app.supabase.com/project/szyouijmxhlbavkzibxa/editor
```

**SQL Editor**: Execute queries personalizadas
```
https://app.supabase.com/project/szyouijmxhlbavkzibxa/sql
```

**Database Backups**: Configure backups automáticos
```
https://app.supabase.com/project/szyouijmxhlbavkzibxa/settings/database
```

### 2. Configurar Backups Automáticos

1. Acesse **Settings** > **Database**
2. Role até **Backups**
3. Backups são automáticos no free tier (7 dias de retenção)
4. Para backups sob demanda, use:
   ```sql
   -- No SQL Editor
   pg_dump via SQL Editor ou localmente
   ```

### 3. Habilitar Extensões PostgreSQL

```sql
-- No SQL Editor do Supabase
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "postgis";  -- Para dados geoespaciais
CREATE EXTENSION IF NOT EXISTS "pg_cron";  -- Para tarefas agendadas
```

### 4. Configurar Alertas

1. Acesse **Settings** > **Database** > **Monitoring**
2. Configure alertas para:
   - Uso de disco > 80%
   - Conexões > limite
   - Queries lentas

### 5. API REST Automática (Opcional)

O Supabase gera automaticamente uma API REST:

```bash
# Exemplo: Listar presentes
curl 'https://szyouijmxhlbavkzibxa.supabase.co/rest/v1/presentes_presente?select=*' \
  -H "apikey: sb_publishable_aswPuvIXjzcejBTyYWObdQ_BpC5l903" \
  -H "Authorization: Bearer sb_publishable_aswPuvIXjzcejBTyYWObdQ_BpC5l903"
```

---

## 🆘 Troubleshooting Avançado

### Problema: Deploy falha com erro de migração

**Sintomas**:
```
django.db.utils.ProgrammingError: relation "presentes_usuario" does not exist
```

**Solução**:
```bash
# Via Render Shell (acesse via Dashboard > Shell)
python manage.py migrate --run-syncdb
python manage.py migrate --fake-initial
```

### Problema: Conexão lenta

**Sintomas**: Requests demoram muito tempo

**Soluções**:
1. **Usar Connection Pooling** (porta 6543)
2. **Escolher região próxima**:
   - Render Oregon → Supabase US West
   - Render Frankfurt → Supabase EU Central
3. **Reduzir conn_max_age** em settings.py

### Problema: Dados não aparecem

**Sintomas**: Tabelas existem mas estão vazias

**Solução**: Verificar se as migrações criaram as tabelas corretamente
```bash
# Via Render Shell
python manage.py showmigrations
python manage.py migrate --list
```

### Problema: Erro de permissão

**Sintomas**:
```
permission denied for table presentes_presente
```

**Solução**: Verificar se o usuário `postgres` tem permissões
```sql
-- No SQL Editor do Supabase
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;
```

---

## 📚 Links Úteis

- **Supabase Dashboard**: https://app.supabase.com/project/szyouijmxhlbavkzibxa
- **Render Dashboard**: https://dashboard.render.com
- **Documentação Supabase**: https://supabase.com/docs
- **Documentação Render**: https://render.com/docs
- **Guia Completo Supabase**: Ver arquivo `SUPABASE.md` na raiz do projeto

---

## 📞 Suporte

Se você encontrar problemas:

1. **Verifique os logs do Render**: Dashboard > Logs
2. **Verifique os logs do Supabase**: Dashboard > Logs > Postgres Logs
3. **Consulte a documentação**: `SUPABASE.md`
4. **Verifique este checklist**: Role até o topo e siga passo-a-passo

---

## 🎯 Resumo Rápido (TL;DR)

```bash
# 1. Adicione no Render Dashboard > Environment:
DATABASE_URL=postgresql://postgres:123ewqasdcxz%21%40%23@db.szyouijmxhlbavkzibxa.supabase.co:6543/postgres
SUPABASE_URL=https://szyouijmxhlbavkzibxa.supabase.co
SUPABASE_KEY=sb_publishable_aswPuvIXjzcejBTyYWObdQ_BpC5l903

# 2. Salve e aguarde deploy automático

# 3. Verifique logs para confirmar migrações

# 4. Teste a aplicação

# 5. (Opcional) Delete o PostgreSQL antigo do Render

# Pronto! ✅
```

---

**Última atualização**: 2026-02-06
**Versão do projeto**: 1.1.18
