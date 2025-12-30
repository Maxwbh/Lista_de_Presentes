# 🐳 Docker Quick Start

Guia rápido para rodar o projeto com Docker.

## 🚀 Início Rápido (3 minutos)

```bash
# 1. Clone o repositório
git clone https://github.com/Maxwbh/Lista_de_Presentes.git
cd Lista_de_Presentes

# 2. Inicie com file watch (recomendado para desenvolvimento)
docker compose up --watch

# 3. Em outro terminal, crie um superusuário
docker compose exec web python manage.py createsuperuser

# 4. Acesse http://localhost:8000
```

Pronto! 🎉

## 📦 Comandos Principais

### Desenvolvimento com Watch

```bash
# Iniciar com auto-reload
docker compose up --watch

# Com rebuild forçado
docker compose up --watch --build

# Modo desenvolvimento (usa runserver Django)
docker compose -f docker-compose.dev.yml up --watch
```

### Comandos Básicos

```bash
# Parar containers
docker compose down

# Ver logs
docker compose logs -f web

# Executar comando Django
docker compose exec web python manage.py <comando>

# Acessar shell do container
docker compose exec web bash

# Resetar tudo (CUIDADO: apaga dados!)
docker compose down -v
```

## 🔧 Comandos Django no Docker

```bash
# Criar superusuário
docker compose exec web python manage.py createsuperuser

# Migrações
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate

# Dados de teste
docker compose exec web python manage.py populate_test_data

# Shell
docker compose exec web python manage.py shell

# Testes
docker compose exec web python manage.py test
```

## 📂 Arquivos de Configuração

### Arquivos Docker Compose

- **docker-compose.yml** - Configuração principal (produção/desenvolvimento)
- **docker-compose.dev.yml** - Configuração otimizada para desenvolvimento
- **docker-compose.override.yml** - Suas customizações locais (gitignored)

### Usar arquivo específico

```bash
# Desenvolvimento
docker compose -f docker-compose.dev.yml up --watch

# Produção
docker compose -f docker-compose.prod.yml up -d

# Múltiplos arquivos
docker compose -f docker-compose.yml -f docker-compose.override.yml up
```

## 🎯 File Watch Configurado

O projeto está configurado com **Docker Compose File Watch** que monitora:

### Sync (Sincronização Instantânea)
- ✅ Código Python (`lista_presentes/`, `presentes/`)
- ✅ Templates HTML (`templates/`)
- ✅ Arquivos estáticos (`static/`)

### Rebuild (Reconstrói Container)
- 🔄 `requirements.txt`
- 🔄 `Dockerfile`

### Como Funciona

Quando você edita um arquivo Python, template ou CSS:
1. **File watch detecta a mudança**
2. **Sincroniza o arquivo no container**
3. **Gunicorn (--reload) reinicia automaticamente**
4. **Mudança visível no browser** (refresh manual)

## 🐛 Problemas Comuns

### Container não inicia

```bash
# Ver logs de erro
docker compose logs web

# Rebuild completo
docker compose down
docker compose build --no-cache
docker compose up --watch
```

### Mudanças não aparecem

```bash
# Verificar se watch está ativo
# Deve aparecer: "Watch enabled"

# Forçar rebuild
docker compose up --watch --build
```

### Erro de permissão (Linux)

```bash
sudo chown -R $USER:$USER .
docker compose down
docker compose up --watch
```

### Porta 8000 já em uso

```bash
# Parar container usando a porta
docker compose down

# Ou mudar porta em docker-compose.yml
ports:
  - "8080:8000"  # Usar porta 8080 localmente
```

## 📊 Monitoramento

```bash
# Ver uso de recursos
docker stats

# Listar containers
docker compose ps

# Health check
docker compose exec db pg_isready -U postgres
```

## 💾 Backup e Restauração

### Backup do Banco

```bash
# Criar backup
docker compose exec db pg_dump -U postgres lista_presentes > backup.sql

# Restaurar backup
docker compose exec -T db psql -U postgres lista_presentes < backup.sql
```

### Backup de Volumes

```bash
# Backup de uploads/media
docker compose exec web tar czf /tmp/media.tar.gz /app/media
docker compose cp web:/tmp/media.tar.gz ./backup-media.tar.gz
```

## 🚀 Deploy em Produção

Para produção, use:

```bash
# Build otimizado
docker compose -f docker-compose.prod.yml build

# Iniciar em background
docker compose -f docker-compose.prod.yml up -d

# Ver logs
docker compose -f docker-compose.prod.yml logs -f
```

## 📚 Documentação Completa

- [Guia Docker Completo](docs/deployment/docker.md)
- [Docker Compose File Watch](https://docs.docker.com/compose/file-watch/)
- [README Principal](README.md)

## 🆘 Precisa de Ajuda?

- **Issues**: [GitHub Issues](https://github.com/Maxwbh/Lista_de_Presentes/issues)
- **Email**: maxwbh@gmail.com
- **LinkedIn**: [Maxwell da Silva Oliveira](https://www.linkedin.com/in/maxwbh/)

---

**Versão**: 1.0.2
**Autor**: Maxwell da Silva Oliveira - M&S do Brasil LTDA

**⭐ Dica**: Use `docker compose up --watch` para desenvolvimento com hot-reload automático!
