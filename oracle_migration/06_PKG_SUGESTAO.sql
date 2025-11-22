-- ==============================================================================
-- PACKAGE: PKG_SUGESTAO
-- Descricao: Gerenciamento de sugestoes de compra
-- Desenvolvedor: Maxwell da Silva Oliveira (@maxwbh)
-- Email: maxwbh@gmail.com
-- Empresa: M&S do Brasil LTDA - msbrasil.inf.br
-- Data: 2025-11-21
-- ==============================================================================

-- ==============================================================================
-- SPECIFICATION
-- ==============================================================================
CREATE OR REPLACE PACKAGE PKG_SUGESTAO AS

    -- Tipos
    TYPE t_cursor IS REF CURSOR;

    -- Record type para sugestao
    TYPE t_sugestao IS RECORD (
        id_sugestao         LCP_SUGESTAO_COMPRA.ID%TYPE,
        id_presente         LCP_SUGESTAO_COMPRA.ID_PRESENTE%TYPE,
        local_compra        LCP_SUGESTAO_COMPRA.LOCAL_COMPRA%TYPE,
        url_compra          LCP_SUGESTAO_COMPRA.URL_COMPRA%TYPE,
        preco_sugerido      LCP_SUGESTAO_COMPRA.PRECO_SUGERIDO%TYPE,
        data_busca          LCP_SUGESTAO_COMPRA.DATA_BUSCA%TYPE
    );

    /**
     * Adiciona sugestao de compra
     * @param p_id_presente ID do presente
     * @param p_local_compra Nome da loja
     * @param p_url_compra URL do produto
     * @param p_preco_sugerido Preco sugerido (opcional)
     * @return ID da sugestao criada
     */
    FUNCTION ADICIONAR_SUGESTAO(
        p_id_presente       IN NUMBER,
        p_local_compra      IN VARCHAR2,
        p_url_compra        IN VARCHAR2,
        p_preco_sugerido    IN NUMBER DEFAULT NULL
    ) RETURN NUMBER;

    /**
     * Adiciona multiplas sugestoes de uma vez
     * Util para integracoes com APIs externas
     * @param p_id_presente ID do presente
     * @param p_limpar_antigas TRUE para limpar sugestoes antigas antes
     */
    PROCEDURE ADICIONAR_SUGESTOES_LOTE(
        p_id_presente       IN NUMBER,
        p_limpar_antigas    IN BOOLEAN DEFAULT TRUE
    );

    /**
     * Atualiza sugestao
     * @param p_id_sugestao ID da sugestao
     * @param p_local_compra Novo local (opcional)
     * @param p_url_compra Nova URL (opcional)
     * @param p_preco_sugerido Novo preco (opcional)
     */
    PROCEDURE ATUALIZAR_SUGESTAO(
        p_id_sugestao       IN NUMBER,
        p_local_compra      IN VARCHAR2 DEFAULT NULL,
        p_url_compra        IN VARCHAR2 DEFAULT NULL,
        p_preco_sugerido    IN NUMBER DEFAULT NULL
    );

    /**
     * Exclui sugestao
     * @param p_id_sugestao ID da sugestao
     */
    PROCEDURE EXCLUIR_SUGESTAO(
        p_id_sugestao       IN NUMBER
    );

    /**
     * Exclui todas sugestoes de um presente
     * @param p_id_presente ID do presente
     * @return Quantidade de sugestoes excluidas
     */
    FUNCTION LIMPAR_SUGESTOES(
        p_id_presente       IN NUMBER
    ) RETURN NUMBER;

    /**
     * Lista sugestoes de um presente
     * @param p_id_presente ID do presente
     * @param p_ordenar_por Criterio de ordenacao (PRECO/DATA/LOJA)
     * @return Cursor com sugestoes
     */
    FUNCTION LISTAR_SUGESTOES(
        p_id_presente       IN NUMBER,
        p_ordenar_por       IN VARCHAR2 DEFAULT 'PRECO'
    ) RETURN t_cursor;

    /**
     * Busca sugestao por ID
     * @param p_id_sugestao ID da sugestao
     * @return Record com dados da sugestao
     */
    FUNCTION BUSCAR_POR_ID(
        p_id_sugestao       IN NUMBER
    ) RETURN t_sugestao;

    /**
     * Obtem melhor preco (menor) entre as sugestoes
     * @param p_id_presente ID do presente
     * @return Menor preco encontrado (NULL se nenhum)
     */
    FUNCTION OBTER_MELHOR_PRECO(
        p_id_presente       IN NUMBER
    ) RETURN NUMBER;

    /**
     * Obtem sugestao com melhor preco
     * @param p_id_presente ID do presente
     * @return Cursor com a melhor sugestao
     */
    FUNCTION OBTER_MELHOR_SUGESTAO(
        p_id_presente       IN NUMBER
    ) RETURN t_cursor;

    /**
     * Conta sugestoes de um presente
     * @param p_id_presente ID do presente
     * @return Total de sugestoes
     */
    FUNCTION CONTAR_SUGESTOES(
        p_id_presente       IN NUMBER
    ) RETURN NUMBER;

    /**
     * Atualiza data de busca das sugestoes
     * Util para indicar que as sugestoes foram revalidadas
     * @param p_id_presente ID do presente
     */
    PROCEDURE ATUALIZAR_DATA_BUSCA(
        p_id_presente       IN NUMBER
    );

END PKG_SUGESTAO;
/


-- ==============================================================================
-- BODY
-- ==============================================================================
CREATE OR REPLACE PACKAGE BODY PKG_SUGESTAO AS

    -- ============================================================================
    -- ADICIONAR_SUGESTAO
    -- ============================================================================
    FUNCTION ADICIONAR_SUGESTAO(
        p_id_presente       IN NUMBER,
        p_local_compra      IN VARCHAR2,
        p_url_compra        IN VARCHAR2,
        p_preco_sugerido    IN NUMBER DEFAULT NULL
    ) RETURN NUMBER IS
        v_id_sugestao       NUMBER;
    BEGIN
        -- Validar se presente existe
        DECLARE
            v_count NUMBER;
        BEGIN
            SELECT COUNT(*) INTO v_count
            FROM LCP_PRESENTE
            WHERE ID_PRESENTE = p_id_presente;

            IF v_count = 0 THEN
                RAISE_APPLICATION_ERROR(-20101, 'Presente nao encontrado');
            END IF;
        END;

        -- Validar dados obrigatorios
        IF TRIM(p_local_compra) IS NULL THEN
            RAISE_APPLICATION_ERROR(-20401, 'Local de compra e obrigatorio');
        END IF;

        IF TRIM(p_url_compra) IS NULL THEN
            RAISE_APPLICATION_ERROR(-20402, 'URL de compra e obrigatoria');
        END IF;

        -- Inserir sugestao
        INSERT INTO LCP_SUGESTAO_COMPRA (
            ID,
            ID_PRESENTE,
            LOCAL_COMPRA,
            URL_COMPRA,
            PRECO_SUGERIDO,
            DATA_BUSCA
        ) VALUES (
            SEQ_LCP_SUGESTAO_COMPRA.NEXTVAL,
            p_id_presente,
            TRIM(p_local_compra),
            TRIM(p_url_compra),
            p_preco_sugerido,
            SYSDATE
        ) RETURNING ID INTO v_id_sugestao;

        COMMIT;

        RETURN v_id_sugestao;
    EXCEPTION
        WHEN OTHERS THEN
            ROLLBACK;
            RAISE;
    END ADICIONAR_SUGESTAO;

    -- ============================================================================
    -- ADICIONAR_SUGESTOES_LOTE
    -- ============================================================================
    PROCEDURE ADICIONAR_SUGESTOES_LOTE(
        p_id_presente       IN NUMBER,
        p_limpar_antigas    IN BOOLEAN DEFAULT TRUE
    ) IS
    BEGIN
        -- Esta procedure e um placeholder para integracao futura
        -- com APIs externas (Zoom, Buscape, etc)
        -- Por enquanto, apenas limpa sugestoes antigas se solicitado

        IF p_limpar_antigas THEN
            DELETE FROM LCP_SUGESTAO_COMPRA
            WHERE ID_PRESENTE = p_id_presente;
            COMMIT;
        END IF;

        -- Aqui seria o ponto de integracao com APIs externas
        -- Exemplo:
        -- 1. Buscar dados via UTL_HTTP ou APEX_WEB_SERVICE
        -- 2. Parsear JSON de resposta
        -- 3. Inserir cada sugestao usando ADICIONAR_SUGESTAO

    END ADICIONAR_SUGESTOES_LOTE;

    -- ============================================================================
    -- ATUALIZAR_SUGESTAO
    -- ============================================================================
    PROCEDURE ATUALIZAR_SUGESTAO(
        p_id_sugestao       IN NUMBER,
        p_local_compra      IN VARCHAR2 DEFAULT NULL,
        p_url_compra        IN VARCHAR2 DEFAULT NULL,
        p_preco_sugerido    IN NUMBER DEFAULT NULL
    ) IS
        v_count NUMBER;
    BEGIN
        -- Verificar se sugestao existe
        SELECT COUNT(*) INTO v_count
        FROM LCP_SUGESTAO_COMPRA
        WHERE ID = p_id_sugestao;

        IF v_count = 0 THEN
            RAISE_APPLICATION_ERROR(-20403, 'Sugestao nao encontrada');
        END IF;

        -- Atualizar apenas campos informados
        UPDATE LCP_SUGESTAO_COMPRA
        SET LOCAL_COMPRA = NVL(p_local_compra, LOCAL_COMPRA),
            URL_COMPRA = NVL(p_url_compra, URL_COMPRA),
            PRECO_SUGERIDO = NVL(p_preco_sugerido, PRECO_SUGERIDO),
            DATA_BUSCA = SYSDATE
        WHERE ID = p_id_sugestao;

        COMMIT;
    EXCEPTION
        WHEN OTHERS THEN
            ROLLBACK;
            RAISE;
    END ATUALIZAR_SUGESTAO;

    -- ============================================================================
    -- EXCLUIR_SUGESTAO
    -- ============================================================================
    PROCEDURE EXCLUIR_SUGESTAO(
        p_id_sugestao       IN NUMBER
    ) IS
    BEGIN
        DELETE FROM LCP_SUGESTAO_COMPRA
        WHERE ID = p_id_sugestao;

        IF SQL%ROWCOUNT = 0 THEN
            RAISE_APPLICATION_ERROR(-20403, 'Sugestao nao encontrada');
        END IF;

        COMMIT;
    EXCEPTION
        WHEN OTHERS THEN
            ROLLBACK;
            RAISE;
    END EXCLUIR_SUGESTAO;

    -- ============================================================================
    -- LIMPAR_SUGESTOES
    -- ============================================================================
    FUNCTION LIMPAR_SUGESTOES(
        p_id_presente       IN NUMBER
    ) RETURN NUMBER IS
        v_count NUMBER;
    BEGIN
        DELETE FROM LCP_SUGESTAO_COMPRA
        WHERE ID_PRESENTE = p_id_presente;

        v_count := SQL%ROWCOUNT;
        COMMIT;

        RETURN v_count;
    EXCEPTION
        WHEN OTHERS THEN
            ROLLBACK;
            RAISE;
    END LIMPAR_SUGESTOES;

    -- ============================================================================
    -- LISTAR_SUGESTOES
    -- ============================================================================
    FUNCTION LISTAR_SUGESTOES(
        p_id_presente       IN NUMBER,
        p_ordenar_por       IN VARCHAR2 DEFAULT 'PRECO'
    ) RETURN t_cursor IS
        v_cursor t_cursor;
        v_order_by VARCHAR2(100);
    BEGIN
        -- Determinar ordenacao
        CASE UPPER(p_ordenar_por)
            WHEN 'PRECO' THEN
                v_order_by := 'PRECO_SUGERIDO NULLS LAST, LOCAL_COMPRA';
            WHEN 'DATA' THEN
                v_order_by := 'DATA_BUSCA DESC';
            WHEN 'LOJA' THEN
                v_order_by := 'LOCAL_COMPRA';
            ELSE
                v_order_by := 'PRECO_SUGERIDO NULLS LAST, LOCAL_COMPRA';
        END CASE;

        OPEN v_cursor FOR
            'SELECT
                ID,
                ID_PRESENTE,
                LOCAL_COMPRA,
                URL_COMPRA,
                PRECO_SUGERIDO,
                DATA_BUSCA
             FROM LCP_SUGESTAO_COMPRA
             WHERE ID_PRESENTE = :p_id_presente
             ORDER BY ' || v_order_by
        USING p_id_presente;

        RETURN v_cursor;
    END LISTAR_SUGESTOES;

    -- ============================================================================
    -- BUSCAR_POR_ID
    -- ============================================================================
    FUNCTION BUSCAR_POR_ID(
        p_id_sugestao       IN NUMBER
    ) RETURN t_sugestao IS
        v_sugestao t_sugestao;
    BEGIN
        SELECT
            ID,
            ID_PRESENTE,
            LOCAL_COMPRA,
            URL_COMPRA,
            PRECO_SUGERIDO,
            DATA_BUSCA
        INTO v_sugestao
        FROM LCP_SUGESTAO_COMPRA
        WHERE ID = p_id_sugestao;

        RETURN v_sugestao;
    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            RAISE_APPLICATION_ERROR(-20403, 'Sugestao nao encontrada');
    END BUSCAR_POR_ID;

    -- ============================================================================
    -- OBTER_MELHOR_PRECO
    -- ============================================================================
    FUNCTION OBTER_MELHOR_PRECO(
        p_id_presente       IN NUMBER
    ) RETURN NUMBER IS
        v_melhor_preco NUMBER;
    BEGIN
        SELECT MIN(PRECO_SUGERIDO)
        INTO v_melhor_preco
        FROM LCP_SUGESTAO_COMPRA
        WHERE ID_PRESENTE = p_id_presente
          AND PRECO_SUGERIDO IS NOT NULL;

        RETURN v_melhor_preco;
    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            RETURN NULL;
    END OBTER_MELHOR_PRECO;

    -- ============================================================================
    -- OBTER_MELHOR_SUGESTAO
    -- ============================================================================
    FUNCTION OBTER_MELHOR_SUGESTAO(
        p_id_presente       IN NUMBER
    ) RETURN t_cursor IS
        v_cursor t_cursor;
    BEGIN
        OPEN v_cursor FOR
            SELECT
                ID,
                ID_PRESENTE,
                LOCAL_COMPRA,
                URL_COMPRA,
                PRECO_SUGERIDO,
                DATA_BUSCA
            FROM LCP_SUGESTAO_COMPRA
            WHERE ID_PRESENTE = p_id_presente
              AND PRECO_SUGERIDO IS NOT NULL
            ORDER BY PRECO_SUGERIDO
            FETCH FIRST 1 ROW ONLY;

        RETURN v_cursor;
    END OBTER_MELHOR_SUGESTAO;

    -- ============================================================================
    -- CONTAR_SUGESTOES
    -- ============================================================================
    FUNCTION CONTAR_SUGESTOES(
        p_id_presente       IN NUMBER
    ) RETURN NUMBER IS
        v_count NUMBER;
    BEGIN
        SELECT COUNT(*)
        INTO v_count
        FROM LCP_SUGESTAO_COMPRA
        WHERE ID_PRESENTE = p_id_presente;

        RETURN v_count;
    END CONTAR_SUGESTOES;

    -- ============================================================================
    -- ATUALIZAR_DATA_BUSCA
    -- ============================================================================
    PROCEDURE ATUALIZAR_DATA_BUSCA(
        p_id_presente       IN NUMBER
    ) IS
    BEGIN
        UPDATE LCP_SUGESTAO_COMPRA
        SET DATA_BUSCA = SYSDATE
        WHERE ID_PRESENTE = p_id_presente;

        COMMIT;
    END ATUALIZAR_DATA_BUSCA;

END PKG_SUGESTAO;
/
