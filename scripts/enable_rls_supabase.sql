-- ================================================================================
-- Habilitar Row Level Security (RLS) em todas as tabelas Django
-- ================================================================================
--
-- PROBLEMA:
--   Supabase expõe schema 'public' via PostgREST API automaticamente.
--   Sem RLS, qualquer pessoa pode acessar dados sensíveis (senhas, tokens, etc.)
--
-- SOLUÇÃO:
--   Habilitar RLS em todas as tabelas Django para BLOQUEAR acesso via API.
--   Django continua funcionando normalmente (usa conexão PostgreSQL direta).
--
-- COMO EXECUTAR:
--   1. Supabase Dashboard > SQL Editor
--   2. Copiar e colar este script
--   3. Executar (Run)
--   4. Verificar que todos os 27 erros desaparecem no Database Linter
--
-- ================================================================================

-- 1. Habilitar RLS em todas as tabelas Django
ALTER TABLE public.django_migrations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.django_content_type ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.auth_permission ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.auth_group ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.auth_group_permissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.django_admin_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.django_session ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.django_site ENABLE ROW LEVEL SECURITY;

-- 2. Habilitar RLS em tabelas de autenticação (django-allauth)
ALTER TABLE public.account_emailaddress ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.account_emailconfirmation ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.socialaccount_socialaccount ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.socialaccount_socialapp ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.socialaccount_socialapp_sites ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.socialaccount_socialtoken ENABLE ROW LEVEL SECURITY;

-- 3. Habilitar RLS em tabelas do aplicativo (presentes)
ALTER TABLE public.presentes_usuario ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.presentes_usuario_groups ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.presentes_usuario_user_permissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.presentes_grupo ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.presentes_grupomembro ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.presentes_presente ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.presentes_compra ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.presentes_sugestaocompra ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.presentes_notificacao ENABLE ROW LEVEL SECURITY;

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
WHERE schemaname = 'public'
  AND tablename LIKE 'django_%'
   OR tablename LIKE 'auth_%'
   OR tablename LIKE 'presentes_%'
   OR tablename LIKE 'account_%'
   OR tablename LIKE 'socialaccount_%'
ORDER BY tablename;

-- Resultado esperado: todas as linhas com rls_enabled = true

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
