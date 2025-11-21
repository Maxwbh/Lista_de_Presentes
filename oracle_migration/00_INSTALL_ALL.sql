-- ==============================================================================
-- SCRIPT DE INSTALACAO COMPLETA - LISTA DE PRESENTES
-- Oracle 26 / Apex 24
-- Data: 2025-11-21
-- Desenvolvedor: Maxwell da Silva Oliveira (@maxwbh)
-- Email: maxwbh@gmail.com
-- Empresa: M&S do Brasil LTDA - msbrasil.inf.br
-- ==============================================================================
--
-- IMPORTANTE: Execute este script como usuario com privilegios adequados
--
-- Este script executa todos os scripts de criacao na ordem correta:
-- 1. DDL (Tabelas, Indices, Views, Sequences)
-- 2. Packages (Usuario, Notificacao, Presente, Sugestao, Compra, Push)
-- 3. Integracao Push Notifications com APEX
--
-- ==============================================================================

SET SERVEROUTPUT ON
SET VERIFY OFF
SET ECHO ON
SET FEEDBACK ON

PROMPT ========================================
PROMPT INSTALACAO SISTEMA LISTA DE PRESENTES
PROMPT Oracle 26 / Apex 24
PROMPT ========================================
PROMPT
PROMPT Iniciando instalacao...
PROMPT

-- ==============================================================================
-- PASSO 1: CRIAR ESTRUTURA DE DADOS (DDL)
-- ==============================================================================

PROMPT ========================================
PROMPT PASSO 1/8: Criando Tabelas, Indices e Views
PROMPT ========================================

@@01_DDL_TABELAS.sql

PROMPT
PROMPT ✓ Estrutura de dados criada com sucesso!
PROMPT

-- ==============================================================================
-- PASSO 2: CRIAR PACKAGE PKG_USUARIO
-- ==============================================================================

PROMPT ========================================
PROMPT PASSO 2/8: Criando Package PKG_USUARIO
PROMPT ========================================

@@02_PKG_USUARIO.sql

PROMPT
PROMPT ✓ Package PKG_USUARIO criado com sucesso!
PROMPT

-- ==============================================================================
-- PASSO 3: CRIAR PACKAGE PKG_NOTIFICACAO
-- ==============================================================================

PROMPT ========================================
PROMPT PASSO 3/8: Criando Package PKG_NOTIFICACAO
PROMPT ========================================

@@05_PKG_NOTIFICACAO.sql

PROMPT
PROMPT ✓ Package PKG_NOTIFICACAO criado com sucesso!
PROMPT

-- ==============================================================================
-- PASSO 4: CRIAR PACKAGE PKG_PRESENTE
-- ==============================================================================

PROMPT ========================================
PROMPT PASSO 4/8: Criando Package PKG_PRESENTE
PROMPT ========================================

@@03_PKG_PRESENTE.sql

PROMPT
PROMPT ✓ Package PKG_PRESENTE criado com sucesso!
PROMPT

-- ==============================================================================
-- PASSO 5: CRIAR PACKAGE PKG_SUGESTAO
-- ==============================================================================

PROMPT ========================================
PROMPT PASSO 5/8: Criando Package PKG_SUGESTAO
PROMPT ========================================

@@06_PKG_SUGESTAO.sql

PROMPT
PROMPT ✓ Package PKG_SUGESTAO criado com sucesso!
PROMPT

-- ==============================================================================
-- PASSO 6: CRIAR PACKAGE PKG_COMPRA
-- ==============================================================================

PROMPT ========================================
PROMPT PASSO 6/8: Criando Package PKG_COMPRA
PROMPT ========================================

@@04_PKG_COMPRA.sql

PROMPT
PROMPT ✓ Package PKG_COMPRA criado com sucesso!
PROMPT

-- ==============================================================================
-- PASSO 7: CRIAR PACKAGE PKG_PUSH_NOTIFICATION
-- ==============================================================================

PROMPT ========================================
PROMPT PASSO 7/8: Criando Package PKG_PUSH_NOTIFICATION
PROMPT ========================================

@@07_PKG_PUSH_NOTIFICATION.sql

PROMPT
PROMPT ✓ Package PKG_PUSH_NOTIFICATION criado com sucesso!
PROMPT

-- ==============================================================================
-- PASSO 8: CRIAR INTEGRACAO PUSH COM APEX
-- ==============================================================================

PROMPT ========================================
PROMPT PASSO 8/8: Criando Integracao Push Notifications
PROMPT ========================================

@@08_INTEGRACAO_PUSH_APEX.sql

PROMPT
PROMPT ✓ Integracao Push Notifications criada com sucesso!
PROMPT

-- ==============================================================================
-- VERIFICACAO FINAL
-- ==============================================================================

PROMPT
PROMPT ========================================
PROMPT VERIFICACAO DA INSTALACAO
PROMPT ========================================
PROMPT

-- Verificar tabelas criadas
PROMPT Tabelas criadas:
SELECT table_name
FROM user_tables
WHERE table_name LIKE 'TB_%'
ORDER BY table_name;

PROMPT
PROMPT Sequences criadas:
SELECT sequence_name
FROM user_sequences
WHERE sequence_name LIKE 'SEQ_%'
ORDER BY sequence_name;

PROMPT
PROMPT Views criadas:
SELECT view_name
FROM user_views
WHERE view_name LIKE 'VW_%'
ORDER BY view_name;

PROMPT
PROMPT Packages criados:
SELECT object_name, object_type, status
FROM user_objects
WHERE object_type IN ('PACKAGE', 'PACKAGE BODY')
  AND object_name LIKE 'PKG_%'
ORDER BY object_name, object_type;

PROMPT
PROMPT ========================================
PROMPT STATUS DA COMPILACAO
PROMPT ========================================
PROMPT

-- Verificar objetos invalidos
PROMPT Objetos invalidos (nao deve haver nenhum):
SELECT object_type, object_name, status
FROM user_objects
WHERE status != 'VALID'
  AND (object_name LIKE 'TB_%'
   OR object_name LIKE 'PKG_%'
   OR object_name LIKE 'VW_%')
ORDER BY object_type, object_name;

PROMPT
PROMPT ========================================
PROMPT INSTALACAO CONCLUIDA!
PROMPT ========================================
PROMPT
PROMPT Sistema Lista de Presentes instalado com sucesso!
PROMPT
PROMPT Proximos passos:
PROMPT 1. Criar usuario administrador com PKG_USUARIO.REGISTRAR_USUARIO
PROMPT 2. Configurar Oracle APEX (importar aplicacao ou criar do zero)
PROMPT 3. Testar funcionalidades basicas
PROMPT
PROMPT Para criar usuario admin, execute:
PROMPT
PROMPT DECLARE
PROMPT     v_id NUMBER;
PROMPT BEGIN
PROMPT     v_id := PKG_USUARIO.REGISTRAR_USUARIO(
PROMPT         p_username => 'admin',
PROMPT         p_email => 'admin@listapresentes.com',
PROMPT         p_senha => 'Admin@123',
PROMPT         p_primeiro_nome => 'Administrador',
PROMPT         p_ultimo_nome => 'Sistema'
PROMPT     );
PROMPT
PROMPT     UPDATE TB_USUARIO
PROMPT     SET IS_SUPERUSER = 'S', IS_STAFF = 'S'
PROMPT     WHERE ID_USUARIO = v_id;
PROMPT
PROMPT     COMMIT;
PROMPT
PROMPT     DBMS_OUTPUT.PUT_LINE('Admin criado com ID: ' || v_id);
PROMPT END;
PROMPT /
PROMPT
PROMPT ========================================
