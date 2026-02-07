# Docker - Desenvolvimento Local

## 🚀 Quick Start (3 minutos)

```bash
# 1. Clone o repositório
git clone https://github.com/Maxwbh/Lista_de_Presentes.git
cd Lista_de_Presentes

# 2. Inicie com file watch (auto-reload)
docker compose up --watch

# 3. Em outro terminal, crie um superusuário
docker compose exec web python manage.py createsuperuser

# 4. Acesse http://localhost:8000
```

Pronto! 🎉

---

## 📦 Comandos Principais

### Desenvolvimento

```bash
# Iniciar com auto-reload
docker compose up --watch

# Com rebuild forçado
docker compose up --watch --build

# Modo background
docker compose up -d

# Parar containers
docker compose down

# Ver logs em tempo real
docker compose logs -f web
```

### Django no Docker

```bash
# Criar superusuário
docker compose exec web python manage.py createsuperuser

# Aplicar migrações
docker compose exec web python manage.py migrate

# Criar migrações
docker compose exec web python manage.py makemigrations

# Coletar static files
docker compose exec web python manage.py collectstatic

# Shell Django
docker compose exec web python manage.py shell

# Shell do container
docker compose exec web bash
```

---

## 🔧 Configuração

### docker-compose.yml

```yaml
services:
  db:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=lista_presentes
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres

  web:
    build: .
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - .:/code
    ports:
      - "8000:8000"
    depends_on:
      - db
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/lista_presentes
      - DEBUG=True
```

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /code

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Coletar static files
RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "--config", "gunicorn.conf.py", "lista_presentes.wsgi:application"]
```

---

## 🐘 PostgreSQL

### Acessar Database

```bash
# Conectar ao PostgreSQL
docker compose exec db psql -U postgres -d lista_presentes

# Comandos úteis no psql
\dt          # Listar tabelas
\d+ tabela   # Descrever tabela
\q           # Sair
```

### Backup e Restore

```bash
# Backup
docker compose exec db pg_dump -U postgres lista_presentes > backup.sql

# Restore
docker compose exec -T db psql -U postgres lista_presentes < backup.sql
```

---

## 🧪 Desenvolvimento

### File Watch (Auto-reload)

Docker Compose 2.22+ suporta `--watch`:

```yaml
# docker-compose.yml
services:
  web:
    develop:
      watch:
        - action: sync
          path: .
          target: /code
          ignore:
            - .git/
            - __pycache__/
```

**Uso:**
```bash
docker compose up --watch  # Sincroniza mudanças automaticamente
```

### Variáveis de Ambiente

```bash
# Criar .env na raiz do projeto
cat > .env <<EOF
DEBUG=True
SECRET_KEY=dev-secret-key-change-in-production
DATABASE_URL=postgresql://postgres:postgres@db:5432/lista_presentes
ALLOWED_HOSTS=localhost,127.0.0.1
EOF
```

---

## 🆘 Troubleshooting

### Porta 8000 Já em Uso

```bash
# Verificar processo usando porta 8000
lsof -i :8000

# Parar processo
kill -9 <PID>

# Ou mudar porta no docker-compose.yml
ports:
  - "8001:8000"  # Acesse via localhost:8001
```

### Container Não Inicia

```bash
# Ver logs detalhados
docker compose logs web

# Rebuild sem cache
docker compose build --no-cache

# Limpar volumes
docker compose down -v
docker compose up --build
```

### Migrações Não Aplicam

```bash
# Aplicar manualmente
docker compose exec web python manage.py migrate

# Verificar status
docker compose exec web python manage.py showmigrations

# Resetar database (CUIDADO!)
docker compose down -v
docker compose up -d db
docker compose exec web python manage.py migrate
```

### Out of Disk Space

```bash
# Limpar containers parados
docker container prune

# Limpar imagens não usadas
docker image prune -a

# Limpar volumes não usados
docker volume prune

# Limpar tudo (CUIDADO!)
docker system prune -a --volumes
```

---

## 🔒 Produção

### Docker para Produção (NÃO RECOMENDADO)

**Recomendação:** Use Render.com com `build.sh` (mais simples e gratuito).

Se precisar usar Docker em produção:

```dockerfile
# Dockerfile.prod
FROM python:3.11-slim

WORKDIR /code

# Instalar dependências
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Criar usuário não-root
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /code
USER appuser

# Coletar static files
RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "--config", "gunicorn.conf.py", "lista_presentes.wsgi:application"]
```

**docker-compose.prod.yml:**
```yaml
services:
  web:
    build:
      context: .
      dockerfile: Dockerfile.prod
    environment:
      - DEBUG=False
      - DJANGO_SETTINGS_MODULE=lista_presentes.settings
      - DATABASE_URL=${DATABASE_URL}
      - SECRET_KEY=${SECRET_KEY}
    ports:
      - "8000:8000"
```

---

## 📊 Multi-Stage Build (Otimizado)

```dockerfile
# Dockerfile.multistage
FROM python:3.11-slim as builder

WORKDIR /code

# Instalar dependências de build
RUN apt-get update && apt-get install -y gcc postgresql-client

COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /code/wheels -r requirements.txt

# Stage final
FROM python:3.11-slim

WORKDIR /code

# Instalar apenas runtime
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copiar wheels do builder
COPY --from=builder /code/wheels /wheels
COPY --from=builder /code/requirements.txt .

RUN pip install --no-cache /wheels/*

COPY . .

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "--config", "gunicorn.conf.py", "lista_presentes.wsgi:application"]
```

**Reduz tamanho da imagem em ~30-40%**

---

## 🔗 Links Úteis

- **Docker Compose Docs**: https://docs.docker.com/compose/
- **Docker Compose Watch**: https://docs.docker.com/compose/file-watch/
- **Dockerfile Best Practices**: https://docs.docker.com/develop/dev-best-practices/
- **Django Docker Guide**: https://docs.docker.com/samples/django/

---

**Última atualização:** 2026-02-07
**Versão:** 1.1.31
**Recomendação:** Use Render.com para produção (gratuito, mais simples)
