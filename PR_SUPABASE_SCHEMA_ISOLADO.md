# Pull Request: Configurar Supabase PostgreSQL com Schema Isolado lista_presentes

## Resumo

Configura aplicação para usar Supabase PostgreSQL com schema isolado `lista_presentes`, permitindo múltiplas apps Django compartilharem o mesmo banco sem conflitos.

## Principais Mudanças

### ⚙️ Configuração de Banco de Dados

**settings.py (lista_presentes/settings.py:117-133)**
- Força `search_path=lista_presentes` em todas as conexões PostgreSQL
- Adiciona signal `connection_created` para garantir schema correto
- Preserva OPTIONS existentes do `dj_database_url`
- Estrutura baseada em projeto Gestao-Contrato (funcionando em produção)

```python
# Preservar OPTIONS e adicionar search_path
if 'OPTIONS' not in DATABASES['default']:
    DATABASES['default']['OPTIONS'] = {}

DATABASES['default']['OPTIONS']['options'] = '-c search_path=lista_presentes'

# Signal para garantir search_path
from django.db.backends.signals import connection_created
def set_search_path(sender, connection, **kwargs):
    if connection.vendor == 'postgresql':
        cursor = connection.cursor()
        cursor.execute("SET search_path TO lista_presentes")
connection_created.connect(set_search_path)
```

**render.yaml**
- DATABASE_URL como manual (`sync: false`)
- Seção `databases:` comentada (não cria Render PostgreSQL)
- Schema aplicado automaticamente via código

### 📚 Documentação

**Reorganização Completa (42 → 12 arquivos markdown)**

Estrutura criada:
```
docs/
├── database/
│   ├── SUPABASE.md (consolidado de 9 arquivos)
│   ├── SCHEMA_ISOLADO.md
│   ├── migrations.md
│   └── MIGRACAO_IMAGENS_BASE64.md
├── deployment/
│   ├── RENDER.md (consolidado de 6 arquivos)
│   └── DOCKER.md (consolidado de 4 arquivos)
├── features/
│   ├── TEMAS.md
│   ├── SCRAPING_LOGS.md
│   ├── SETUP_GRUPOS.md
│   ├── SOCIAL_LOGIN_CONFIG.md
│   └── KEEP_ALIVE.md
└── development/
    ├── VERSIONAMENTO.md
    ├── DEBUG_500_ERRORS.md
    └── CONTRIBUTING.md
```

**Removidos:**
- 28 arquivos obsoletos (Oracle migration, duplicados)
- MIGRACAO_MYSQL_POSTGRESQL.md (MySQL nunca usado)
- MIGRACAO_SUPABASE_RENDER.md (usando Supabase permanentemente)

**Atualizados:**
- SUPABASE.md: Schema isolado como configuração padrão
- RENDER.md: DATABASE_URL sem `?options=` (aplicado via código)
- SCHEMA_ISOLADO.md: Guia completo de migração

### 🔒 Segurança

**Credenciais Removidas da Documentação**
- Project IDs mascarados
- Senhas removidas
- API Keys substituídas por placeholders
- URLs específicas generalizadas

**Row Level Security (RLS)**
- Habilitado em 23 tabelas Django
- Script atualizado para schema `lista_presentes`
- PostgREST API bloqueada, Django funciona normalmente

### 📝 Commits

1. `feat: Configurar Render Free para usar Supabase com schema isolado`
2. `docs: Remover documentações desnecessárias`
3. `feat: Forçar criação de schema lista_presentes (estrutura Gestao-Contrato)`
4. `fix: Preservar OPTIONS do dj_database_url ao adicionar search_path`

## Configuração Requerida

### DATABASE_URL (Render Dashboard)

```
postgresql://postgres.PROJECT:PASS@aws-1-us-east-2.pooler.supabase.com:6543/postgres
```

**Importante:**
- Usar Connection Pooler (porta 6543)
- NÃO adicionar `?options=` (aplicado automaticamente)
- Schema `lista_presentes` configurado via `settings.py`

### ✨ Criação Automática do Schema

O schema `lista_presentes` é criado **automaticamente** durante o build do Render:

1. **Script:** `scripts/ensure_schema.py`
2. **Execução:** Antes das migrations Django (via `build.sh`)
3. **Idempotente:** Seguro executar múltiplas vezes
4. **Permissões:** Concedidas automaticamente ao role `postgres`

**Nenhuma ação manual necessária!** O build do Render cria tudo automaticamente.

### Variáveis Opcionais

```bash
SUPABASE_URL=https://PROJECT_ID.supabase.co
SUPABASE_KEY=sb_publishable_YOUR_ANON_KEY
```

## Testes

- [ ] Build Render com sucesso
- [ ] Migrations executadas no schema `lista_presentes`
- [ ] Tabelas criadas no schema correto
- [ ] Login funcionando
- [ ] Isolamento de outras apps Django verificado

## Referências

- Projeto Gestao-Contrato: https://github.com/Maxwbh/Gestao-Contrato
- Documentação: docs/database/SCHEMA_ISOLADO.md
- Scripts SQL: scripts/create_isolated_schema.sql

## Versão

**1.1.40** (build 44)

---

## Como Criar o PR

### Opção 1: Interface Web GitHub

Acesse: https://github.com/Maxwbh/Lista_de_Presentes/compare/master...claude/apply-login-theme-app-L1t7x

### Opção 2: GitHub CLI

```bash
gh pr create --title "Configurar Supabase PostgreSQL com Schema Isolado lista_presentes" --body-file PR_SUPABASE_SCHEMA_ISOLADO.md
```

https://claude.ai/code/session_01KK97osnRZ6zD6iGige5656
