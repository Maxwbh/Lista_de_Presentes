# 🐳 Docker para Desenvolvimento - Recursos Mínimos

Guia para rodar o projeto em ambientes com **512MB a 1GB de RAM**.

## 🎯 Visão Geral

Oferecemos 3 configurações otimizadas para diferentes níveis de recursos:

| Configuração | RAM Usada | Arquivo | Banco de Dados |
|--------------|-----------|---------|----------------|
| **Ultra Leve** | ~300-400MB | `docker-compose.sqlite.yml` | SQLite |
| **Leve** | ~500-700MB | `docker-compose.minimal.yml` | PostgreSQL |
| **Padrão** | ~1-2GB | `docker-compose.yml` | PostgreSQL |

## 🚀 Opção 1: Ultra Leve (SQLite)

**Uso de RAM: ~300-400MB**

Ideal para:
- ✅ Computadores antigos
- ✅ Máquinas virtuais com pouca RAM
- ✅ Testes rápidos
- ✅ Desenvolvimento offline

```bash
# Iniciar
docker compose -f docker-compose.sqlite.yml up --watch

# Criar superusuário
docker compose -f docker-compose.sqlite.yml exec web python manage.py createsuperuser

# Acessar http://localhost:8000
```

### Características

- ✅ **Apenas 1 container** (web)
- ✅ **SQLite** ao invés de PostgreSQL
- ✅ **Imagem Alpine** (~150MB vs ~900MB)
- ✅ **Runserver Django** (mais leve que Gunicorn)
- ✅ **File watch** ativo

### ⚠️ Limitações

- ❌ **Não use em produção**
- ❌ SQLite não suporta concorrência pesada
- ❌ Algumas features avançadas do PostgreSQL não funcionam

## 🚀 Opção 2: Leve (PostgreSQL)

**Uso de RAM: ~500-700MB**

Ideal para:
- ✅ Desenvolvimento local com PostgreSQL
- ✅ Testes de funcionalidades específicas do PostgreSQL
- ✅ Ambiente próximo da produção

```bash
# Iniciar
docker compose -f docker-compose.minimal.yml up --watch

# Criar superusuário
docker compose -f docker-compose.minimal.yml exec web python manage.py createsuperuser

# Acessar http://localhost:8000
```

### Características

- ✅ **2 containers** (web + db)
- ✅ **PostgreSQL otimizado** (256MB RAM)
- ✅ **Web otimizado** (384MB RAM)
- ✅ **1 worker** ao invés de 3
- ✅ **File watch** ativo

### Otimizações PostgreSQL

O PostgreSQL está configurado com:

```
shared_buffers=32MB           (padrão: 128MB)
effective_cache_size=64MB     (padrão: 4GB)
work_mem=2MB                  (padrão: 4MB)
maintenance_work_mem=32MB     (padrão: 64MB)
max_worker_processes=2        (padrão: 8)
```

## 📊 Comparação de Recursos

### Antes (Configuração Padrão)

```yaml
web:
  resources:
    memory: 1GB
  workers: 3

db:
  resources:
    memory: 512MB
  shared_buffers: 128MB

TOTAL: ~1.5-2GB RAM
```

### Depois (Configuração Mínima)

```yaml
web:
  resources:
    memory: 384MB
  workers: 1

db:
  resources:
    memory: 256MB
  shared_buffers: 32MB

TOTAL: ~640MB RAM
```

### Ultra Leve (SQLite)

```yaml
web:
  resources:
    memory: 512MB
  workers: 0 (runserver)

TOTAL: ~300-400MB RAM
```

## 🛠️ Comandos Úteis

### Ultra Leve (SQLite)

```bash
# Iniciar
docker compose -f docker-compose.sqlite.yml up --watch

# Parar
docker compose -f docker-compose.sqlite.yml down

# Ver logs
docker compose -f docker-compose.sqlite.yml logs -f web

# Shell Django
docker compose -f docker-compose.sqlite.yml exec web python manage.py shell

# Dados de teste
docker compose -f docker-compose.sqlite.yml exec web python manage.py populate_test_data

# Reset completo
docker compose -f docker-compose.sqlite.yml down -v
```

### Leve (PostgreSQL)

```bash
# Iniciar
docker compose -f docker-compose.minimal.yml up --watch

# Parar
docker compose -f docker-compose.minimal.yml down

# Ver logs
docker compose -f docker-compose.minimal.yml logs -f

# Shell Django
docker compose -f docker-compose.minimal.yml exec web python manage.py shell

# Acessar PostgreSQL
docker compose -f docker-compose.minimal.yml exec db psql -U postgres -d lista_presentes

# Dados de teste
docker compose -f docker-compose.minimal.yml exec web python manage.py populate_test_data

# Reset completo
docker compose -f docker-compose.minimal.yml down -v
```

## 📈 Monitoramento de Recursos

### Ver uso de RAM

```bash
# Todos os containers
docker stats

# Container específico
docker stats lista_presentes_web_minimal

# Ver uso atual
docker compose -f docker-compose.minimal.yml ps
docker system df
```

### Limpar recursos

```bash
# Limpar imagens não utilizadas
docker image prune -a

# Limpar tudo
docker system prune -a --volumes

# Limpar cache de build
docker builder prune
```

## 🔧 Otimizações Aplicadas

### 1. Dockerfile.minimal

- ✅ Baseado em **Alpine Linux** (50MB vs 900MB)
- ✅ Multi-stage build
- ✅ Sem cache de pip
- ✅ Layers otimizadas

### 2. PostgreSQL

- ✅ Configurações de memória mínimas
- ✅ Redução de workers e processos paralelos
- ✅ Limites de memória por container
- ✅ WAL otimizado

### 3. Django/Gunicorn

- ✅ 1 worker ao invés de 3
- ✅ Runserver para dev (mais leve)
- ✅ Debug toolbar desabilitado
- ✅ Log level WARNING

### 4. Docker Compose

- ✅ Limites de memória por serviço
- ✅ Healthchecks otimizados
- ✅ Volumes minimizados

## 🐛 Troubleshooting

### Container mata/reinicia automaticamente

Isso indica falta de memória. Soluções:

```bash
# 1. Use SQLite ao invés de PostgreSQL
docker compose -f docker-compose.sqlite.yml up --watch

# 2. Aumente limite de memória do Docker Desktop
# Settings > Resources > Memory: 2GB ou mais

# 3. Feche outros programas para liberar RAM
```

### SQLite "database is locked"

```bash
# Pare o container
docker compose -f docker-compose.sqlite.yml down

# Remova o volume
docker volume rm lista_de_presentes_sqlite_data

# Reinicie
docker compose -f docker-compose.sqlite.yml up --watch
```

### PostgreSQL muito lento

```bash
# Use SQLite para desenvolvimento
docker compose -f docker-compose.sqlite.yml up --watch

# Ou ajuste configurações no docker-compose.minimal.yml
# Reduza ainda mais:
shared_buffers=16MB
work_mem=1MB
```

### Imagem muito grande

```bash
# Use Dockerfile.minimal ao invés do padrão
# Ele gera imagem de ~150MB vs ~900MB

# Rebuild com minimal
docker compose -f docker-compose.minimal.yml build --no-cache
```

## ⚡ Dicas de Performance

### 1. Desabilitar features opcionais

No `docker-compose.*.yml`, comente:

```yaml
# APIs opcionais (economiza ~50MB RAM)
# - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
# - OPENAI_API_KEY=${OPENAI_API_KEY}
# - GEMINI_API_KEY=${GEMINI_API_KEY}
```

### 2. Reduzir logs

```yaml
environment:
  - DJANGO_LOG_LEVEL=ERROR  # ao invés de WARNING
```

### 3. Usar volumes ao invés de bind mounts

Mais rápido em Windows/Mac:

```yaml
volumes:
  - app_data:/app  # ao invés de .:/app
```

### 4. Limitar concorrência

```bash
# No settings.py
CONN_MAX_AGE = 60  # ao invés de 600
```

## 📚 Documentação Adicional

- [Docker Compose](docker-compose.yml) - Configuração padrão
- [Docker Minimal](docker-compose.minimal.yml) - PostgreSQL otimizado
- [Docker SQLite](docker-compose.sqlite.yml) - Ultra leve
- [Dockerfile Minimal](Dockerfile.minimal) - Imagem Alpine

## 🎓 Tutoriais

### Setup Ultra Rápido (SQLite)

```bash
# 1. Clone
git clone https://github.com/Maxwbh/Lista_de_Presentes.git
cd Lista_de_Presentes

# 2. Inicie
docker compose -f docker-compose.sqlite.yml up --watch

# 3. Crie usuário (em outro terminal)
docker compose -f docker-compose.sqlite.yml exec web python manage.py createsuperuser

# 4. Acesse http://localhost:8000
```

**Tempo total: ~2 minutos**

### Migrar de SQLite para PostgreSQL

```bash
# 1. Backup dos dados
docker compose -f docker-compose.sqlite.yml exec web python manage.py dumpdata > backup.json

# 2. Parar SQLite
docker compose -f docker-compose.sqlite.yml down

# 3. Iniciar PostgreSQL
docker compose -f docker-compose.minimal.yml up -d

# 4. Restaurar dados
docker compose -f docker-compose.minimal.yml exec web python manage.py loaddata backup.json
```

## 🆘 Precisa de Ajuda?

- **Documentação**: [DOCKER.md](DOCKER.md)
- **Issues**: [GitHub Issues](https://github.com/Maxwbh/Lista_de_Presentes/issues)
- **Email**: maxwbh@gmail.com

---

**Versão**: 1.0.2
**Autor**: Maxwell da Silva Oliveira - M&S do Brasil LTDA

**💡 Dica**: Para máximo desempenho com poucos recursos, use SQLite!
