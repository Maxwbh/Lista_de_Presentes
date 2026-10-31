# 🐘 Supabase PostgreSQL

Em produção o app usa PostgreSQL do **Supabase**, num schema próprio (`lista_presentes`), acessado pelo Render via `DATABASE_URL`. Localmente, sem `DATABASE_URL`, usa SQLite ([INSTALACAO.md](../development/INSTALACAO.md#️-banco-de-dados)).

---

## 🔌 Conexão

No Render (**Environment**), defina a URL do **Connection Pooler** do Supabase (Dashboard do Supabase → **Connect**):

```bash
DATABASE_URL=postgresql://postgres.SEU_PROJETO:SENHA_COM_URL_ENCODING@aws-1-us-east-2.pooler.supabase.com:6543/postgres
```

- **Não** adicione `?options=...`: o `settings.py` acrescenta `search_path=lista_presentes` automaticamente.
- Use o pooler (`*.pooler.supabase.com`), não o host direto `db.SEU_PROJETO.supabase.co:5432`, que é só IPv6 e costuma dar `Network is unreachable` no Render.
- Senha com caracteres especiais precisa de URL encoding (`@` → `%40`, `#` → `%23`, `!` → `%21`).
- `SUPABASE_URL` e `SUPABASE_KEY` existem no `settings.py`, mas o Django não as usa hoje.

### O que o `settings.py` configura

| Configuração | Motivo |
|--------------|--------|
| `search_path=lista_presentes` (na URL e em `OPTIONS`) | Tabelas só no schema próprio, nunca em `public` |
| Signal `connection_created` (`presentes/apps.py`) roda `SET search_path TO lista_presentes` | O pooler em modo transação (porta 6543) ignora as opções de conexão |
| `DISABLE_SERVER_SIDE_CURSORS = True` | O modo transação não suporta cursores do lado do servidor (`.iterator()`) |
| `conn_max_age=600`, `conn_health_checks=True` | Reaproveita conexões e descarta as quebradas |
| `connect_timeout=10` e TCP keepalives | Falha rápido e detecta conexões ociosas fechadas pelo pooler |

O pooler tem dois modos: **transação** (porta 6543, usado acima) e **sessão** (porta 5432 no mesmo host do pooler). O comentário do `settings.py` recomenda o modo sessão para conexões persistentes (`conn_max_age`); o signal e o `DISABLE_SERVER_SIDE_CURSORS` mantêm o modo transação funcionando.

---

## 🗂️ Schema isolado `lista_presentes`

Vários apps Django podem dividir o mesmo banco Supabase sem conflito de `django_migrations`, porque cada um usa seu schema:

```
outro_app.django_migrations
lista_presentes.django_migrations   ← este app
```

O search path contém **apenas** `lista_presentes` (sem `public`): se o schema não existir, o PostgreSQL dá erro em vez de criar tabelas no lugar errado. Quem cria o schema:

- `scripts/ensure_schema.py` — rodado pelo `build.sh` (Render) e pelo `entrypoint.sh` (Docker) antes das migrações; idempotente.
- Nos testes, o próprio signal cria o schema no banco de teste.

Para migrar tabelas antigas de `public` para o schema: `scripts/create_isolated_schema.sql`. Detalhes: [SCHEMA_ISOLADO.md](SCHEMA_ISOLADO.md).

---

## 🔐 Row Level Security (RLS)

O Supabase expõe os schemas pela API REST (PostgREST). Com RLS habilitado e **sem políticas**, a API não retorna nenhuma linha, enquanto o Django continua com acesso total (conecta como `postgres`, que ignora RLS).

1. Supabase → **SQL Editor** → execute [`scripts/enable_rls_supabase.sql`](../../scripts/enable_rls_supabase.sql).
2. O script cobre as 23 tabelas originais. As tabelas criadas depois precisam ser incluídas manualmente:

   ```sql
   ALTER TABLE lista_presentes.presentes_precohistorico     ENABLE ROW LEVEL SECURITY;
   ALTER TABLE lista_presentes.presentes_pesquisaprecolog   ENABLE ROW LEVEL SECURITY;
   ALTER TABLE lista_presentes.presentes_pushsubscription   ENABLE ROW LEVEL SECURITY;
   ALTER TABLE lista_presentes.presentes_mercadolivretoken  ENABLE ROW LEVEL SECURITY;
   ALTER TABLE lista_presentes.presentes_despertarservidor  ENABLE ROW LEVEL SECURITY;
   ALTER TABLE lista_presentes.presentes_acessohora         ENABLE ROW LEVEL SECURITY;
   ```

3. Confira (e repita a cada nova tabela, ou use o **Database Linter** do Supabase):

   ```sql
   SELECT tablename, rowsecurity AS rls_enabled
   FROM pg_tables
   WHERE schemaname = 'lista_presentes'
   ORDER BY tablename;
   ```

Se o schema `lista_presentes` não estiver exposto na API (Supabase → Settings → API → Exposed schemas), a API já não o acessa; o RLS continua sendo uma proteção extra.

---

## 🔍 Verificação

```bash
DATABASE_URL="postgresql://..." python scripts/check_database_config.py
```

O script confirma que a `DATABASE_URL` foi lida, que o Django está em PostgreSQL (e não SQLite) e testa a conexão. No deploy, o `build.sh` faz um teste parecido e falha se estiver em SQLite.

---

## 🆘 Solução de problemas

| Erro | Solução |
|------|---------|
| `Network is unreachable` | Use o host do pooler, não `db.SEU_PROJETO.supabase.co` |
| `password authentication failed` | Usuário no formato `postgres.SEU_PROJETO` e senha com URL encoding |
| `no schema has been selected to create in` | Schema ausente: `python scripts/ensure_schema.py` |
| `permission denied for schema/table` | Rode `ensure_schema.py` (concede `GRANT` no schema `lista_presentes` ao `postgres`) |
| `Using SQLite instead of PostgreSQL!` (build) | `DATABASE_URL` não definida no Render |
| `InconsistentMigrationHistory` | O `build.sh` tenta corrigir; se persistir, veja [migrations.md](migrations.md) |
| Erros com `.iterator()` / cursores | Confirme que `DISABLE_SERVER_SIDE_CURSORS` continua no `settings.py` |

---

## 🔗 Links

- Supabase Dashboard: https://supabase.com/dashboard
- Conexão com o banco: https://supabase.com/docs/guides/database/connecting-to-postgres
- RLS no Supabase: https://supabase.com/docs/guides/database/postgres/row-level-security
