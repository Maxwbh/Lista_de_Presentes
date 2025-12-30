# 🐳 Docker - Guia Completo

Guia completo para usar Docker e Docker Compose com o projeto Lista de Presentes.

## 📋 Pré-requisitos

- Docker Desktop 4.24+ (para suporte ao file watch)
- Docker Compose v2.22+
- 4GB RAM disponível (mínimo)
- 10GB espaço em disco

### Verificar Versões

```bash
docker --version
# Docker version 24.0.0 ou superior

docker compose version
# Docker Compose version v2.22.0 ou superior
```

## 🚀 Quick Start

### 1. Desenvolvimento com Watch (Recomendado)

O modo watch monitora mudanças nos arquivos e recarrega automaticamente:

```bash
# Iniciar com file watch
docker compose up --watch

# Ou usar arquivo de desenvolvimento
docker compose -f docker-compose.dev.yml up --watch
```

**O que o watch faz:**
- ✅ **Sync**: Sincroniza mudanças em Python, templates e static files
- ✅ **Reload**: Recarrega servidor automaticamente
- ✅ **Rebuild**: Reconstrói container se requirements.txt mudar

### 2. Modo Normal (Sem Watch)

```bash
# Build e iniciar
docker compose up --build

# Rodar em background
docker compose up -d

# Ver logs
docker compose logs -f web

# Parar containers
docker compose down
```

## 📦 Comandos Docker Úteis

### Gerenciar Containers

```bash
# Listar containers rodando
docker compose ps

# Parar containers
docker compose stop

# Reiniciar containers
docker compose restart web

# Remover containers e volumes
docker compose down -v

# Rebuild forçado
docker compose build --no-cache
```

### Django Management Commands

```bash
# Executar comandos Django
docker compose exec web python manage.py <comando>

# Criar superusuário
docker compose exec web python manage.py createsuperuser

# Fazer migrações
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate

# Popular dados de teste
docker compose exec web python manage.py populate_test_data

# Shell Django
docker compose exec web python manage.py shell

# Collectstatic
docker compose exec web python manage.py collectstatic --noinput
```

### Banco de Dados

```bash
# Acessar PostgreSQL
docker compose exec db psql -U postgres -d lista_presentes

# Backup do banco
docker compose exec db pg_dump -U postgres lista_presentes > backup.sql

# Restaurar backup
docker compose exec -T db psql -U postgres lista_presentes < backup.sql

# Ver logs do banco
docker compose logs -f db
```

### Logs e Debug

```bash
# Ver logs de todos os serviços
docker compose logs -f

# Ver logs apenas do web
docker compose logs -f web

# Ver logs com timestamp
docker compose logs -f -t

# Últimas 100 linhas
docker compose logs --tail=100 web
```

## 📂 Estrutura de Volumes

```yaml
volumes:
  postgres_data:     # Dados do PostgreSQL
  static_volume:     # Arquivos estáticos coletados
  media_volume:      # Uploads de usuários
```

### Gerenciar Volumes

```bash
# Listar volumes
docker volume ls

# Inspecionar volume
docker volume inspect lista_de_presentes_postgres_data

# Remover volumes não utilizados
docker volume prune

# Remover volume específico (CUIDADO: apaga dados!)
docker volume rm lista_de_presentes_postgres_data
```

## 🔧 Configuração Avançada

### Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
# Django
DEBUG=True
SECRET_KEY=sua-chave-secreta

# Banco de Dados
POSTGRES_DB=lista_presentes
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres_senha_segura

# APIs (opcional)
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...

# Email (opcional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=seu-email@gmail.com
EMAIL_HOST_PASSWORD=sua-senha-app
```

### Docker Compose Override

Crie `docker-compose.override.yml` para customizações locais:

```yaml
version: '3.8'

services:
  web:
    ports:
      - "8080:8000"  # Mudar porta local
    environment:
      - DEBUG=True
      - CUSTOM_SETTING=valor
```

## 🎯 File Watch - Configuração Detalhada

### O que é File Watch?

File watch é um recurso do Docker Compose que monitora mudanças em arquivos e atualiza automaticamente o container.

### Configuração Atual

```yaml
develop:
  watch:
    # Sync - Sincroniza mudanças instantaneamente
    - action: sync
      path: ./presentes
      target: /app/presentes
      ignore:
        - __pycache__/
        - "*.pyc"

    # Rebuild - Reconstrói container
    - action: rebuild
      path: ./requirements.txt
```

### Tipos de Ações

1. **sync**: Sincroniza arquivos (mais rápido)
2. **sync+restart**: Sincroniza e reinicia container
3. **rebuild**: Reconstrói imagem do container

### Usar File Watch

```bash
# Modo watch básico
docker compose up --watch

# Watch com rebuild forçado
docker compose up --watch --build

# Watch em background
docker compose up -d --watch

# Parar watch
Ctrl+C ou docker compose down
```

## 🐛 Troubleshooting

### Container não inicia

```bash
# Ver logs de erro
docker compose logs web

# Verificar saúde do banco
docker compose exec db pg_isready -U postgres

# Reiniciar do zero
docker compose down -v
docker compose up --build
```

### Mudanças não refletem no container

```bash
# Rebuild completo
docker compose down
docker compose build --no-cache
docker compose up --watch

# Verificar volumes
docker compose exec web ls -la /app
```

### Erro de permissão

```bash
# Linux: ajustar permissões
sudo chown -R $USER:$USER .

# Reconstruir
docker compose build --no-cache
```

### Banco de dados não conecta

```bash
# Verificar se PostgreSQL está rodando
docker compose ps db

# Ver logs do banco
docker compose logs db

# Testar conexão
docker compose exec db psql -U postgres -c "SELECT 1"
```

### Container muito lento

```bash
# Limpar recursos não utilizados
docker system prune -a --volumes

# Aumentar recursos do Docker Desktop
# Settings > Resources > aumentar CPU/RAM
```

## 🚀 Deploy em Produção

### Usar arquivo de produção

```bash
# Criar docker-compose.prod.yml
docker compose -f docker-compose.prod.yml up -d
```

### Exemplo docker-compose.prod.yml

```yaml
version: '3.8'

services:
  web:
    build: .
    command: gunicorn --bind 0.0.0.0:8000 --workers 4 lista_presentes.wsgi:application
    environment:
      - DEBUG=False
      - SECRET_KEY=${SECRET_KEY}
      - DATABASE_URL=${DATABASE_URL}
    restart: always

  nginx:
    image: nginx:alpine
    volumes:
      - static_volume:/app/staticfiles
      - ./nginx.conf:/etc/nginx/nginx.conf
    ports:
      - "80:80"
    depends_on:
      - web
```

## 📊 Monitoramento

### Estatísticas de uso

```bash
# Ver uso de recursos
docker stats

# Ver uso por container
docker stats lista_de_presentes_web_1

# Top de processos
docker compose exec web top
```

### Health Checks

```bash
# Verificar saúde dos containers
docker compose ps

# Health check manual
docker compose exec web python manage.py check
```

## 📚 Recursos Adicionais

- [Docker Compose File Watch Docs](https://docs.docker.com/compose/file-watch/)
- [Docker Compose Specification](https://docs.docker.com/compose/compose-file/)
- [Django + Docker Best Practices](https://docs.docker.com/samples/django/)

## 💡 Dicas de Desenvolvimento

### 1. Usar shell interativo

```bash
# Bash no container
docker compose exec web bash

# Python shell
docker compose exec web python manage.py shell

# Django dbshell
docker compose exec web python manage.py dbshell
```

### 2. Instalar pacotes temporariamente

```bash
# Instalar no container em execução
docker compose exec web pip install nome-do-pacote

# Permanente: adicionar em requirements.txt e rebuild
```

### 3. Debug com pdb

Adicione no código:
```python
import pdb; pdb.set_trace()
```

Rode com stdin ativo:
```bash
docker compose run --rm --service-ports web
```

## 🎓 Tutoriais

### Setup Inicial Completo

```bash
# 1. Clone o repositório
git clone https://github.com/Maxwbh/Lista_de_Presentes.git
cd Lista_de_Presentes

# 2. Crie .env
cp .env.example .env

# 3. Build e inicie com watch
docker compose up --watch --build

# 4. Em outro terminal, crie superusuário
docker compose exec web python manage.py createsuperuser

# 5. Popule dados de teste
docker compose exec web python manage.py populate_test_data

# 6. Acesse http://localhost:8000
```

### Workflow de Desenvolvimento

```bash
# 1. Inicie com watch
docker compose up --watch

# 2. Faça mudanças no código
# (Servidor recarrega automaticamente)

# 3. Execute testes
docker compose exec web python manage.py test

# 4. Commit e push
git add .
git commit -m "feat: Nova funcionalidade"
git push
```

---

**Versão**: 1.0.2
**Autor**: Maxwell da Silva Oliveira - M&S do Brasil LTDA
**Atualizado**: 2025-11-29
