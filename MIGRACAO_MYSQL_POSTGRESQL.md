# 🔄 Guia de Migração: MySQL → PostgreSQL

## 📋 Sumário

- [Por que Migrar?](#por-que-migrar)
- [Método 1: Migração com Dados (Recomendado)](#método-1-migração-com-dados-recomendado)
- [Método 2: Migração Fresh (Sem Dados)](#método-2-migração-fresh-sem-dados)
- [Método 3: Migração no Render.com](#método-3-migração-no-rendercom)
- [Troubleshooting](#troubleshooting)

---

## 🤔 Por que Migrar?

### Vantagens do PostgreSQL

✅ **Melhor para produção**
- Mais robusto e confiável
- ACID compliance total
- Melhor concorrência

✅ **Hospedagem gratuita**
- Render.com oferece PostgreSQL free
- Heroku, Railway, Supabase também

✅ **Features avançadas**
- JSON fields
- Full-text search nativo
- Array fields

✅ **Django suporta melhor**
- Todas as features funcionam
- Migrations mais confiáveis

---

## 📦 Método 1: Migração com Dados (Recomendado)

Este método preserva todos os seus dados existentes.

### Passo 1: Instalar Dependências

```bash
pip install psycopg2-binary django-extensions
```

### Passo 2: Backup do MySQL

```bash
# Fazer dump do banco MySQL
python manage.py dumpdata > backup_mysql.json

# Ou específico por app
python manage.py dumpdata presentes > backup_presentes.json
python manage.py dumpdata auth > backup_auth.json
```

### Passo 3: Configurar PostgreSQL Local

#### Opção A: Usando Docker (Mais Fácil)

```bash
# docker-compose.yml já tem PostgreSQL configurado!
docker-compose up -d db

# Aguardar banco estar pronto
docker-compose logs db
```

#### Opção B: Instalar PostgreSQL Localmente

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo service postgresql start
```

**Mac (Homebrew):**
```bash
brew install postgresql
brew services start postgresql
```

**Windows:**
Baixar de [postgresql.org/download](https://www.postgresql.org/download/)

### Passo 4: Criar Banco PostgreSQL

```bash
# Entrar no PostgreSQL
sudo -u postgres psql

# Dentro do psql:
CREATE DATABASE lista_presentes;
CREATE USER lista_presentes_user WITH PASSWORD 'senha_segura';
ALTER ROLE lista_presentes_user SET client_encoding TO 'utf8';
ALTER ROLE lista_presentes_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE lista_presentes_user SET timezone TO 'America/Sao_Paulo';
GRANT ALL PRIVILEGES ON DATABASE lista_presentes TO lista_presentes_user;
\q
```

### Passo 5: Atualizar settings.py

O arquivo `settings.py` já está preparado! Basta configurar variável de ambiente:

```bash
# Criar/editar arquivo .env
nano .env
```

Adicionar:
```bash
DATABASE_URL=postgresql://lista_presentes_user:senha_segura@localhost:5432/lista_presentes
```

### Passo 6: Executar Migrations no PostgreSQL

```bash
# Deletar pasta de migrations antiga (opcional, mas recomendado)
rm -rf presentes/migrations/
mkdir presentes/migrations
touch presentes/migrations/__init__.py

# Criar novas migrations
python manage.py makemigrations

# Executar migrations
python manage.py migrate
```

### Passo 7: Importar Dados

```bash
# Carregar dados do backup
python manage.py loaddata backup_mysql.json

# Ou por partes:
python manage.py loaddata backup_auth.json
python manage.py loaddata backup_presentes.json
```

### Passo 8: Verificar Dados

```bash
# Entrar no shell Django
python manage.py shell

# Testar queries:
>>> from presentes.models import Usuario, Presente
>>> Usuario.objects.count()
>>> Presente.objects.all()[:5]
>>> exit()
```

### Passo 9: Testar Aplicação

```bash
python manage.py runserver

# Ou com Docker:
docker-compose up
```

✅ **Migração completa!** Todos os dados foram preservados.

---

## 🆕 Método 2: Migração Fresh (Sem Dados)

Use este método se não precisa manter os dados existentes.

### Passo 1: Atualizar .env

```bash
DATABASE_URL=postgresql://lista_presentes_user:senha_segura@localhost:5432/lista_presentes
```

### Passo 2: Migrations

```bash
# Deletar migrations antigas
rm -rf presentes/migrations/
mkdir presentes/migrations
touch presentes/migrations/__init__.py

# Deletar db.sqlite3 (se existir)
rm db.sqlite3

# Criar migrations
python manage.py makemigrations

# Executar migrations
python manage.py migrate
```

### Passo 3: Criar Superusuário

```bash
python manage.py createsuperuser
```

### Passo 4: Dados de Teste (Opcional)

```bash
# Criar via shell Django
python manage.py shell

>>> from presentes.models import Usuario
>>> usuario = Usuario.objects.create_user(
...     username='joao',
...     email='joao@example.com',
...     password='senha123',
...     first_name='João',
...     last_name='Silva'
... )
>>> exit()
```

✅ **Banco novo criado!**

---

## ☁️ Método 3: Migração no Render.com

### Cenário: Você tem dados no MySQL local e quer migrar para Render

#### Passo 1: Deploy no Render (PostgreSQL será criado automaticamente)

Siga o [README_DOCKER.md](README_DOCKER.md) para fazer deploy.

#### Passo 2: Backup Local

```bash
# No seu computador (MySQL local)
python manage.py dumpdata > backup_production.json
```

#### Passo 3: Upload para Render via Shell

1. Acesse o **Render Dashboard**
2. Vá em seu Web Service → **Shell**
3. Upload do arquivo:

```bash
# No Shell do Render:
cat > backup_production.json << 'EOF'
[cole o conteúdo do backup aqui]
EOF
```

#### Passo 4: Importar Dados no Render

```bash
# Ainda no Shell do Render:
python manage.py loaddata backup_production.json
```

#### Método Alternativo: Via psql direto

```bash
# 1. Exportar do MySQL local para SQL
mysqldump -u root -p lista_presentes_db > mysql_dump.sql

# 2. Converter MySQL SQL para PostgreSQL
# Usar ferramenta: https://github.com/lanyrd/mysql-postgresql-converter
pgloader mysql_dump.sql > postgres_dump.sql

# 3. Importar no Render PostgreSQL
# Pegar credenciais em: Render Dashboard → Database → Connection String
psql postgresql://user:pass@host/db < postgres_dump.sql
```

---

## 🔧 Troubleshooting

### Problema: "ImproperlyConfigured: Error loading psycopg2 module"

**Causa:** `psycopg2-binary` não instalado

**Solução:**
```bash
pip install psycopg2-binary
```

### Problema: "FATAL: role does not exist"

**Causa:** Usuário PostgreSQL não criado

**Solução:**
```bash
sudo -u postgres psql
CREATE USER lista_presentes_user WITH PASSWORD 'senha';
\q
```

### Problema: "database does not exist"

**Causa:** Banco não foi criado

**Solução:**
```bash
sudo -u postgres psql
CREATE DATABASE lista_presentes;
\q
```

### Problema: "loaddata failed: IntegrityError"

**Causa:** Chaves estrangeiras ou conflitos de IDs

**Solução:**
```bash
# Opção 1: Limpar banco e tentar novamente
python manage.py flush
python manage.py loaddata backup.json

# Opção 2: Importar em ordem
python manage.py loaddata backup_auth.json
python manage.py loaddata backup_presentes.json

# Opção 3: Ignorar erros (última opção)
python manage.py loaddata backup.json --ignorenonexistent
```

### Problema: "Column does not exist" após migração

**Causa:** Migrations desatualizadas

**Solução:**
```bash
# Deletar migrations antigas
rm -rf presentes/migrations/

# Criar novas
python manage.py makemigrations presentes

# Aplicar
python manage.py migrate
```

### Problema: Erro de encoding (caracteres especiais)

**Solução:**
```bash
# Ao criar banco PostgreSQL:
CREATE DATABASE lista_presentes
    ENCODING 'UTF8'
    LC_COLLATE 'pt_BR.UTF-8'
    LC_CTYPE 'pt_BR.UTF-8';
```

### Problema: Permissões negadas no PostgreSQL

**Solução:**
```bash
sudo -u postgres psql
GRANT ALL PRIVILEGES ON DATABASE lista_presentes TO lista_presentes_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO lista_presentes_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO lista_presentes_user;
\q
```

---

## 🔍 Verificar Migração Bem-Sucedida

```bash
# 1. Verificar conexão
python manage.py dbshell

# 2. Contar registros
python manage.py shell
>>> from presentes.models import Usuario, Presente, Compra
>>> print(f"Usuários: {Usuario.objects.count()}")
>>> print(f"Presentes: {Presente.objects.count()}")
>>> print(f"Compras: {Compra.objects.count()}")

# 3. Testar queries complexas
>>> Usuario.objects.filter(ativo=True).count()
>>> Presente.objects.filter(status='ATIVO').select_related('usuario')

# 4. Verificar integridade
>>> from django.core import management
>>> management.call_command('check')
```

---

## 📊 Comparação: MySQL vs PostgreSQL

| Feature | MySQL | PostgreSQL |
|---------|-------|------------|
| **Tipo** | Relacional | Relacional + NoSQL |
| **ACID** | Parcial | Completo |
| **Concorrência** | Locks | MVCC |
| **JSON** | Limitado | Completo |
| **Full-text** | Básico | Avançado |
| **Hospedagem Free** | Raro | Comum |
| **Django Support** | Bom | Excelente |

---

## 🎯 Checklist de Migração

- [ ] Backup completo do MySQL feito
- [ ] PostgreSQL instalado/configurado
- [ ] DATABASE_URL atualizado
- [ ] Dependências instaladas (psycopg2)
- [ ] Migrations executadas
- [ ] Dados importados
- [ ] Verificação de contagens
- [ ] Testes manuais realizados
- [ ] Superusuário funciona
- [ ] Upload de imagens funciona
- [ ] Notificações funcionam
- [ ] Busca com IA funciona

---

## 💡 Dicas Importantes

### 1. Sempre Faça Backup

```bash
# MySQL
mysqldump -u root -p lista_presentes_db > backup_$(date +%Y%m%d).sql

# PostgreSQL
pg_dump -U lista_presentes_user lista_presentes > backup_$(date +%Y%m%d).sql
```

### 2. Teste em Ambiente Local Primeiro

Nunca migre direto em produção. Teste localmente primeiro!

### 3. Use Docker para Testes

```bash
# docker-compose.yml já tem tudo configurado!
docker-compose up -d
```

### 4. Monitore Logs Durante Migração

```bash
# Ver logs Django
python manage.py runserver --verbosity 3

# Ver logs PostgreSQL
tail -f /var/log/postgresql/postgresql-15-main.log
```

---

## 🆘 Precisa de Ajuda?

- **PostgreSQL Docs:** [postgresql.org/docs](https://www.postgresql.org/docs/)
- **Django Databases:** [docs.djangoproject.com/en/5.0/ref/databases](https://docs.djangoproject.com/en/5.0/ref/databases/)
- **Render PostgreSQL:** [render.com/docs/databases](https://render.com/docs/databases)

---

**✅ Migração Concluída!** Seu sistema agora usa PostgreSQL, mais robusto e pronto para produção!
