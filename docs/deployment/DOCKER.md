# 🐳 Docker - Desenvolvimento Local

O Docker é uma alternativa para rodar o app localmente. A produção usa o Render com `build.sh` ([RENDER.md](RENDER.md)), não estes arquivos.

## 🚀 Início rápido

```bash
git clone https://github.com/Maxwbh/Lista_de_Presentes.git
cd Lista_de_Presentes

docker compose up --watch          # PostgreSQL + Django em http://localhost:8000
```

Na primeira subida o `entrypoint.sh` cria o schema `lista_presentes`, aplica as migrações e roda o `fix_admin`. Para criar outro admin ou dados de teste:

```bash
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py populate_test_data
```

`--watch` requer Docker Compose 2.22 ou superior.

---

## 📁 Arquivos

| Arquivo | Conteúdo |
|---------|----------|
| `Dockerfile` | `python:3.11-slim`, usuário não-root `app`, `collectstatic` no build, `HEALTHCHECK` em `/health/`, `ENTRYPOINT` `entrypoint.sh` e Gunicorn com `gunicorn.conf.py` |
| `entrypoint.sh` | Aguarda o PostgreSQL (se houver `DATABASE_URL`), roda `scripts/ensure_schema.py`, `migrate`, `fix_admin` e `collectstatic`; com `CREATE_SUPERUSER=true` cria o superusuário de `DJANGO_SUPERUSER_EMAIL`/`_PASSWORD`/`_USERNAME` |
| `docker-compose.yml` | `db` (`postgres:15-alpine`, porta 5432) + `web` (Gunicorn com `--reload`, porta 8000) e `develop.watch` |
| `docker-compose.dev.yml` | Override do serviço `web` para usar `runserver` |
| `docker-compose.sqlite.yml` | Só o `web`, com `Dockerfile.minimal` (Alpine) e `USE_SQLITE=True` (banco no volume `/app/data`); limite de 512 MB |
| `docker-compose.minimal.yml` | PostgreSQL com pouca memória + `Dockerfile.minimal`; limites de 256 MB (db) e 384 MB (web) |

O CSS do Tailwind não é compilado no build da imagem: é usado o `theme/static/css/dist/styles.css` do repositório. Para recompilar, veja [INSTALACAO.md](../development/INSTALACAO.md#-frontend-tailwind-css--daisyui).

### Variantes

```bash
# runserver em vez de Gunicorn (o dev.yml só sobrescreve o serviço web)
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --watch

# Ultra leve, com SQLite
docker compose -f docker-compose.sqlite.yml up --watch

# PostgreSQL com pouca memória
docker compose -f docker-compose.minimal.yml up --watch
```

> ⚠️ O `Dockerfile.minimal` não usa o `entrypoint.sh`, então no `docker-compose.minimal.yml` o schema `lista_presentes` não é criado sozinho e o `migrate` falha num banco novo. Crie o schema uma vez antes:
>
> ```bash
> docker compose -f docker-compose.minimal.yml up -d db
> docker compose -f docker-compose.minimal.yml run --rm web python scripts/ensure_schema.py
> docker compose -f docker-compose.minimal.yml up --watch
> ```

### File watch

No `docker-compose.yml`, o `develop.watch` sincroniza `lista_presentes/`, `presentes/` (exceto `migrations/`), `templates/` e `static/`, e refaz a imagem quando `requirements.txt` ou `Dockerfile` mudam.

### Variáveis de ambiente

O `docker-compose.yml` já define `DEBUG`, `SECRET_KEY` de desenvolvimento, `DATABASE_URL` e `ALLOWED_HOSTS`, e repassa `GEMINI_API_KEY`, `ANTHROPIC_API_KEY` e `OPENAI_API_KEY` do ambiente do host. Outras variáveis ([lista completa](../development/INSTALACAO.md#️-variáveis-de-ambiente)) devem ser adicionadas em `environment:`.

---

## 📦 Comandos úteis

```bash
docker compose up -d                # em segundo plano
docker compose up --watch --build   # forçando rebuild
docker compose logs -f web          # logs
docker compose down                 # parar (down -v apaga os volumes/banco)

docker compose exec web python manage.py migrate
docker compose exec web python manage.py shell
docker compose exec web bash

# PostgreSQL
docker compose exec db psql -U postgres -d lista_presentes   # \dt lista_presentes.*
docker compose exec db pg_dump -U postgres lista_presentes > backup.sql
docker compose exec -T db psql -U postgres lista_presentes < backup.sql
```

---

## 🆘 Solução de problemas

- **Porta 8000 ou 5432 em uso:** pare o processo local ou troque o mapeamento em `ports:` (ex.: `"8001:8000"`).
- **Container não sobe:** `docker compose logs web`; depois `docker compose build --no-cache`.
- **`no schema has been selected to create in`:** o schema `lista_presentes` não existe; rode `docker compose exec web python scripts/ensure_schema.py` (ou veja o aviso do `minimal.yml` acima).
- **Recomeçar do zero:** `docker compose down -v && docker compose up --build` (apaga o banco).
- **Pouco espaço em disco:** `docker system prune` (com `-a --volumes` remove também imagens e volumes; cuidado).

---

## 🔗 Links

- Docker Compose: https://docs.docker.com/compose/
- Compose Watch: https://docs.docker.com/compose/how-tos/file-watch/
