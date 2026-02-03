# Gerenciamento de Migrações no Render

Este documento descreve como as migrações são gerenciadas automaticamente no Render e como resolver problemas.

## Processo Automático de Deploy

Quando você faz push para a branch `master`, o Render executa automaticamente:

### 1. Build Script (`build.sh`)

O arquivo `build.sh` é executado e realiza:

1. **Upgrade do pip**
2. **Instalação de dependências** (`requirements.txt`)
3. **Coleta de arquivos estáticos** (`collectstatic`)
4. **Criação de migrações** (`makemigrations`)
5. **Verificação de migrações pendentes** (`showmigrations`)
6. **Aplicação de migrações** (`migrate --run-syncdb`)
7. **Verificação final** (confirma que todas migrações foram aplicadas)
8. **Criação/ajuste do usuário admin** (`fix_admin`)

### 2. Comandos Executados

```bash
# Criar migrações novas (se houver mudanças nos models)
python manage.py makemigrations --noinput

# Verificar migrações pendentes
python manage.py showmigrations --plan

# Aplicar todas as migrações (força com --run-syncdb)
python manage.py migrate --noinput --run-syncdb

# Verificar se todas foram aplicadas
python manage.py showmigrations | grep "\[ \]"
```

## Comando Customizado: force_migrate

Criamos um comando Django customizado para forçar migrações:

### Uso Básico

```bash
# Aplicar todas as migrações forçadamente
python manage.py force_migrate

# Apenas verificar sem aplicar
python manage.py force_migrate --check

# Modo verboso (mais detalhes)
python manage.py force_migrate --verbose
```

### O que o comando faz:

1. Testa conexão com banco de dados
2. Mostra status atual das migrações
3. Cria novas migrações se necessário
4. Aplica todas as migrações com `--run-syncdb`
5. Verifica status final

## Script Manual: force_migrations.sh

Para casos extremos, use o script bash:

```bash
# No Render, via Shell
bash scripts/force_migrations.sh
```

Este script:
- Verifica se está no ambiente Render
- Mostra todas as migrações pendentes
- Cria e aplica migrações forçadamente
- Valida que todas foram aplicadas
- Retorna erro se houver migrações pendentes

## Resolver Problemas Comuns

### Problema 1: Migrações não aplicadas no deploy

**Solução 1: Verificar logs do build**
```bash
# No Render Dashboard
1. Vá em "Logs"
2. Procure por "Running migrations"
3. Veja se houve erros
```

**Solução 2: Executar manualmente via Shell**
```bash
# No Render Dashboard > Shell
python manage.py force_migrate --verbose
```

### Problema 2: Conflitos de migração

**Solução:**
```bash
# Via Shell do Render
# 1. Verificar conflitos
python manage.py showmigrations

# 2. Resolver conflitos (se necessário)
python manage.py makemigrations --merge

# 3. Aplicar novamente
python manage.py migrate --run-syncdb
```

### Problema 3: Migrações "fake" (já aplicadas mas não registradas)

**Solução:**
```bash
# Marcar migração como aplicada sem executar
python manage.py migrate --fake presentes 0004

# Depois aplicar as restantes
python manage.py migrate
```

## Verificar Status das Migrações

### Via Dashboard do Render

1. Acesse o **Shell** no dashboard do Render
2. Execute:
```bash
python manage.py showmigrations
```

### Via Logs

Os logs do build mostram:
```
🔄 Creating migrations...
✅ No migrations to create

🔍 Checking for pending migrations...
🗄️  Running migrations...
✅ All migrations applied successfully
```

## Deploy Manual de Migrações

Se o processo automático falhar:

### Opção 1: Via Shell do Render

```bash
# 1. Abrir Shell no dashboard
# 2. Executar comando customizado
python manage.py force_migrate
```

### Opção 2: Forçar novo deploy

```bash
# 1. Fazer qualquer mudança (ex: adicionar comentário)
# 2. Commit e push
git commit --allow-empty -m "Force rebuild"
git push origin master
```

### Opção 3: Redeploy manual

1. No dashboard do Render
2. Clique em "Manual Deploy"
3. Escolha "Clear build cache & deploy"

## Monitoramento

### Verificar se migrações estão OK

```bash
# Verificar status
python manage.py showmigrations

# Sem [ ] = OK
# Com [ ] = Migração pendente
```

### Logs importantes

```
✅ All migrations applied successfully  # Tudo OK
⚠️  WARNING: Some migrations not applied!  # Problema!
```

## Arquivos de Configuração

### build.sh
- Local: `/build.sh`
- Função: Script principal de build do Render
- Quando executa: Cada deploy
- Inclui: makemigrations + migrate + verificação

### render.yaml
- Local: `/render.yaml`
- Função: Configuração do serviço no Render
- Define: `buildCommand: bash build.sh`

### force_migrations.sh
- Local: `/scripts/force_migrations.sh`
- Função: Script bash para forçar migrações manualmente
- Uso: Casos de emergência via Shell

### force_migrate command
- Local: `/presentes/management/commands/force_migrate.py`
- Função: Comando Django customizado
- Uso: `python manage.py force_migrate`

## Fluxo de Deploy Completo

```
1. Push para master
   ↓
2. Render detecta mudança
   ↓
3. Executa build.sh
   ↓
4. pip install -r requirements.txt
   ↓
5. collectstatic --noinput
   ↓
6. makemigrations --noinput
   ↓
7. showmigrations --plan
   ↓
8. migrate --run-syncdb --noinput
   ↓
9. Verifica migrações aplicadas
   ↓
10. fix_admin
   ↓
11. Inicia gunicorn
```

## Troubleshooting

### Error: "No migrations to apply"
✅ Isso é bom! Significa que está tudo em dia.

### Error: "Migration X conflicts with Y"
❌ Resolva com `makemigrations --merge`

### Error: "Can't connect to database"
❌ Verifique DATABASE_URL nas variáveis de ambiente

### Warning: "Some migrations not applied"
⚠️  Execute `python manage.py force_migrate` via Shell

## Contato e Suporte

Se os problemas persistirem:

1. Verifique logs completos no Render Dashboard
2. Execute `force_migrate --verbose` para mais detalhes
3. Use `showmigrations` para ver status exato
4. Entre em contato com Maxwell Oliveira (@maxwbh)
