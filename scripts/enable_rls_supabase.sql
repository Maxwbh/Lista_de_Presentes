-- ================================================================================
-- Habilitar Row Level Security (RLS) em todas as tabelas Django
-- ================================================================================
--
-- ⚠️ ATENÇÃO:
--   Este script é para SCHEMA ISOLADO 'lista_presentes'
--   Se você ainda está usando 'public', execute primeiro: create_isolated_schema.sql
--
-- PROBLEMA:
--   Supabase expõe schemas via PostgREST API automaticamente.
--   Sem RLS, qualquer pessoa pode acessar dados sensíveis (senhas, tokens, etc.)
--
-- SOLUÇÃO:
--   Habilitar RLS em todas as tabelas Django no schema 'lista_presentes'
--   Django continua funcionando normalmente (usa conexão PostgreSQL direta).
--
-- COMO EXECUTAR:
--   1. Supabase Dashboard > SQL Editor
--   2. Copiar e colar este script
--   3. Executar (Run)
--   4. Verificar que todos os erros desaparecem no Database Linter
--
-- ================================================================================

-- 1. Habilitar RLS em todas as tabelas Django
ALTER TABLE lista_presentes.django_migrations ENABLE ROW LEVEL SECURITY;
ALTER TABLE lista_presentes.django_content_type ENABLE ROW LEVEL SECURITY;
ALTER TABLE lista_presentes.auth_permission ENABLE ROW LEVEL SECURITY;
ALTER TABLE lista_presentes.auth_group ENABLE ROW LEVEL SECURITY;
ALTER TABLE lista_presentes.auth_group_permissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE lista_presentes.django_admin_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE lista_presentes.django_session ENABLE ROW LEVEL SECURITY;
ALTER TABLE lista_presentes.django_site ENABLE ROW LEVEL SECURITY;

-- 2. Habilitar RLS em tabelas de autenticação (django-allauth)
ALTER TABLE lista_presentes.account_emailaddress ENABLE ROW LEVEL SECURITY;
ALTER TABLE lista_presentes.account_emailconfirmation ENABLE ROW LEVEL SECURITY;
ALTER TABLE lista_presentes.socialaccount_socialaccount ENABLE ROW LEVEL SECURITY;
ALTER TABLE lista_presentes.socialaccount_socialapp ENABLE ROW LEVEL SECURITY;
ALTER TABLE lista_presentes.socialaccount_socialapp_sites ENABLE ROW LEVEL SECURITY;
ALTER TABLE lista_presentes.socialaccount_socialtoken ENABLE ROW LEVEL SECURITY;

-- 3. Habilitar RLS em tabelas do aplicativo (presentes)
ALTER TABLE lista_presentes.presentes_usuario ENABLE ROW LEVEL SECURITY;
ALTER TABLE lista_presentes.presentes_usuario_groups ENABLE ROW LEVEL SECURITY;
ALTER TABLE lista_presentes.presentes_usuario_user_permissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE lista_presentes.presentes_grupo ENABLE ROW LEVEL SECURITY;
ALTER TABLE lista_presentes.presentes_grupomembro ENABLE ROW LEVEL SECURITY;
ALTER TABLE lista_presentes.presentes_presente ENABLE ROW LEVEL SECURITY;
ALTER TABLE lista_presentes.presentes_compra ENABLE ROW LEVEL SECURITY;
ALTER TABLE lista_presentes.presentes_sugestaocompra ENABLE ROW LEVEL SECURITY;
ALTER TABLE lista_presentes.presentes_notificacao ENABLE ROW LEVEL SECURITY;

-- ================================================================================
-- IMPORTANTE: Políticas RLS
-- ================================================================================
--
-- Com RLS habilitado mas SEM políticas, o comportamento é:
--   ✅ Django funciona normalmente (usa role 'postgres' com BYPASSRLS)
--   ❌ API PostgREST bloqueada (retorna 0 rows para tudo)
--
-- Isso é EXATAMENTE o que queremos para um Django app!
--
-- Se no futuro você quiser usar a Supabase API, adicione políticas:
--
-- Exemplo (NÃO executar agora):
-- CREATE POLICY "Allow authenticated users to read their own data"
--   ON public.presentes_presente
--   FOR SELECT
--   USING (auth.uid() = usuario_id);
--
-- ================================================================================

-- 4. Verificar que RLS está habilitado
SELECT
    schemaname,
    tablename,
    rowsecurity AS rls_enabled
FROM pg_tables
WHERE schemaname = 'lista_presentes'
  AND (
    tablename LIKE 'django_%'
    OR tablename LIKE 'auth_%'
    OR tablename LIKE 'presentes_%'
    OR tablename LIKE 'account_%'
    OR tablename LIKE 'socialaccount_%'
  )
ORDER BY tablename;

-- Resultado esperado: todas as linhas com rls_enabled = true e schemaname = 'lista_presentes'

-- ================================================================================
-- BONUS: Desabilitar PostgREST API completamente (opcional)
-- ================================================================================
--
-- Se você NÃO usa a API do Supabase e quer desabilitá-la completamente:
--
-- 1. Supabase Dashboard > Settings > API
-- 2. Disable API (PostgREST)
--
-- Isso desabilita completamente a API REST, tornando RLS desnecessário.
-- Recomendado apenas se você tem certeza que não usa a API.
--
-- ================================================================================
