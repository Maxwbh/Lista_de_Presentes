-- ================================================================================
-- Schema Isolado - Lista de Presentes
-- ================================================================================
--
-- PROBLEMA:
--   Múltiplas aplicações Django no mesmo banco Supabase compartilham schema 'public'
--   Django encontra tabelas django_migrations, auth_user, etc de outras apps
--   Causa InconsistentMigrationHistory e conflitos de dependências
--
-- SOLUÇÃO:
--   Criar schema isolado 'lista_presentes' com search_path exclusivo
--   Django cria suas próprias tabelas sem interferência de outras apps
--
-- COMO EXECUTAR:
--   1. Supabase Dashboard > SQL Editor
--   2. Copiar e colar este script
--   3. Executar (Run)
--   4. Atualizar DATABASE_URL no Render com ?options=-csearch_path%3Dlista_presentes
--   5. Redeploy da aplicação
--
-- ⚠️ IMPORTANTE:
--   Este script MOVE tabelas existentes de 'public' para 'lista_presentes'
--   Se preferir começar do zero, pule a seção "MIGRAÇÃO DE TABELAS EXISTENTES"
--
-- ================================================================================

-- ================================================================================
-- 1. CRIAR SCHEMA ISOLADO
-- ================================================================================

-- Criar schema lista_presentes
CREATE SCHEMA IF NOT EXISTS lista_presentes;

-- Dar permissões ao role postgres
GRANT ALL ON SCHEMA lista_presentes TO postgres;
GRANT ALL ON ALL TABLES IN SCHEMA lista_presentes TO postgres;
GRANT ALL ON ALL SEQUENCES IN SCHEMA lista_presentes TO postgres;
ALTER DEFAULT PRIVILEGES IN SCHEMA lista_presentes GRANT ALL ON TABLES TO postgres;
ALTER DEFAULT PRIVILEGES IN SCHEMA lista_presentes GRANT ALL ON SEQUENCES TO postgres;

-- ================================================================================
-- 2. MIGRAÇÃO DE TABELAS EXISTENTES (Opcional - se já tem dados)
-- ================================================================================

-- ⚠️ ATENÇÃO: Só execute esta seção se você JÁ TEM TABELAS em 'public'
--             e quer MOVER elas para 'lista_presentes'
--
-- Se você quer começar do zero, pule para a seção 3

-- Tabelas Django Core
DO $$
BEGIN
    -- django_migrations
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'django_migrations') THEN
        ALTER TABLE public.django_migrations SET SCHEMA lista_presentes;
    END IF;

    -- django_content_type
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'django_content_type') THEN
        ALTER TABLE public.django_content_type SET SCHEMA lista_presentes;
    END IF;

    -- django_admin_log
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'django_admin_log') THEN
        ALTER TABLE public.django_admin_log SET SCHEMA lista_presentes;
    END IF;

    -- django_session
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'django_session') THEN
        ALTER TABLE public.django_session SET SCHEMA lista_presentes;
    END IF;

    -- django_site
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'django_site') THEN
        ALTER TABLE public.django_site SET SCHEMA lista_presentes;
    END IF;
END $$;

-- Tabelas Auth
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'auth_permission') THEN
        ALTER TABLE public.auth_permission SET SCHEMA lista_presentes;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'auth_group') THEN
        ALTER TABLE public.auth_group SET SCHEMA lista_presentes;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'auth_group_permissions') THEN
        ALTER TABLE public.auth_group_permissions SET SCHEMA lista_presentes;
    END IF;
END $$;

-- Tabelas Allauth
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'account_emailaddress') THEN
        ALTER TABLE public.account_emailaddress SET SCHEMA lista_presentes;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'account_emailconfirmation') THEN
        ALTER TABLE public.account_emailconfirmation SET SCHEMA lista_presentes;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'socialaccount_socialaccount') THEN
        ALTER TABLE public.socialaccount_socialaccount SET SCHEMA lista_presentes;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'socialaccount_socialapp') THEN
        ALTER TABLE public.socialaccount_socialapp SET SCHEMA lista_presentes;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'socialaccount_socialapp_sites') THEN
        ALTER TABLE public.socialaccount_socialapp_sites SET SCHEMA lista_presentes;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'socialaccount_socialtoken') THEN
        ALTER TABLE public.socialaccount_socialtoken SET SCHEMA lista_presentes;
    END IF;
END $$;

-- Tabelas App Presentes
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'presentes_usuario') THEN
        ALTER TABLE public.presentes_usuario SET SCHEMA lista_presentes;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'presentes_usuario_groups') THEN
        ALTER TABLE public.presentes_usuario_groups SET SCHEMA lista_presentes;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'presentes_usuario_user_permissions') THEN
        ALTER TABLE public.presentes_usuario_user_permissions SET SCHEMA lista_presentes;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'presentes_grupo') THEN
        ALTER TABLE public.presentes_grupo SET SCHEMA lista_presentes;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'presentes_grupomembro') THEN
        ALTER TABLE public.presentes_grupomembro SET SCHEMA lista_presentes;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'presentes_presente') THEN
        ALTER TABLE public.presentes_presente SET SCHEMA lista_presentes;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'presentes_compra') THEN
        ALTER TABLE public.presentes_compra SET SCHEMA lista_presentes;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'presentes_sugestaocompra') THEN
        ALTER TABLE public.presentes_sugestaocompra SET SCHEMA lista_presentes;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'presentes_notificacao') THEN
        ALTER TABLE public.presentes_notificacao SET SCHEMA lista_presentes;
    END IF;
END $$;

-- ================================================================================
-- 3. HABILITAR ROW LEVEL SECURITY (RLS)
-- ================================================================================

-- Habilitar RLS em todas as tabelas no schema lista_presentes

-- Django Core
ALTER TABLE IF EXISTS lista_presentes.django_migrations ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS lista_presentes.django_content_type ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS lista_presentes.django_admin_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS lista_presentes.django_session ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS lista_presentes.django_site ENABLE ROW LEVEL SECURITY;

-- Auth
ALTER TABLE IF EXISTS lista_presentes.auth_permission ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS lista_presentes.auth_group ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS lista_presentes.auth_group_permissions ENABLE ROW LEVEL SECURITY;

-- Allauth
ALTER TABLE IF EXISTS lista_presentes.account_emailaddress ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS lista_presentes.account_emailconfirmation ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS lista_presentes.socialaccount_socialaccount ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS lista_presentes.socialaccount_socialapp ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS lista_presentes.socialaccount_socialapp_sites ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS lista_presentes.socialaccount_socialtoken ENABLE ROW LEVEL SECURITY;

-- App Presentes
ALTER TABLE IF EXISTS lista_presentes.presentes_usuario ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS lista_presentes.presentes_usuario_groups ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS lista_presentes.presentes_usuario_user_permissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS lista_presentes.presentes_grupo ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS lista_presentes.presentes_grupomembro ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS lista_presentes.presentes_presente ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS lista_presentes.presentes_compra ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS lista_presentes.presentes_sugestaocompra ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS lista_presentes.presentes_notificacao ENABLE ROW LEVEL SECURITY;

-- ================================================================================
-- 4. CONFIGURAR PostgREST (Supabase API)
-- ================================================================================

-- Expor schema lista_presentes via API (se necessário)
-- Por padrão, apenas 'public' é exposto
-- Descomente se quiser expor lista_presentes via API:

-- ALTER ROLE authenticator SET pgrst.db_schemas = 'public,lista_presentes';

-- ⚠️ NÃO RECOMENDADO: Como Django não usa a API do Supabase,
--    é melhor NÃO expor o schema lista_presentes

-- ================================================================================
-- 5. VERIFICAÇÃO
-- ================================================================================

-- Verificar tabelas no schema lista_presentes
SELECT
    schemaname,
    tablename,
    rowsecurity AS rls_enabled
FROM pg_tables
WHERE schemaname = 'lista_presentes'
ORDER BY tablename;

-- Resultado esperado:
-- Todas as tabelas Django no schema 'lista_presentes' com RLS habilitado

-- Verificar que public não tem mais tabelas Django (se migrou)
SELECT tablename
FROM pg_tables
WHERE schemaname = 'public'
  AND (
    tablename LIKE 'django_%'
    OR tablename LIKE 'auth_%'
    OR tablename LIKE 'account_%'
    OR tablename LIKE 'socialaccount_%'
    OR tablename LIKE 'presentes_%'
  )
ORDER BY tablename;

-- Resultado esperado:
-- Nenhuma linha (se migrou) ou todas as tabelas (se começou do zero)

-- ================================================================================
-- CONCLUSÃO
-- ================================================================================

/*
✅ Schema 'lista_presentes' criado
✅ Tabelas migradas de 'public' → 'lista_presentes' (se existiam)
✅ RLS habilitado em todas as tabelas
✅ Permissões configuradas para role 'postgres'

PRÓXIMOS PASSOS:

1. Atualizar DATABASE_URL no Render:

   DATABASE_URL=postgresql://postgres.YOUR_PROJECT:YOUR_PASSWORD@aws-1-us-east-2.pooler.supabase.com:6543/postgres?options=-csearch_path%3Dlista_presentes

   Importante: ?options=-csearch_path%3Dlista_presentes
              (URL encoded: search_path=lista_presentes)

2. Atualizar settings.py (local):

   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql',
           'NAME': 'postgres',
           'USER': 'postgres',
           'PASSWORD': '...',
           'HOST': '...',
           'PORT': '6543',
           'OPTIONS': {
               'options': '-c search_path=lista_presentes'
           }
       }
   }

3. Redeploy no Render

4. Verificar logs:
   - Django deve usar schema 'lista_presentes'
   - Migrações devem aplicar sem conflitos
   - Nenhum InconsistentMigrationHistory

BENEFÍCIOS:

✅ Isolamento total de outras apps Django
✅ Sem conflitos de django_migrations
✅ Sem conflitos de auth_user
✅ Múltiplas apps Django no mesmo Supabase
✅ RLS protege todas as tabelas
*/
