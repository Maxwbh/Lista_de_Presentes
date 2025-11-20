# 🐧 Guia de Instalação - Ubuntu Server (Desenvolvimento)

Guia completo para configurar o ambiente de desenvolvimento do **Lista de Presentes** em Ubuntu Server.

---

## 📋 Sumário

- [Pré-requisitos](#pré-requisitos)
- [Instalação Rápida](#instalação-rápida)
- [Instalação Detalhada](#instalação-detalhada)
  - [1. Atualizar Sistema](#1-atualizar-sistema)
  - [2. Instalar Python 3.11](#2-instalar-python-311)
  - [3. Instalar PostgreSQL](#3-instalar-postgresql)
  - [4. Clonar Repositório](#4-clonar-repositório)
  - [5. Configurar Ambiente Virtual](#5-configurar-ambiente-virtual)
  - [6. Configurar Banco de Dados](#6-configurar-banco-de-dados)
  - [7. Executar Migrations](#7-executar-migrations)
  - [8. Criar Superusuário](#8-criar-superusuário)
  - [9. Executar Servidor](#9-executar-servidor)
- [Configuração de Produção](#configuração-de-produção)
- [Troubleshooting](#troubleshooting)

---

## 🔧 Pré-requisitos

### Versões Testadas
- **Ubuntu Server**: 20.04 LTS, 22.04 LTS, 24.04 LTS
- **Python**: 3.11+
- **PostgreSQL**: 14, 15, 16
- **RAM**: Mínimo 1 GB (recomendado 2 GB)
- **Disco**: 2 GB livres

### Acesso
- Usuário com privilégios `sudo`
- Conexão à internet
- Acesso SSH (se remoto)

---

## ⚡ Instalação Rápida

Para desenvolvedores experientes:

```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependências
sudo apt install -y python3.11 python3.11-venv python3.11-dev \
    postgresql postgresql-contrib libpq-dev git build-essential \
    pkg-config default-libmysqlclient-dev

# Clonar repositório
git clone https://github.com/Maxwbh/Lista_de_Presentes.git
cd Lista_de_Presentes

# Criar ambiente virtual
python3.11 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install --upgrade pip
pip install -r requirements.txt

# Configurar .env
cp .env.example .env
nano .env  # Editar conforme necessário

# Configurar banco de dados PostgreSQL
sudo -u postgres psql -c "CREATE DATABASE lista_presentes;"
sudo -u postgres psql -c "CREATE USER lista_user WITH PASSWORD 'senha_segura';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE lista_presentes TO lista_user;"
sudo -u postgres psql -c "ALTER DATABASE lista_presentes OWNER TO lista_user;"

# Executar migrations
python manage.py makemigrations
python manage.py migrate

# Criar superusuário
python manage.py createsuperuser

# Coletar arquivos estáticos
python manage.py collectstatic --noinput

# Executar servidor de desenvolvimento
python manage.py runserver 0.0.0.0:8000
```

Acesse: `http://seu-ip:8000`

---

## 📖 Instalação Detalhada

### 1. Atualizar Sistema

```bash
# Atualizar lista de pacotes
sudo apt update

# Atualizar pacotes instalados
sudo apt upgrade -y

# Reiniciar se necessário (kernel updates)
sudo reboot  # Opcional
```

---

### 2. Instalar Python 3.11

#### Ubuntu 22.04+ (Python 3.11 disponível)

```bash
# Instalar Python 3.11
sudo apt install -y python3.11 python3.11-venv python3.11-dev

# Verificar instalação
python3.11 --version
# Saída esperada: Python 3.11.x
```

#### Ubuntu 20.04 (Adicionar PPA)

```bash
# Adicionar PPA do deadsnakes
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update

# Instalar Python 3.11
sudo apt install -y python3.11 python3.11-venv python3.11-dev

# Verificar instalação
python3.11 --version
```

#### Instalar pip

```bash
# Instalar pip para Python 3.11
sudo apt install -y python3-pip

# Ou instalar via get-pip.py
curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11

# Verificar pip
python3.11 -m pip --version
```

---

### 3. Instalar PostgreSQL

```bash
# Instalar PostgreSQL
sudo apt install -y postgresql postgresql-contrib libpq-dev

# Verificar instalação
psql --version
# Saída esperada: psql (PostgreSQL) 14.x ou superior

# Verificar status do serviço
sudo systemctl status postgresql

# Iniciar PostgreSQL (se não estiver rodando)
sudo systemctl start postgresql

# Habilitar PostgreSQL na inicialização
sudo systemctl enable postgresql
```

#### Instalar Dependências de Compilação

```bash
# Necessário para psycopg2 e mysqlclient
sudo apt install -y build-essential pkg-config \
    default-libmysqlclient-dev python3-dev
```

---

### 4. Clonar Repositório

```bash
# Instalar Git (se não instalado)
sudo apt install -y git

# Clonar repositório
cd ~
git clone https://github.com/Maxwbh/Lista_de_Presentes.git

# Ou usar SSH
# git clone git@github.com:Maxwbh/Lista_de_Presentes.git

# Entrar no diretório
cd Lista_de_Presentes

# Verificar branch
git branch
# Deve estar em: claude/review-wishlist-system-01KfJhmcrfGbvMcnDhbE7pNx

# Se não estiver, mudar para o branch correto
git checkout claude/review-wishlist-system-01KfJhmcrfGbvMcnDhbE7pNx
```

---

### 5. Configurar Ambiente Virtual

```bash
# Criar ambiente virtual
python3.11 -m venv venv

# Ativar ambiente virtual
source venv/bin/activate

# Seu prompt deve mudar para:
# (venv) user@hostname:~/Lista_de_Presentes$

# Upgrade pip
pip install --upgrade pip

# Instalar dependências do projeto
pip install -r requirements.txt

# Verificar instalação do Django
python -c "import django; print(django.get_version())"
# Saída esperada: 5.0
```

#### Configurar Variáveis de Ambiente

```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar .env
nano .env

# Configurar as seguintes variáveis:
```

**Arquivo `.env`** (mínimo para desenvolvimento):
```bash
# Django
SECRET_KEY=django-insecure-seu-secret-key-aqui-mude-em-producao
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,seu-ip-local

# Banco de Dados PostgreSQL
DATABASE_URL=postgresql://lista_user:senha_segura@localhost:5432/lista_presentes

# APIs de IA (opcional para desenvolvimento)
ANTHROPIC_API_KEY=sua-chave-anthropic-opcional
OPENAI_API_KEY=sua-chave-openai-opcional
GEMINI_API_KEY=sua-chave-gemini-opcional
```

**Gerar SECRET_KEY** (recomendado):
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

### 6. Configurar Banco de Dados

#### Criar Banco e Usuário PostgreSQL

```bash
# Trocar para usuário postgres
sudo -i -u postgres

# Abrir psql
psql

# Ou em uma linha:
sudo -u postgres psql
```

**Comandos SQL** (executar no psql):
```sql
-- Criar banco de dados
CREATE DATABASE lista_presentes;

-- Criar usuário
CREATE USER lista_user WITH PASSWORD 'senha_segura_aqui';

-- Conceder privilégios
GRANT ALL PRIVILEGES ON DATABASE lista_presentes TO lista_user;

-- Alterar owner do banco
ALTER DATABASE lista_presentes OWNER TO lista_user;

-- PostgreSQL 15+ (permissões adicionais)
\c lista_presentes
GRANT ALL ON SCHEMA public TO lista_user;

-- Sair do psql
\q
```

#### Verificar Conexão

```bash
# Testar conexão (fora do psql)
psql -h localhost -U lista_user -d lista_presentes -W

# Digitar senha quando solicitado
# Se conectar com sucesso, digite \q para sair
```

#### Configurar Autenticação PostgreSQL (se necessário)

Se receber erro de autenticação:

```bash
# Editar pg_hba.conf
sudo nano /etc/postgresql/14/main/pg_hba.conf

# Adicionar/modificar linha (antes das outras regras):
# local   all             lista_user                              md5

# Reiniciar PostgreSQL
sudo systemctl restart postgresql
```

---

### 7. Executar Migrations

```bash
# Certifique-se de estar no diretório do projeto com venv ativo
cd ~/Lista_de_Presentes
source venv/bin/activate

# Criar migrations (já devem existir)
python manage.py makemigrations

# Saída esperada:
# No changes detected (migrations já criadas)

# Aplicar migrations
python manage.py migrate

# Saída esperada:
# Running migrations:
#   Applying contenttypes.0001_initial... OK
#   Applying auth.0001_initial... OK
#   ...
#   Applying presentes.0001_initial... OK
```

#### Verificar Migrations

```bash
# Listar todas as migrations
python manage.py showmigrations

# Verificar status das migrations do app presentes
python manage.py showmigrations presentes

# Saída esperada:
# presentes
#  [X] 0001_initial
```

---

### 8. Criar Superusuário

```bash
# Criar superusuário admin
python manage.py createsuperuser

# Responder as perguntas:
# E-mail: admin@example.com
# Username: admin
# Password: ******** (mínimo 8 caracteres)
# Password (again): ********
```

---

### 9. Executar Servidor

#### Coletar Arquivos Estáticos

```bash
# Coletar arquivos estáticos
python manage.py collectstatic --noinput

# Saída esperada:
# 186 static files copied to '/home/user/Lista_de_Presentes/staticfiles'
```

#### Iniciar Servidor de Desenvolvimento

```bash
# Executar servidor (localhost apenas)
python manage.py runserver

# Ou permitir acesso externo:
python manage.py runserver 0.0.0.0:8000

# Saída esperada:
# Watching for file changes with StatReloader
# Performing system checks...
#
# System check identified no issues (0 silenced).
# November 20, 2025 - 18:00:00
# Django version 5.0, using settings 'lista_presentes.settings'
# Starting development server at http://0.0.0.0:8000/
# Quit the server with CONTROL-C.
```

#### Acessar Aplicação

**Navegador Web:**
- **Local**: http://localhost:8000
- **Remoto**: http://seu-ip:8000

**Páginas importantes:**
- **Home/Login**: http://localhost:8000/
- **Admin**: http://localhost:8000/admin/
- **Dashboard**: http://localhost:8000/dashboard/

#### Testar Admin

1. Acesse: http://localhost:8000/admin/
2. Login com superusuário criado
3. Verifique se pode ver: Usuários, Presentes, Compras, Sugestões, Notificações

---

## 🚀 Configuração de Produção

### Opção 1: Nginx + Gunicorn

#### Instalar Nginx

```bash
sudo apt install -y nginx
```

#### Criar Arquivo de Configuração Nginx

```bash
sudo nano /etc/nginx/sites-available/lista-presentes
```

**Conteúdo**:
```nginx
server {
    listen 80;
    server_name seu-dominio.com www.seu-dominio.com;

    location /static/ {
        alias /home/user/Lista_de_Presentes/staticfiles/;
    }

    location /media/ {
        alias /home/user/Lista_de_Presentes/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### Habilitar Site

```bash
# Criar link simbólico
sudo ln -s /etc/nginx/sites-available/lista-presentes /etc/nginx/sites-enabled/

# Testar configuração
sudo nginx -t

# Reiniciar Nginx
sudo systemctl restart nginx
```

#### Executar Gunicorn

```bash
# Dentro do diretório do projeto com venv ativo
cd ~/Lista_de_Presentes
source venv/bin/activate

# Executar Gunicorn
gunicorn --bind 127.0.0.1:8000 --workers 3 lista_presentes.wsgi:application

# Ou em background:
gunicorn --bind 127.0.0.1:8000 --workers 3 --daemon lista_presentes.wsgi:application
```

#### Criar Serviço Systemd (Recomendado)

```bash
sudo nano /etc/systemd/system/lista-presentes.service
```

**Conteúdo**:
```ini
[Unit]
Description=Lista de Presentes Django App
After=network.target

[Service]
Type=simple
User=user
Group=www-data
WorkingDirectory=/home/user/Lista_de_Presentes
Environment="PATH=/home/user/Lista_de_Presentes/venv/bin"
ExecStart=/home/user/Lista_de_Presentes/venv/bin/gunicorn \
    --workers 3 \
    --bind 127.0.0.1:8000 \
    --timeout 120 \
    lista_presentes.wsgi:application

Restart=always

[Install]
WantedBy=multi-user.target
```

**Habilitar e Iniciar Serviço**:
```bash
# Recarregar systemd
sudo systemctl daemon-reload

# Habilitar serviço
sudo systemctl enable lista-presentes

# Iniciar serviço
sudo systemctl start lista-presentes

# Verificar status
sudo systemctl status lista-presentes

# Ver logs
sudo journalctl -u lista-presentes -f
```

---

### Opção 2: SSL/HTTPS com Let's Encrypt

```bash
# Instalar Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obter certificado SSL
sudo certbot --nginx -d seu-dominio.com -d www.seu-dominio.com

# Renovação automática (já configurado por padrão)
sudo certbot renew --dry-run
```

---

## 🐛 Troubleshooting

### Erro: `ModuleNotFoundError: No module named 'django'`

**Causa**: Ambiente virtual não está ativado

**Solução**:
```bash
source venv/bin/activate
```

---

### Erro: `psycopg2.OperationalError: connection to server failed`

**Causa**: PostgreSQL não está rodando ou configuração incorreta

**Solução**:
```bash
# Verificar status
sudo systemctl status postgresql

# Iniciar PostgreSQL
sudo systemctl start postgresql

# Verificar DATABASE_URL no .env
cat .env | grep DATABASE_URL
```

---

### Erro: `django.db.utils.OperationalError: FATAL: password authentication failed`

**Causa**: Senha incorreta no DATABASE_URL

**Solução**:
```bash
# Resetar senha do usuário PostgreSQL
sudo -u postgres psql
ALTER USER lista_user WITH PASSWORD 'nova_senha_segura';
\q

# Atualizar .env
nano .env
# DATABASE_URL=postgresql://lista_user:nova_senha_segura@localhost:5432/lista_presentes
```

---

### Erro: `ALLOWED_HOSTS`

**Causa**: IP/domínio não está em ALLOWED_HOSTS

**Solução**:
```bash
# Editar .env
nano .env

# Adicionar seu IP/domínio
ALLOWED_HOSTS=localhost,127.0.0.1,seu-ip,seu-dominio.com
```

---

### Erro: `Migrations not applied`

**Causa**: Migrations não foram executadas

**Solução**:
```bash
python manage.py migrate
```

---

### Erro: `Static files not found (404)`

**Causa**: Arquivos estáticos não foram coletados

**Solução**:
```bash
python manage.py collectstatic --noinput
```

---

### Erro: `Port 8000 already in use`

**Causa**: Outro processo usando a porta 8000

**Solução**:
```bash
# Encontrar processo
sudo lsof -i :8000

# Matar processo
sudo kill -9 PID

# Ou usar outra porta
python manage.py runserver 0.0.0.0:8001
```

---

### Erro: `mysqlclient install failed`

**Causa**: Faltam dependências de desenvolvimento

**Solução**:
```bash
sudo apt install -y build-essential pkg-config \
    default-libmysqlclient-dev python3-dev

pip install mysqlclient
```

---

## 📚 Comandos Úteis

### Django

```bash
# Criar migrations
python manage.py makemigrations

# Aplicar migrations
python manage.py migrate

# Criar superusuário
python manage.py createsuperuser

# Coletar statics
python manage.py collectstatic

# Shell Django
python manage.py shell

# Verificar configuração
python manage.py check

# Executar testes
python manage.py test
```

### PostgreSQL

```bash
# Conectar ao banco
psql -h localhost -U lista_user -d lista_presentes -W

# Backup
pg_dump -U lista_user lista_presentes > backup.sql

# Restore
psql -U lista_user lista_presentes < backup.sql

# Listar bancos
sudo -u postgres psql -c "\l"

# Listar usuários
sudo -u postgres psql -c "\du"
```

### Git

```bash
# Atualizar código
git pull origin claude/review-wishlist-system-01KfJhmcrfGbvMcnDhbE7pNx

# Verificar status
git status

# Ver logs
git log --oneline -10
```

### Ambiente Virtual

```bash
# Ativar
source venv/bin/activate

# Desativar
deactivate

# Recriar (se necessário)
rm -rf venv
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 📞 Suporte

### Logs

```bash
# Logs do Django (servidor de desenvolvimento)
# Aparecem no terminal onde você executou runserver

# Logs do Gunicorn (produção)
sudo journalctl -u lista-presentes -f

# Logs do Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Logs do PostgreSQL
sudo tail -f /var/log/postgresql/postgresql-14-main.log
```

### Verificação de Saúde

```bash
# Verificar serviços
sudo systemctl status postgresql
sudo systemctl status nginx
sudo systemctl status lista-presentes

# Verificar portas
sudo netstat -tlnp | grep :8000
sudo netstat -tlnp | grep :5432
sudo netstat -tlnp | grep :80

# Verificar processos Python
ps aux | grep python
```

---

## 🎯 Checklist de Instalação

- [ ] Sistema atualizado
- [ ] Python 3.11 instalado
- [ ] PostgreSQL instalado e rodando
- [ ] Repositório clonado
- [ ] Ambiente virtual criado e ativado
- [ ] Dependências instaladas
- [ ] Arquivo .env configurado
- [ ] Banco de dados criado
- [ ] Usuário PostgreSQL criado
- [ ] Migrations executadas
- [ ] Superusuário criado
- [ ] Arquivos estáticos coletados
- [ ] Servidor rodando
- [ ] Login no admin funcionando
- [ ] (Produção) Nginx configurado
- [ ] (Produção) Gunicorn configurado
- [ ] (Produção) SSL configurado

---

## 📖 Documentação Adicional

- [README_DOCKER.md](README_DOCKER.md) - Instalação com Docker
- [TROUBLESHOOTING_RENDER.md](TROUBLESHOOTING_RENDER.md) - Deploy no Render.com
- [MIGRACAO_MYSQL_POSTGRESQL.md](MIGRACAO_MYSQL_POSTGRESQL.md) - Migração MySQL → PostgreSQL

---

**Desenvolvido com ❤️ para facilitar o gerenciamento de listas de presentes de Natal em família!** 🎁🎄
