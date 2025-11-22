-- ==============================================================================
-- APLICACAO ORACLE APEX - LISTA DE PRESENTES
-- Oracle APEX 24 / Oracle 26
-- Data: 2025-11-21
-- Desenvolvedor: Maxwell da Silva Oliveira (@maxwbh)
-- Email: maxwbh@gmail.com
-- Empresa: M&S do Brasil LTDA - msbrasil.inf.br
-- ==============================================================================
--
-- Este script cria a estrutura basica da aplicacao APEX
-- Execute apos instalar todos os objetos de banco (00_INSTALL_ALL.sql)
--
-- ==============================================================================

SET SERVEROUTPUT ON
SET DEFINE OFF

PROMPT ========================================
PROMPT CRIANDO APLICACAO APEX - LISTA DE PRESENTES
PROMPT ========================================

-- ==============================================================================
-- PARTE 1: FUNCAO DE AUTENTICACAO CUSTOMIZADA
-- ==============================================================================

CREATE OR REPLACE FUNCTION FN_APEX_AUTENTICAR(
    p_username IN VARCHAR2,
    p_password IN VARCHAR2
) RETURN BOOLEAN IS
    v_id_usuario NUMBER;
BEGIN
    -- Usar package de autenticacao
    v_id_usuario := PKG_USUARIO.AUTENTICAR_USUARIO(
        p_email => p_username,
        p_senha => p_password
    );

    -- Se chegou aqui, autenticacao OK
    RETURN TRUE;
EXCEPTION
    WHEN OTHERS THEN
        RETURN FALSE;
END FN_APEX_AUTENTICAR;
/

COMMENT ON FUNCTION FN_APEX_AUTENTICAR IS 'Funcao de autenticacao customizada para APEX';


-- ==============================================================================
-- PARTE 2: FUNCAO PARA OBTER ID DO USUARIO LOGADO
-- ==============================================================================

CREATE OR REPLACE FUNCTION FN_APEX_GET_USER_ID RETURN NUMBER IS
    v_email     VARCHAR2(255);
    v_usuario   PKG_USUARIO.t_usuario;
BEGIN
    -- Obter email do usuario logado no APEX
    v_email := APEX_UTIL.GET_SESSION_EMAIL;

    IF v_email IS NULL THEN
        v_email := V('APP_USER');
    END IF;

    -- Buscar ID do usuario
    v_usuario := PKG_USUARIO.BUSCAR_POR_EMAIL(v_email);

    RETURN v_usuario.id_usuario;
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END FN_APEX_GET_USER_ID;
/

COMMENT ON FUNCTION FN_APEX_GET_USER_ID IS 'Retorna ID do usuario logado no APEX';


-- ==============================================================================
-- PARTE 3: FUNCAO PARA VERIFICAR SE USUARIO E ADMIN
-- ==============================================================================

CREATE OR REPLACE FUNCTION FN_APEX_IS_ADMIN RETURN VARCHAR2 IS
    v_id_usuario NUMBER;
BEGIN
    v_id_usuario := FN_APEX_GET_USER_ID;

    IF v_id_usuario IS NULL THEN
        RETURN 'N';
    END IF;

    IF PKG_USUARIO.IS_SUPERUSER(v_id_usuario) THEN
        RETURN 'S';
    ELSE
        RETURN 'N';
    END IF;
END FN_APEX_IS_ADMIN;
/

COMMENT ON FUNCTION FN_APEX_IS_ADMIN IS 'Verifica se usuario logado e administrador';


-- ==============================================================================
-- PARTE 4: PROCEDURE PARA PROCESSAR ACOES DO APEX
-- ==============================================================================

-- Procedure para adicionar presente via APEX
CREATE OR REPLACE PROCEDURE PRC_APEX_ADICIONAR_PRESENTE(
    p_descricao     IN CLOB,
    p_url           IN VARCHAR2 DEFAULT NULL,
    p_preco         IN NUMBER DEFAULT NULL,
    p_imagem_base64 IN CLOB DEFAULT NULL,
    p_imagem_nome   IN VARCHAR2 DEFAULT NULL,
    p_imagem_tipo   IN VARCHAR2 DEFAULT NULL,
    p_id_presente   OUT NUMBER
) IS
    v_id_usuario NUMBER;
BEGIN
    v_id_usuario := FN_APEX_GET_USER_ID;

    IF v_id_usuario IS NULL THEN
        RAISE_APPLICATION_ERROR(-20900, 'Usuario nao autenticado');
    END IF;

    p_id_presente := PKG_PRESENTE.ADICIONAR_PRESENTE(
        p_id_usuario    => v_id_usuario,
        p_descricao     => p_descricao,
        p_url           => p_url,
        p_preco         => p_preco,
        p_imagem_base64 => p_imagem_base64,
        p_imagem_nome   => p_imagem_nome,
        p_imagem_tipo   => p_imagem_tipo
    );
END PRC_APEX_ADICIONAR_PRESENTE;
/

-- Procedure para marcar presente como comprado via APEX
CREATE OR REPLACE PROCEDURE PRC_APEX_COMPRAR_PRESENTE(
    p_id_presente   IN NUMBER,
    p_id_compra     OUT NUMBER
) IS
    v_id_usuario NUMBER;
BEGIN
    v_id_usuario := FN_APEX_GET_USER_ID;

    IF v_id_usuario IS NULL THEN
        RAISE_APPLICATION_ERROR(-20900, 'Usuario nao autenticado');
    END IF;

    p_id_compra := PKG_COMPRA.MARCAR_COMPRADO(
        p_id_presente   => p_id_presente,
        p_id_comprador  => v_id_usuario
    );
END PRC_APEX_COMPRAR_PRESENTE;
/

-- Procedure para registrar novo usuario via APEX
CREATE OR REPLACE PROCEDURE PRC_APEX_REGISTRAR_USUARIO(
    p_username      IN VARCHAR2,
    p_email         IN VARCHAR2,
    p_senha         IN VARCHAR2,
    p_primeiro_nome IN VARCHAR2,
    p_ultimo_nome   IN VARCHAR2,
    p_telefone      IN VARCHAR2 DEFAULT NULL,
    p_id_usuario    OUT NUMBER
) IS
BEGIN
    p_id_usuario := PKG_USUARIO.REGISTRAR_USUARIO(
        p_username      => p_username,
        p_email         => p_email,
        p_senha         => p_senha,
        p_primeiro_nome => p_primeiro_nome,
        p_ultimo_nome   => p_ultimo_nome,
        p_telefone      => p_telefone
    );
END PRC_APEX_REGISTRAR_USUARIO;
/


-- ==============================================================================
-- PARTE 5: VIEWS PARA APEX
-- ==============================================================================

-- View para listagem de presentes do usuario logado
CREATE OR REPLACE VIEW VW_APEX_MEUS_PRESENTES AS
SELECT
    p.ID,
    p.DESCRICAO,
    p.URL,
    p.PRECO,
    p.STATUS,
    p.DATA_CADASTRO,
    p.ID_USUARIO,
    CASE WHEN p.IMAGEM_BASE64 IS NOT NULL THEN 'S' ELSE 'N' END AS TEM_IMAGEM,
    p.IMAGEM_NOME,
    p.IMAGEM_TIPO,
    (SELECT COUNT(*) FROM LCP_SUGESTAO_COMPRA s WHERE s.ID_PRESENTE = p.ID) AS TOTAL_SUGESTOES,
    (SELECT MIN(PRECO_SUGERIDO) FROM LCP_SUGESTAO_COMPRA s WHERE s.ID_PRESENTE = p.ID AND PRECO_SUGERIDO IS NOT NULL) AS MELHOR_PRECO,
    c.DATA_COMPRA,
    comp.PRIMEIRO_NOME || ' ' || comp.ULTIMO_NOME AS COMPRADOR_NOME
FROM LCP_PRESENTE p
LEFT JOIN LCP_COMPRA c ON p.ID = c.ID_PRESENTE
LEFT JOIN LCP_USUARIO comp ON c.ID_COMPRADOR = comp.ID;

COMMENT ON VIEW VW_APEX_MEUS_PRESENTES IS 'View para listagem de presentes no APEX';

-- View para listagem de presentes de outros usuarios
CREATE OR REPLACE VIEW VW_APEX_PRESENTES_OUTROS AS
SELECT
    p.ID,
    p.DESCRICAO,
    p.URL,
    p.PRECO,
    p.STATUS,
    p.DATA_CADASTRO,
    p.ID_USUARIO,
    u.PRIMEIRO_NOME || ' ' || u.ULTIMO_NOME AS NOME_DONO,
    u.EMAIL AS EMAIL_DONO,
    CASE WHEN p.IMAGEM_BASE64 IS NOT NULL THEN 'S' ELSE 'N' END AS TEM_IMAGEM,
    (SELECT COUNT(*) FROM LCP_SUGESTAO_COMPRA s WHERE s.ID_PRESENTE = p.ID) AS TOTAL_SUGESTOES,
    (SELECT MIN(PRECO_SUGERIDO) FROM LCP_SUGESTAO_COMPRA s WHERE s.ID_PRESENTE = p.ID AND PRECO_SUGERIDO IS NOT NULL) AS MELHOR_PRECO
FROM LCP_PRESENTE p
INNER JOIN LCP_USUARIO u ON p.ID_USUARIO = u.ID
WHERE p.STATUS = 'ATIVO'
  AND u.ATIVO = 'S';

COMMENT ON VIEW VW_APEX_PRESENTES_OUTROS IS 'View para listagem de presentes de outros usuarios no APEX';

-- View para notificacoes do usuario
CREATE OR REPLACE VIEW VW_APEX_NOTIFICACOES AS
SELECT
    n.ID,
    n.ID_USUARIO,
    n.MENSAGEM,
    n.LIDA,
    n.DATA_NOTIFICACAO,
    n.DATA_LEITURA,
    CASE
        WHEN n.DATA_NOTIFICACAO > SYSDATE - 1 THEN 'Hoje'
        WHEN n.DATA_NOTIFICACAO > SYSDATE - 2 THEN 'Ontem'
        WHEN n.DATA_NOTIFICACAO > SYSDATE - 7 THEN TO_CHAR(n.DATA_NOTIFICACAO, 'Day')
        ELSE TO_CHAR(n.DATA_NOTIFICACAO, 'DD/MM/YYYY')
    END AS DATA_FORMATADA
FROM LCP_NOTIFICACAO n
ORDER BY n.DATA_NOTIFICACAO DESC;

COMMENT ON VIEW VW_APEX_NOTIFICACOES IS 'View para notificacoes no APEX';

-- View para dashboard
CREATE OR REPLACE VIEW VW_APEX_DASHBOARD AS
SELECT
    u.ID AS ID_USUARIO,
    u.PRIMEIRO_NOME || ' ' || u.ULTIMO_NOME AS NOME_COMPLETO,
    (SELECT COUNT(*) FROM LCP_PRESENTE p WHERE p.ID_USUARIO = u.ID AND p.STATUS = 'ATIVO') AS PRESENTES_ATIVOS,
    (SELECT COUNT(*) FROM LCP_PRESENTE p WHERE p.ID_USUARIO = u.ID AND p.STATUS = 'COMPRADO') AS PRESENTES_COMPRADOS,
    (SELECT COUNT(*) FROM LCP_NOTIFICACAO n WHERE n.ID_USUARIO = u.ID AND n.LIDA = 'N') AS NOTIF_NAO_LIDAS,
    (SELECT COUNT(*) FROM LCP_COMPRA c WHERE c.ID_COMPRADOR = u.ID) AS COMPRAS_REALIZADAS,
    (SELECT COUNT(*) FROM LCP_PUSH_SUBSCRIPTION ps WHERE ps.ID_USUARIO = u.ID AND ps.ATIVO = 'S') AS PUSH_ATIVO
FROM LCP_USUARIO u
WHERE u.ATIVO = 'S';

COMMENT ON VIEW VW_APEX_DASHBOARD IS 'View para dashboard do usuario no APEX';


-- ==============================================================================
-- PARTE 6: FUNCOES AUXILIARES PARA APEX
-- ==============================================================================

-- Funcao para formatar preco
CREATE OR REPLACE FUNCTION FN_APEX_FORMATAR_PRECO(p_valor IN NUMBER) RETURN VARCHAR2 IS
BEGIN
    IF p_valor IS NULL THEN
        RETURN '-';
    END IF;
    RETURN 'R$ ' || TO_CHAR(p_valor, 'FM999G999G999D00', 'NLS_NUMERIC_CHARACTERS='',.''');
END FN_APEX_FORMATAR_PRECO;
/

-- Funcao para obter badge de status
CREATE OR REPLACE FUNCTION FN_APEX_BADGE_STATUS(p_status IN VARCHAR2) RETURN VARCHAR2 IS
BEGIN
    CASE p_status
        WHEN 'ATIVO' THEN
            RETURN '<span class="u-success-text"><span class="fa fa-gift"></span> Disponivel</span>';
        WHEN 'COMPRADO' THEN
            RETURN '<span class="u-color-success"><span class="fa fa-check-circle"></span> Comprado</span>';
        ELSE
            RETURN p_status;
    END CASE;
END FN_APEX_BADGE_STATUS;
/

-- Funcao para contar notificacoes nao lidas
CREATE OR REPLACE FUNCTION FN_APEX_NOTIF_COUNT RETURN NUMBER IS
    v_id_usuario NUMBER;
    v_count NUMBER;
BEGIN
    v_id_usuario := FN_APEX_GET_USER_ID;

    IF v_id_usuario IS NULL THEN
        RETURN 0;
    END IF;

    RETURN PKG_NOTIFICACAO.CONTAR_NAO_LIDAS(v_id_usuario);
END FN_APEX_NOTIF_COUNT;
/


-- ==============================================================================
-- FIM DO SCRIPT
-- ==============================================================================

PROMPT
PROMPT ========================================
PROMPT Funcoes e Views APEX criadas com sucesso!
PROMPT ========================================
PROMPT
PROMPT Objetos criados:
PROMPT   - FN_APEX_AUTENTICAR (Autenticacao customizada)
PROMPT   - FN_APEX_GET_USER_ID (Obter ID usuario logado)
PROMPT   - FN_APEX_IS_ADMIN (Verificar admin)
PROMPT   - PRC_APEX_ADICIONAR_PRESENTE
PROMPT   - PRC_APEX_COMPRAR_PRESENTE
PROMPT   - PRC_APEX_REGISTRAR_USUARIO
PROMPT   - VW_APEX_MEUS_PRESENTES
PROMPT   - VW_APEX_PRESENTES_OUTROS
PROMPT   - VW_APEX_NOTIFICACOES
PROMPT   - VW_APEX_DASHBOARD
PROMPT   - FN_APEX_FORMATAR_PRECO
PROMPT   - FN_APEX_BADGE_STATUS
PROMPT   - FN_APEX_NOTIF_COUNT
PROMPT ========================================
