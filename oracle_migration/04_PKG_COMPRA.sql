-- ==============================================================================
-- PACKAGE: PKG_COMPRA
-- Descricao: Gerenciamento de compras de presentes
-- Desenvolvedor: Maxwell da Silva Oliveira (@maxwbh)
-- Email: maxwbh@gmail.com
-- Empresa: M&S do Brasil LTDA - msbrasil.inf.br
-- Data: 2025-11-21
-- ==============================================================================

-- ==============================================================================
-- SPECIFICATION
-- ==============================================================================
CREATE OR REPLACE PACKAGE PKG_COMPRA AS

    -- Tipos
    TYPE t_cursor IS REF CURSOR;

    -- Excecoes customizadas
    EX_PRESENTE_JA_COMPRADO     EXCEPTION;
    EX_PROPRIO_PRESENTE         EXCEPTION;
    EX_PRESENTE_NAO_ATIVO       EXCEPTION;
    EX_COMPRA_NAO_ENCONTRADA    EXCEPTION;

    PRAGMA EXCEPTION_INIT(EX_PRESENTE_JA_COMPRADO, -20201);
    PRAGMA EXCEPTION_INIT(EX_PROPRIO_PRESENTE, -20202);
    PRAGMA EXCEPTION_INIT(EX_PRESENTE_NAO_ATIVO, -20203);
    PRAGMA EXCEPTION_INIT(EX_COMPRA_NAO_ENCONTRADA, -20204);

    /**
     * Marca presente como comprado
     * - Valida se presente pode ser comprado
     * - Cria registro de compra
     * - Atualiza status do presente
     * - Cria notificacao para dono do presente
     * @param p_id_presente ID do presente
     * @param p_id_comprador ID do usuario comprador
     * @return ID da compra criada
     */
    FUNCTION MARCAR_COMPRADO(
        p_id_presente       IN NUMBER,
        p_id_comprador      IN NUMBER
    ) RETURN NUMBER;

    /**
     * Cancela compra de presente
     * - Valida se compra existe
     * - Volta presente para status ATIVO
     * - Remove registro de compra
     * - Cria notificacao
     * @param p_id_presente ID do presente
     * @param p_id_usuario ID do usuario (deve ser o comprador ou dono)
     */
    PROCEDURE CANCELAR_COMPRA(
        p_id_presente       IN NUMBER,
        p_id_usuario        IN NUMBER
    );

    /**
     * Lista compras realizadas por usuario
     * @param p_id_comprador ID do comprador
     * @return Cursor com compras
     */
    FUNCTION LISTAR_MINHAS_COMPRAS(
        p_id_comprador      IN NUMBER
    ) RETURN t_cursor;

    /**
     * Lista presentes comprados de um usuario
     * @param p_id_usuario ID do usuario dono dos presentes
     * @return Cursor com presentes comprados
     */
    FUNCTION LISTAR_PRESENTES_COMPRADOS(
        p_id_usuario        IN NUMBER
    ) RETURN t_cursor;

    /**
     * Busca dados da compra por presente
     * @param p_id_presente ID do presente
     * @return Cursor com dados da compra
     */
    FUNCTION BUSCAR_COMPRA_POR_PRESENTE(
        p_id_presente       IN NUMBER
    ) RETURN t_cursor;

    /**
     * Verifica se presente ja foi comprado
     * @param p_id_presente ID do presente
     * @return TRUE se comprado, FALSE caso contrario
     */
    FUNCTION IS_COMPRADO(
        p_id_presente       IN NUMBER
    ) RETURN BOOLEAN;

    /**
     * Verifica se usuario comprou o presente
     * @param p_id_presente ID do presente
     * @param p_id_usuario ID do usuario
     * @return TRUE se usuario comprou, FALSE caso contrario
     */
    FUNCTION IS_COMPRADOR(
        p_id_presente       IN NUMBER,
        p_id_usuario        IN NUMBER
    ) RETURN BOOLEAN;

    /**
     * Conta total de compras realizadas por usuario
     * @param p_id_comprador ID do comprador
     * @return Total de compras
     */
    FUNCTION CONTAR_MINHAS_COMPRAS(
        p_id_comprador      IN NUMBER
    ) RETURN NUMBER;

END PKG_COMPRA;
/


-- ==============================================================================
-- BODY
-- ==============================================================================
CREATE OR REPLACE PACKAGE BODY PKG_COMPRA AS

    -- ============================================================================
    -- MARCAR_COMPRADO
    -- Corrigido: Race Condition - usar UPDATE atomico com validacoes no WHERE
    -- ============================================================================
    FUNCTION MARCAR_COMPRADO(
        p_id_presente       IN NUMBER,
        p_id_comprador      IN NUMBER
    ) RETURN NUMBER IS
        v_id_compra         NUMBER;
        v_id_usuario_dono   NUMBER;
        v_descricao         CLOB;
        v_rows_updated      NUMBER;
    BEGIN
        -- Buscar dados do presente primeiro (para validacoes e notificacao)
        BEGIN
            SELECT p.ID_USUARIO, p.DESCRICAO
            INTO v_id_usuario_dono, v_descricao
            FROM LCP_PRESENTE p
            WHERE p.ID = p_id_presente;
        EXCEPTION
            WHEN NO_DATA_FOUND THEN
                RAISE_APPLICATION_ERROR(-20101, 'Presente nao encontrado');
        END;

        -- Validacao: Nao pode comprar proprio presente
        IF v_id_usuario_dono = p_id_comprador THEN
            RAISE EX_PROPRIO_PRESENTE;
        END IF;

        -- UPDATE ATOMICO: Atualizar apenas se STATUS = 'ATIVO'
        -- Isso previne race condition pois a verificacao e update sao atomicos
        UPDATE LCP_PRESENTE
        SET STATUS = 'COMPRADO',
            DATA_ALTERACAO = SYSDATE
        WHERE ID = p_id_presente
          AND STATUS = 'ATIVO'
          AND NOT EXISTS (
              SELECT 1 FROM LCP_COMPRA c WHERE c.ID_PRESENTE = p_id_presente
          );

        v_rows_updated := SQL%ROWCOUNT;

        -- Se nenhuma linha foi atualizada, presente ja foi comprado
        IF v_rows_updated = 0 THEN
            RAISE EX_PRESENTE_JA_COMPRADO;
        END IF;

        -- Criar registro de compra (agora seguro pois presente ja esta COMPRADO)
        INSERT INTO LCP_COMPRA (
            ID,
            ID_PRESENTE,
            ID_COMPRADOR,
            DATA_COMPRA
        ) VALUES (
            SEQ_LCP_COMPRA.NEXTVAL,
            p_id_presente,
            p_id_comprador,
            SYSDATE
        ) RETURNING ID INTO v_id_compra;

        -- Criar notificacao para dono do presente
        PKG_NOTIFICACAO.CRIAR_NOTIFICACAO(
            p_id_usuario => v_id_usuario_dono,
            p_mensagem => '🎁 Um dos seus presentes foi comprado: ' ||
                         SUBSTR(v_descricao, 1, 50) || '!'
        );

        COMMIT;

        RETURN v_id_compra;
    EXCEPTION
        WHEN EX_PROPRIO_PRESENTE THEN
            ROLLBACK;
            RAISE_APPLICATION_ERROR(-20202, 'Voce nao pode comprar seu proprio presente');
        WHEN EX_PRESENTE_JA_COMPRADO THEN
            ROLLBACK;
            RAISE_APPLICATION_ERROR(-20201, 'Este presente ja foi comprado');
        WHEN OTHERS THEN
            ROLLBACK;
            RAISE;
    END MARCAR_COMPRADO;

    -- ============================================================================
    -- CANCELAR_COMPRA
    -- ============================================================================
    PROCEDURE CANCELAR_COMPRA(
        p_id_presente       IN NUMBER,
        p_id_usuario        IN NUMBER
    ) IS
        v_id_comprador      NUMBER;
        v_id_usuario_dono   NUMBER;
        v_descricao         CLOB;
    BEGIN
        -- Buscar dados da compra
        BEGIN
            SELECT c.ID_COMPRADOR, p.ID_USUARIO, p.DESCRICAO
            INTO v_id_comprador, v_id_usuario_dono, v_descricao
            FROM LCP_COMPRA c
            INNER JOIN LCP_PRESENTE p ON c.ID_PRESENTE = p.ID
            WHERE c.ID_PRESENTE = p_id_presente;
        EXCEPTION
            WHEN NO_DATA_FOUND THEN
                RAISE EX_COMPRA_NAO_ENCONTRADA;
        END;

        -- Validar se usuario pode cancelar (comprador ou dono)
        IF v_id_comprador != p_id_usuario AND v_id_usuario_dono != p_id_usuario THEN
            RAISE_APPLICATION_ERROR(-20102, 'Usuario nao autorizado para cancelar esta compra');
        END IF;

        -- Voltar presente para ATIVO
        UPDATE LCP_PRESENTE
        SET STATUS = 'ATIVO',
            DATA_ALTERACAO = SYSDATE
        WHERE ID = p_id_presente;

        -- Excluir compra
        DELETE FROM LCP_COMPRA
        WHERE ID_PRESENTE = p_id_presente;

        -- Criar notificacao
        IF v_id_comprador = p_id_usuario THEN
            -- Comprador cancelou - notificar dono
            PKG_NOTIFICACAO.CRIAR_NOTIFICACAO(
                p_id_usuario => v_id_usuario_dono,
                p_mensagem => '⚠️ A compra de um presente foi cancelada: ' ||
                             SUBSTR(v_descricao, 1, 50)
            );
        ELSE
            -- Dono cancelou - notificar comprador
            PKG_NOTIFICACAO.CRIAR_NOTIFICACAO(
                p_id_usuario => v_id_comprador,
                p_mensagem => '⚠️ Uma compra que voce realizou foi cancelada: ' ||
                             SUBSTR(v_descricao, 1, 50)
            );
        END IF;

        COMMIT;
    EXCEPTION
        WHEN EX_COMPRA_NAO_ENCONTRADA THEN
            RAISE_APPLICATION_ERROR(-20204, 'Compra nao encontrada');
        WHEN OTHERS THEN
            ROLLBACK;
            RAISE;
    END CANCELAR_COMPRA;

    -- ============================================================================
    -- LISTAR_MINHAS_COMPRAS
    -- ============================================================================
    FUNCTION LISTAR_MINHAS_COMPRAS(
        p_id_comprador      IN NUMBER
    ) RETURN t_cursor IS
        v_cursor t_cursor;
    BEGIN
        OPEN v_cursor FOR
            SELECT
                c.ID,
                c.ID_PRESENTE,
                c.DATA_COMPRA,
                -- Dados do presente
                p.DESCRICAO,
                p.URL,
                p.PRECO,
                CASE WHEN p.IMAGEM_BASE64 IS NOT NULL THEN 'S' ELSE 'N' END AS TEM_IMAGEM,
                -- Dados do dono do presente
                u.ID AS ID_DONO,
                u.PRIMEIRO_NOME || ' ' || u.ULTIMO_NOME AS NOME_DONO,
                u.EMAIL AS EMAIL_DONO
            FROM LCP_COMPRA c
            INNER JOIN LCP_PRESENTE p ON c.ID_PRESENTE = p.ID
            INNER JOIN LCP_USUARIO u ON p.ID_USUARIO = u.ID
            WHERE c.ID_COMPRADOR = p_id_comprador
            ORDER BY c.DATA_COMPRA DESC;

        RETURN v_cursor;
    END LISTAR_MINHAS_COMPRAS;

    -- ============================================================================
    -- LISTAR_PRESENTES_COMPRADOS
    -- ============================================================================
    FUNCTION LISTAR_PRESENTES_COMPRADOS(
        p_id_usuario        IN NUMBER
    ) RETURN t_cursor IS
        v_cursor t_cursor;
    BEGIN
        OPEN v_cursor FOR
            SELECT
                p.ID,
                p.DESCRICAO,
                p.URL,
                p.PRECO,
                p.DATA_CADASTRO,
                CASE WHEN p.IMAGEM_BASE64 IS NOT NULL THEN 'S' ELSE 'N' END AS TEM_IMAGEM,
                -- Dados da compra
                c.ID,
                c.DATA_COMPRA,
                -- Dados do comprador
                comp.ID AS ID_COMPRADOR,
                comp.PRIMEIRO_NOME || ' ' || comp.ULTIMO_NOME AS NOME_COMPRADOR,
                comp.EMAIL AS EMAIL_COMPRADOR
            FROM LCP_PRESENTE p
            INNER JOIN LCP_COMPRA c ON p.ID = c.ID_PRESENTE
            INNER JOIN LCP_USUARIO comp ON c.ID_COMPRADOR = comp.ID
            WHERE p.ID_USUARIO = p_id_usuario
            ORDER BY c.DATA_COMPRA DESC;

        RETURN v_cursor;
    END LISTAR_PRESENTES_COMPRADOS;

    -- ============================================================================
    -- BUSCAR_COMPRA_POR_PRESENTE
    -- ============================================================================
    FUNCTION BUSCAR_COMPRA_POR_PRESENTE(
        p_id_presente       IN NUMBER
    ) RETURN t_cursor IS
        v_cursor t_cursor;
    BEGIN
        OPEN v_cursor FOR
            SELECT
                c.ID,
                c.ID_PRESENTE,
                c.ID_COMPRADOR,
                c.DATA_COMPRA,
                -- Dados do comprador
                u.PRIMEIRO_NOME || ' ' || u.ULTIMO_NOME AS NOME_COMPRADOR,
                u.EMAIL AS EMAIL_COMPRADOR
            FROM LCP_COMPRA c
            INNER JOIN LCP_USUARIO u ON c.ID_COMPRADOR = u.ID
            WHERE c.ID_PRESENTE = p_id_presente;

        RETURN v_cursor;
    END BUSCAR_COMPRA_POR_PRESENTE;

    -- ============================================================================
    -- IS_COMPRADO
    -- ============================================================================
    FUNCTION IS_COMPRADO(
        p_id_presente       IN NUMBER
    ) RETURN BOOLEAN IS
        v_count NUMBER;
    BEGIN
        SELECT COUNT(*) INTO v_count
        FROM LCP_COMPRA
        WHERE ID_PRESENTE = p_id_presente;

        RETURN v_count > 0;
    END IS_COMPRADO;

    -- ============================================================================
    -- IS_COMPRADOR
    -- ============================================================================
    FUNCTION IS_COMPRADOR(
        p_id_presente       IN NUMBER,
        p_id_usuario        IN NUMBER
    ) RETURN BOOLEAN IS
        v_count NUMBER;
    BEGIN
        SELECT COUNT(*) INTO v_count
        FROM LCP_COMPRA
        WHERE ID_PRESENTE = p_id_presente
          AND ID_COMPRADOR = p_id_usuario;

        RETURN v_count > 0;
    END IS_COMPRADOR;

    -- ============================================================================
    -- CONTAR_MINHAS_COMPRAS
    -- ============================================================================
    FUNCTION CONTAR_MINHAS_COMPRAS(
        p_id_comprador      IN NUMBER
    ) RETURN NUMBER IS
        v_count NUMBER;
    BEGIN
        SELECT COUNT(*) INTO v_count
        FROM LCP_COMPRA
        WHERE ID_COMPRADOR = p_id_comprador;

        RETURN v_count;
    END CONTAR_MINHAS_COMPRAS;

END PKG_COMPRA;
/
