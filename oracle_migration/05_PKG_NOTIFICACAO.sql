-- ==============================================================================
-- PACKAGE: PKG_NOTIFICACAO
-- Descricao: Gerenciamento de notificacoes
-- Desenvolvedor: Maxwell da Silva Oliveira (@maxwbh)
-- Email: maxwbh@gmail.com
-- Empresa: M&S do Brasil LTDA - msbrasil.inf.br
-- Data: 2025-11-21
-- ==============================================================================

-- ==============================================================================
-- SPECIFICATION
-- ==============================================================================
CREATE OR REPLACE PACKAGE PKG_NOTIFICACAO AS

    -- Tipos
    TYPE t_cursor IS REF CURSOR;

    -- Record type para notificacao
    TYPE t_notificacao IS RECORD (
        id                  LCP_NOTIFICACAO.ID%TYPE,
        id_usuario          LCP_NOTIFICACAO.ID_USUARIO%TYPE,
        mensagem            LCP_NOTIFICACAO.MENSAGEM%TYPE,
        lida                LCP_NOTIFICACAO.LIDA%TYPE,
        data_notificacao    LCP_NOTIFICACAO.DATA_NOTIFICACAO%TYPE,
        data_leitura        LCP_NOTIFICACAO.DATA_LEITURA%TYPE
    );

    /**
     * Cria nova notificacao
     * @param p_id_usuario ID do usuario
     * @param p_mensagem Mensagem da notificacao
     * @return ID da notificacao criada
     */
    FUNCTION CRIAR_NOTIFICACAO(
        p_id_usuario        IN NUMBER,
        p_mensagem          IN CLOB
    ) RETURN NUMBER;

    /**
     * Marca notificacao como lida
     * @param p_id_notificacao ID da notificacao
     * @param p_id_usuario ID do usuario (para validacao)
     */
    PROCEDURE MARCAR_LIDA(
        p_id_notificacao    IN NUMBER,
        p_id_usuario        IN NUMBER
    );

    /**
     * Marca todas notificacoes do usuario como lidas
     * @param p_id_usuario ID do usuario
     * @return Quantidade de notificacoes marcadas
     */
    FUNCTION MARCAR_TODAS_LIDAS(
        p_id_usuario        IN NUMBER
    ) RETURN NUMBER;

    /**
     * Lista notificacoes do usuario
     * @param p_id_usuario ID do usuario
     * @param p_apenas_nao_lidas TRUE para apenas nao lidas, FALSE para todas
     * @param p_limite Limite de registros (opcional)
     * @return Cursor com notificacoes
     */
    FUNCTION LISTAR_NOTIFICACOES(
        p_id_usuario        IN NUMBER,
        p_apenas_nao_lidas  IN BOOLEAN DEFAULT FALSE,
        p_limite            IN NUMBER DEFAULT NULL
    ) RETURN t_cursor;

    /**
     * Conta notificacoes nao lidas
     * @param p_id_usuario ID do usuario
     * @return Total de notificacoes nao lidas
     */
    FUNCTION CONTAR_NAO_LIDAS(
        p_id_usuario        IN NUMBER
    ) RETURN NUMBER;

    /**
     * Exclui notificacao
     * @param p_id_notificacao ID da notificacao
     * @param p_id_usuario ID do usuario (para validacao)
     */
    PROCEDURE EXCLUIR_NOTIFICACAO(
        p_id_notificacao    IN NUMBER,
        p_id_usuario        IN NUMBER
    );

    /**
     * Exclui todas notificacoes lidas do usuario
     * @param p_id_usuario ID do usuario
     * @return Quantidade de notificacoes excluidas
     */
    FUNCTION LIMPAR_NOTIFICACOES_LIDAS(
        p_id_usuario        IN NUMBER
    ) RETURN NUMBER;

    /**
     * Busca notificacao por ID
     * @param p_id_notificacao ID da notificacao
     * @return Record com dados da notificacao
     */
    FUNCTION BUSCAR_POR_ID(
        p_id_notificacao    IN NUMBER
    ) RETURN t_notificacao;

END PKG_NOTIFICACAO;
/


-- ==============================================================================
-- BODY
-- ==============================================================================
CREATE OR REPLACE PACKAGE BODY PKG_NOTIFICACAO AS

    -- ============================================================================
    -- CRIAR_NOTIFICACAO
    -- ============================================================================
    FUNCTION CRIAR_NOTIFICACAO(
        p_id_usuario        IN NUMBER,
        p_mensagem          IN CLOB
    ) RETURN NUMBER IS
        v_id_notificacao    NUMBER;
    BEGIN
        -- Validar se usuario existe
        DECLARE
            v_count NUMBER;
        BEGIN
            SELECT COUNT(*) INTO v_count
            FROM LCP_USUARIO
            WHERE ID = p_id_usuario;

            IF v_count = 0 THEN
                RAISE_APPLICATION_ERROR(-20001, 'Usuario nao encontrado');
            END IF;
        END;

        -- Inserir notificacao
        INSERT INTO LCP_NOTIFICACAO (
            ID,
            ID_USUARIO,
            MENSAGEM,
            LIDA,
            DATA_NOTIFICACAO
        ) VALUES (
            SEQ_LCP_NOTIFICACAO.NEXTVAL,
            p_id_usuario,
            p_mensagem,
            'N',
            SYSDATE
        ) RETURNING ID INTO v_id_notificacao;

        COMMIT;

        RETURN v_id_notificacao;
    EXCEPTION
        WHEN OTHERS THEN
            ROLLBACK;
            RAISE;
    END CRIAR_NOTIFICACAO;

    -- ============================================================================
    -- MARCAR_LIDA
    -- ============================================================================
    PROCEDURE MARCAR_LIDA(
        p_id_notificacao    IN NUMBER,
        p_id_usuario        IN NUMBER
    ) IS
        v_id_usuario_notif  NUMBER;
    BEGIN
        -- Verificar propriedade da notificacao
        BEGIN
            SELECT ID_USUARIO INTO v_id_usuario_notif
            FROM LCP_NOTIFICACAO
            WHERE ID = p_id_notificacao;
        EXCEPTION
            WHEN NO_DATA_FOUND THEN
                RAISE_APPLICATION_ERROR(-20301, 'Notificacao nao encontrada');
        END;

        IF v_id_usuario_notif != p_id_usuario THEN
            RAISE_APPLICATION_ERROR(-20102, 'Usuario nao autorizado');
        END IF;

        -- Marcar como lida
        UPDATE LCP_NOTIFICACAO
        SET LIDA = 'S',
            DATA_LEITURA = SYSDATE
        WHERE ID = p_id_notificacao
          AND LIDA = 'N'; -- Apenas se ainda nao foi lida

        COMMIT;
    EXCEPTION
        WHEN OTHERS THEN
            ROLLBACK;
            RAISE;
    END MARCAR_LIDA;

    -- ============================================================================
    -- MARCAR_TODAS_LIDAS
    -- ============================================================================
    FUNCTION MARCAR_TODAS_LIDAS(
        p_id_usuario        IN NUMBER
    ) RETURN NUMBER IS
        v_count NUMBER;
    BEGIN
        UPDATE LCP_NOTIFICACAO
        SET LIDA = 'S',
            DATA_LEITURA = SYSDATE
        WHERE ID_USUARIO = p_id_usuario
          AND LIDA = 'N';

        v_count := SQL%ROWCOUNT;
        COMMIT;

        RETURN v_count;
    EXCEPTION
        WHEN OTHERS THEN
            ROLLBACK;
            RAISE;
    END MARCAR_TODAS_LIDAS;

    -- ============================================================================
    -- LISTAR_NOTIFICACOES
    -- ============================================================================
    FUNCTION LISTAR_NOTIFICACOES(
        p_id_usuario        IN NUMBER,
        p_apenas_nao_lidas  IN BOOLEAN DEFAULT FALSE,
        p_limite            IN NUMBER DEFAULT NULL
    ) RETURN t_cursor IS
        v_cursor t_cursor;
        v_sql    VARCHAR2(4000);
    BEGIN
        v_sql := 'SELECT
                    ID,
                    ID_USUARIO,
                    MENSAGEM,
                    LIDA,
                    DATA_NOTIFICACAO,
                    DATA_LEITURA
                  FROM LCP_NOTIFICACAO
                  WHERE ID_USUARIO = :p_id_usuario';

        -- Filtrar apenas nao lidas
        IF p_apenas_nao_lidas THEN
            v_sql := v_sql || ' AND LIDA = ''N''';
        END IF;

        v_sql := v_sql || ' ORDER BY DATA_NOTIFICACAO DESC';

        -- Aplicar limite
        IF p_limite IS NOT NULL THEN
            v_sql := v_sql || ' FETCH FIRST :p_limite ROWS ONLY';
            OPEN v_cursor FOR v_sql USING p_id_usuario, p_limite;
        ELSE
            OPEN v_cursor FOR v_sql USING p_id_usuario;
        END IF;

        RETURN v_cursor;
    END LISTAR_NOTIFICACOES;

    -- ============================================================================
    -- CONTAR_NAO_LIDAS
    -- ============================================================================
    FUNCTION CONTAR_NAO_LIDAS(
        p_id_usuario        IN NUMBER
    ) RETURN NUMBER IS
        v_count NUMBER;
    BEGIN
        SELECT COUNT(*)
        INTO v_count
        FROM LCP_NOTIFICACAO
        WHERE ID_USUARIO = p_id_usuario
          AND LIDA = 'N';

        RETURN v_count;
    END CONTAR_NAO_LIDAS;

    -- ============================================================================
    -- EXCLUIR_NOTIFICACAO
    -- ============================================================================
    PROCEDURE EXCLUIR_NOTIFICACAO(
        p_id_notificacao    IN NUMBER,
        p_id_usuario        IN NUMBER
    ) IS
        v_id_usuario_notif  NUMBER;
    BEGIN
        -- Verificar propriedade
        BEGIN
            SELECT ID_USUARIO INTO v_id_usuario_notif
            FROM LCP_NOTIFICACAO
            WHERE ID = p_id_notificacao;
        EXCEPTION
            WHEN NO_DATA_FOUND THEN
                RAISE_APPLICATION_ERROR(-20301, 'Notificacao nao encontrada');
        END;

        IF v_id_usuario_notif != p_id_usuario THEN
            RAISE_APPLICATION_ERROR(-20102, 'Usuario nao autorizado');
        END IF;

        -- Excluir
        DELETE FROM LCP_NOTIFICACAO
        WHERE ID = p_id_notificacao;

        COMMIT;
    EXCEPTION
        WHEN OTHERS THEN
            ROLLBACK;
            RAISE;
    END EXCLUIR_NOTIFICACAO;

    -- ============================================================================
    -- LIMPAR_NOTIFICACOES_LIDAS
    -- ============================================================================
    FUNCTION LIMPAR_NOTIFICACOES_LIDAS(
        p_id_usuario        IN NUMBER
    ) RETURN NUMBER IS
        v_count NUMBER;
    BEGIN
        DELETE FROM LCP_NOTIFICACAO
        WHERE ID_USUARIO = p_id_usuario
          AND LIDA = 'S';

        v_count := SQL%ROWCOUNT;
        COMMIT;

        RETURN v_count;
    EXCEPTION
        WHEN OTHERS THEN
            ROLLBACK;
            RAISE;
    END LIMPAR_NOTIFICACOES_LIDAS;

    -- ============================================================================
    -- BUSCAR_POR_ID
    -- ============================================================================
    FUNCTION BUSCAR_POR_ID(
        p_id_notificacao    IN NUMBER
    ) RETURN t_notificacao IS
        v_notificacao t_notificacao;
    BEGIN
        SELECT
            ID,
            ID_USUARIO,
            MENSAGEM,
            LIDA,
            DATA_NOTIFICACAO,
            DATA_LEITURA
        INTO v_notificacao
        FROM LCP_NOTIFICACAO
        WHERE ID = p_id_notificacao;

        RETURN v_notificacao;
    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            RAISE_APPLICATION_ERROR(-20301, 'Notificacao nao encontrada');
    END BUSCAR_POR_ID;

END PKG_NOTIFICACAO;
/
