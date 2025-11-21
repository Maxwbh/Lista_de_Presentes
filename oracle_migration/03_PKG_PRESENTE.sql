-- ==============================================================================
-- PACKAGE: PKG_PRESENTE
-- Descricao: Gerenciamento de presentes do sistema
-- Desenvolvedor: Maxwell da Silva Oliveira (@maxwbh)
-- Email: maxwbh@gmail.com
-- Empresa: M&S do Brasil LTDA - msbrasil.inf.br
-- Data: 2025-11-21
-- ==============================================================================

-- ==============================================================================
-- SPECIFICATION
-- ==============================================================================
CREATE OR REPLACE PACKAGE PKG_PRESENTE AS

    -- Tipos
    TYPE t_cursor IS REF CURSOR;

    -- Record type para presente
    TYPE t_presente IS RECORD (
        id_presente         TB_PRESENTE.ID_PRESENTE%TYPE,
        id_usuario          TB_PRESENTE.ID_USUARIO%TYPE,
        descricao           TB_PRESENTE.DESCRICAO%TYPE,
        url                 TB_PRESENTE.URL%TYPE,
        preco               TB_PRESENTE.PRECO%TYPE,
        status              TB_PRESENTE.STATUS%TYPE,
        data_cadastro       TB_PRESENTE.DATA_CADASTRO%TYPE
    );

    -- Excecoes customizadas
    EX_PRESENTE_NAO_ENCONTRADO  EXCEPTION;
    EX_USUARIO_NAO_AUTORIZADO   EXCEPTION;
    EX_PRESENTE_JA_COMPRADO     EXCEPTION;
    EX_PROPRIO_PRESENTE         EXCEPTION;

    PRAGMA EXCEPTION_INIT(EX_PRESENTE_NAO_ENCONTRADO, -20101);
    PRAGMA EXCEPTION_INIT(EX_USUARIO_NAO_AUTORIZADO, -20102);
    PRAGMA EXCEPTION_INIT(EX_PRESENTE_JA_COMPRADO, -20103);
    PRAGMA EXCEPTION_INIT(EX_PROPRIO_PRESENTE, -20104);

    /**
     * Adiciona novo presente
     * @param p_id_usuario ID do usuario dono do presente
     * @param p_descricao Descricao do presente
     * @param p_url URL do produto (opcional)
     * @param p_preco Preco estimado (opcional)
     * @param p_imagem_base64 Imagem em base64 (opcional)
     * @param p_imagem_nome Nome do arquivo da imagem (opcional)
     * @param p_imagem_tipo MIME type da imagem (opcional)
     * @return ID do presente criado
     */
    FUNCTION ADICIONAR_PRESENTE(
        p_id_usuario        IN NUMBER,
        p_descricao         IN CLOB,
        p_url               IN VARCHAR2 DEFAULT NULL,
        p_preco             IN NUMBER DEFAULT NULL,
        p_imagem_base64     IN CLOB DEFAULT NULL,
        p_imagem_nome       IN VARCHAR2 DEFAULT NULL,
        p_imagem_tipo       IN VARCHAR2 DEFAULT NULL
    ) RETURN NUMBER;

    /**
     * Atualiza dados do presente
     * @param p_id_presente ID do presente
     * @param p_id_usuario ID do usuario (para validacao de propriedade)
     * @param p_descricao Nova descricao (opcional)
     * @param p_url Nova URL (opcional)
     * @param p_preco Novo preco (opcional)
     * @param p_imagem_base64 Nova imagem (opcional)
     * @param p_imagem_nome Nome da imagem (opcional)
     * @param p_imagem_tipo Tipo da imagem (opcional)
     */
    PROCEDURE ATUALIZAR_PRESENTE(
        p_id_presente       IN NUMBER,
        p_id_usuario        IN NUMBER,
        p_descricao         IN CLOB DEFAULT NULL,
        p_url               IN VARCHAR2 DEFAULT NULL,
        p_preco             IN NUMBER DEFAULT NULL,
        p_imagem_base64     IN CLOB DEFAULT NULL,
        p_imagem_nome       IN VARCHAR2 DEFAULT NULL,
        p_imagem_tipo       IN VARCHAR2 DEFAULT NULL
    );

    /**
     * Exclui presente
     * @param p_id_presente ID do presente
     * @param p_id_usuario ID do usuario (para validacao de propriedade)
     */
    PROCEDURE EXCLUIR_PRESENTE(
        p_id_presente       IN NUMBER,
        p_id_usuario        IN NUMBER
    );

    /**
     * Busca presente por ID
     * @param p_id_presente ID do presente
     * @return Cursor com dados do presente
     */
    FUNCTION BUSCAR_POR_ID(
        p_id_presente       IN NUMBER
    ) RETURN t_cursor;

    /**
     * Lista presentes do usuario
     * @param p_id_usuario ID do usuario
     * @param p_status Filtro de status (ATIVO/COMPRADO) - NULL para todos
     * @return Cursor com presentes
     */
    FUNCTION LISTAR_MEUS_PRESENTES(
        p_id_usuario        IN NUMBER,
        p_status            IN VARCHAR2 DEFAULT NULL
    ) RETURN t_cursor;

    /**
     * Lista presentes de outros usuarios (ativos)
     * @param p_id_usuario_excluir ID do usuario a excluir
     * @param p_preco_min Filtro de preco minimo (opcional)
     * @param p_preco_max Filtro de preco maximo (opcional)
     * @return Cursor com presentes
     */
    FUNCTION LISTAR_PRESENTES_OUTROS(
        p_id_usuario_excluir IN NUMBER,
        p_preco_min          IN NUMBER DEFAULT NULL,
        p_preco_max          IN NUMBER DEFAULT NULL
    ) RETURN t_cursor;

    /**
     * Lista presentes de um usuario especifico
     * @param p_id_usuario_dono ID do usuario dono dos presentes
     * @param p_id_usuario_visualizador ID do usuario que esta visualizando
     * @return Cursor com presentes
     */
    FUNCTION LISTAR_PRESENTES_USUARIO(
        p_id_usuario_dono           IN NUMBER,
        p_id_usuario_visualizador   IN NUMBER
    ) RETURN t_cursor;

    /**
     * Busca imagem do presente em base64
     * @param p_id_presente ID do presente
     * @return CLOB com imagem em base64
     */
    FUNCTION OBTER_IMAGEM_BASE64(
        p_id_presente       IN NUMBER
    ) RETURN CLOB;

    /**
     * Conta presentes do usuario por status
     * @param p_id_usuario ID do usuario
     * @param p_status Status (ATIVO/COMPRADO)
     * @return Quantidade de presentes
     */
    FUNCTION CONTAR_PRESENTES(
        p_id_usuario        IN NUMBER,
        p_status            IN VARCHAR2 DEFAULT NULL
    ) RETURN NUMBER;

    /**
     * Verifica se usuario e dono do presente
     * @param p_id_presente ID do presente
     * @param p_id_usuario ID do usuario
     * @return TRUE se dono, FALSE caso contrario
     */
    FUNCTION IS_DONO_PRESENTE(
        p_id_presente       IN NUMBER,
        p_id_usuario        IN NUMBER
    ) RETURN BOOLEAN;

    /**
     * Obtem estatisticas do presente
     * @param p_id_presente ID do presente
     * @return Cursor com estatisticas
     */
    FUNCTION OBTER_ESTATISTICAS(
        p_id_presente       IN NUMBER
    ) RETURN t_cursor;

    /**
     * Marca presente como comprado
     * IMPORTANTE: Esta funcao esta no PKG_COMPRA
     * Esta aqui apenas como referencia
     */
    -- FUNCTION MARCAR_COMPRADO(...) -> Ver PKG_COMPRA

END PKG_PRESENTE;
/


-- ==============================================================================
-- BODY
-- ==============================================================================
CREATE OR REPLACE PACKAGE BODY PKG_PRESENTE AS

    -- ============================================================================
    -- ADICIONAR_PRESENTE
    -- ============================================================================
    FUNCTION ADICIONAR_PRESENTE(
        p_id_usuario        IN NUMBER,
        p_descricao         IN CLOB,
        p_url               IN VARCHAR2 DEFAULT NULL,
        p_preco             IN NUMBER DEFAULT NULL,
        p_imagem_base64     IN CLOB DEFAULT NULL,
        p_imagem_nome       IN VARCHAR2 DEFAULT NULL,
        p_imagem_tipo       IN VARCHAR2 DEFAULT NULL
    ) RETURN NUMBER IS
        v_id_presente       NUMBER;
    BEGIN
        -- Validar se usuario existe e esta ativo
        DECLARE
            v_ativo CHAR(1);
        BEGIN
            SELECT ATIVO INTO v_ativo
            FROM TB_USUARIO
            WHERE ID_USUARIO = p_id_usuario;

            IF v_ativo = 'N' THEN
                RAISE_APPLICATION_ERROR(-20105, 'Usuario inativo');
            END IF;
        EXCEPTION
            WHEN NO_DATA_FOUND THEN
                RAISE_APPLICATION_ERROR(-20001, 'Usuario nao encontrado');
        END;

        -- Inserir presente
        INSERT INTO TB_PRESENTE (
            ID_PRESENTE,
            ID_USUARIO,
            DESCRICAO,
            URL,
            PRECO,
            STATUS,
            IMAGEM_BASE64,
            IMAGEM_NOME,
            IMAGEM_TIPO,
            DATA_CADASTRO,
            DATA_ALTERACAO
        ) VALUES (
            SEQ_PRESENTE.NEXTVAL,
            p_id_usuario,
            p_descricao,
            p_url,
            p_preco,
            'ATIVO',
            p_imagem_base64,
            p_imagem_nome,
            p_imagem_tipo,
            SYSDATE,
            SYSDATE
        ) RETURNING ID_PRESENTE INTO v_id_presente;

        COMMIT;

        RETURN v_id_presente;
    EXCEPTION
        WHEN OTHERS THEN
            ROLLBACK;
            RAISE;
    END ADICIONAR_PRESENTE;

    -- ============================================================================
    -- ATUALIZAR_PRESENTE
    -- ============================================================================
    PROCEDURE ATUALIZAR_PRESENTE(
        p_id_presente       IN NUMBER,
        p_id_usuario        IN NUMBER,
        p_descricao         IN CLOB DEFAULT NULL,
        p_url               IN VARCHAR2 DEFAULT NULL,
        p_preco             IN NUMBER DEFAULT NULL,
        p_imagem_base64     IN CLOB DEFAULT NULL,
        p_imagem_nome       IN VARCHAR2 DEFAULT NULL,
        p_imagem_tipo       IN VARCHAR2 DEFAULT NULL
    ) IS
        v_id_usuario_dono   NUMBER;
    BEGIN
        -- Verificar se presente existe e se usuario e dono
        BEGIN
            SELECT ID_USUARIO INTO v_id_usuario_dono
            FROM TB_PRESENTE
            WHERE ID_PRESENTE = p_id_presente;
        EXCEPTION
            WHEN NO_DATA_FOUND THEN
                RAISE EX_PRESENTE_NAO_ENCONTRADO;
        END;

        -- Validar propriedade
        IF v_id_usuario_dono != p_id_usuario THEN
            RAISE EX_USUARIO_NAO_AUTORIZADO;
        END IF;

        -- Atualizar apenas campos informados (não nulos)
        UPDATE TB_PRESENTE
        SET DESCRICAO = CASE WHEN p_descricao IS NOT NULL THEN p_descricao ELSE DESCRICAO END,
            URL = CASE WHEN p_url IS NOT NULL THEN p_url ELSE URL END,
            PRECO = CASE WHEN p_preco IS NOT NULL THEN p_preco ELSE PRECO END,
            IMAGEM_BASE64 = CASE WHEN p_imagem_base64 IS NOT NULL THEN p_imagem_base64 ELSE IMAGEM_BASE64 END,
            IMAGEM_NOME = CASE WHEN p_imagem_nome IS NOT NULL THEN p_imagem_nome ELSE IMAGEM_NOME END,
            IMAGEM_TIPO = CASE WHEN p_imagem_tipo IS NOT NULL THEN p_imagem_tipo ELSE IMAGEM_TIPO END,
            DATA_ALTERACAO = SYSDATE
        WHERE ID_PRESENTE = p_id_presente;

        COMMIT;
    EXCEPTION
        WHEN EX_PRESENTE_NAO_ENCONTRADO THEN
            RAISE_APPLICATION_ERROR(-20101, 'Presente nao encontrado');
        WHEN EX_USUARIO_NAO_AUTORIZADO THEN
            RAISE_APPLICATION_ERROR(-20102, 'Usuario nao autorizado para esta operacao');
        WHEN OTHERS THEN
            ROLLBACK;
            RAISE;
    END ATUALIZAR_PRESENTE;

    -- ============================================================================
    -- EXCLUIR_PRESENTE
    -- ============================================================================
    PROCEDURE EXCLUIR_PRESENTE(
        p_id_presente       IN NUMBER,
        p_id_usuario        IN NUMBER
    ) IS
        v_id_usuario_dono   NUMBER;
    BEGIN
        -- Verificar propriedade
        BEGIN
            SELECT ID_USUARIO INTO v_id_usuario_dono
            FROM TB_PRESENTE
            WHERE ID_PRESENTE = p_id_presente;
        EXCEPTION
            WHEN NO_DATA_FOUND THEN
                RAISE EX_PRESENTE_NAO_ENCONTRADO;
        END;

        IF v_id_usuario_dono != p_id_usuario THEN
            RAISE EX_USUARIO_NAO_AUTORIZADO;
        END IF;

        -- Excluir presente (CASCADE vai excluir sugestoes e compras)
        DELETE FROM TB_PRESENTE
        WHERE ID_PRESENTE = p_id_presente;

        COMMIT;
    EXCEPTION
        WHEN EX_PRESENTE_NAO_ENCONTRADO THEN
            RAISE_APPLICATION_ERROR(-20101, 'Presente nao encontrado');
        WHEN EX_USUARIO_NAO_AUTORIZADO THEN
            RAISE_APPLICATION_ERROR(-20102, 'Usuario nao autorizado para esta operacao');
        WHEN OTHERS THEN
            ROLLBACK;
            RAISE;
    END EXCLUIR_PRESENTE;

    -- ============================================================================
    -- BUSCAR_POR_ID
    -- ============================================================================
    FUNCTION BUSCAR_POR_ID(
        p_id_presente       IN NUMBER
    ) RETURN t_cursor IS
        v_cursor t_cursor;
    BEGIN
        OPEN v_cursor FOR
            SELECT
                p.ID_PRESENTE,
                p.ID_USUARIO,
                p.DESCRICAO,
                p.URL,
                p.PRECO,
                p.STATUS,
                p.DATA_CADASTRO,
                p.DATA_ALTERACAO,
                -- Dados do usuario
                u.EMAIL AS USUARIO_EMAIL,
                u.PRIMEIRO_NOME || ' ' || u.ULTIMO_NOME AS USUARIO_NOME,
                -- Indicador de imagem
                CASE WHEN p.IMAGEM_BASE64 IS NOT NULL THEN 'S' ELSE 'N' END AS TEM_IMAGEM,
                p.IMAGEM_NOME,
                p.IMAGEM_TIPO,
                -- Dados da compra (se houver)
                c.ID_COMPRA,
                c.DATA_COMPRA,
                c.ID_COMPRADOR,
                comp.PRIMEIRO_NOME || ' ' || comp.ULTIMO_NOME AS COMPRADOR_NOME
            FROM TB_PRESENTE p
            INNER JOIN TB_USUARIO u ON p.ID_USUARIO = u.ID_USUARIO
            LEFT JOIN TB_COMPRA c ON p.ID_PRESENTE = c.ID_PRESENTE
            LEFT JOIN TB_USUARIO comp ON c.ID_COMPRADOR = comp.ID_USUARIO
            WHERE p.ID_PRESENTE = p_id_presente;

        RETURN v_cursor;
    END BUSCAR_POR_ID;

    -- ============================================================================
    -- LISTAR_MEUS_PRESENTES
    -- ============================================================================
    FUNCTION LISTAR_MEUS_PRESENTES(
        p_id_usuario        IN NUMBER,
        p_status            IN VARCHAR2 DEFAULT NULL
    ) RETURN t_cursor IS
        v_cursor t_cursor;
    BEGIN
        OPEN v_cursor FOR
            SELECT
                p.ID_PRESENTE,
                p.DESCRICAO,
                p.URL,
                p.PRECO,
                p.STATUS,
                p.DATA_CADASTRO,
                CASE WHEN p.IMAGEM_BASE64 IS NOT NULL THEN 'S' ELSE 'N' END AS TEM_IMAGEM,
                -- Estatisticas
                (SELECT COUNT(*)
                 FROM TB_SUGESTAO_COMPRA s
                 WHERE s.ID_PRESENTE = p.ID_PRESENTE) AS TOTAL_SUGESTOES,
                (SELECT MIN(PRECO_SUGERIDO)
                 FROM TB_SUGESTAO_COMPRA s
                 WHERE s.ID_PRESENTE = p.ID_PRESENTE
                   AND PRECO_SUGERIDO IS NOT NULL) AS MELHOR_PRECO,
                -- Dados da compra
                c.DATA_COMPRA,
                comp.PRIMEIRO_NOME || ' ' || comp.ULTIMO_NOME AS COMPRADOR_NOME
            FROM TB_PRESENTE p
            LEFT JOIN TB_COMPRA c ON p.ID_PRESENTE = c.ID_PRESENTE
            LEFT JOIN TB_USUARIO comp ON c.ID_COMPRADOR = comp.ID_USUARIO
            WHERE p.ID_USUARIO = p_id_usuario
              AND (p_status IS NULL OR p.STATUS = p_status)
            ORDER BY p.DATA_CADASTRO DESC;

        RETURN v_cursor;
    END LISTAR_MEUS_PRESENTES;

    -- ============================================================================
    -- LISTAR_PRESENTES_OUTROS
    -- ============================================================================
    FUNCTION LISTAR_PRESENTES_OUTROS(
        p_id_usuario_excluir IN NUMBER,
        p_preco_min          IN NUMBER DEFAULT NULL,
        p_preco_max          IN NUMBER DEFAULT NULL
    ) RETURN t_cursor IS
        v_cursor t_cursor;
    BEGIN
        OPEN v_cursor FOR
            SELECT
                p.ID_PRESENTE,
                p.DESCRICAO,
                p.URL,
                p.PRECO,
                p.DATA_CADASTRO,
                -- Usuario dono
                u.ID_USUARIO,
                u.PRIMEIRO_NOME || ' ' || u.ULTIMO_NOME AS USUARIO_NOME,
                u.EMAIL AS USUARIO_EMAIL,
                -- Imagem
                CASE WHEN p.IMAGEM_BASE64 IS NOT NULL THEN 'S' ELSE 'N' END AS TEM_IMAGEM,
                -- Estatisticas
                (SELECT COUNT(*)
                 FROM TB_SUGESTAO_COMPRA s
                 WHERE s.ID_PRESENTE = p.ID_PRESENTE) AS TOTAL_SUGESTOES,
                (SELECT MIN(PRECO_SUGERIDO)
                 FROM TB_SUGESTAO_COMPRA s
                 WHERE s.ID_PRESENTE = p.ID_PRESENTE
                   AND PRECO_SUGERIDO IS NOT NULL) AS MELHOR_PRECO
            FROM TB_PRESENTE p
            INNER JOIN TB_USUARIO u ON p.ID_USUARIO = u.ID_USUARIO
            WHERE p.STATUS = 'ATIVO'
              AND u.ATIVO = 'S'
              AND p.ID_USUARIO != p_id_usuario_excluir
              AND (p_preco_min IS NULL OR p.PRECO >= p_preco_min OR
                   (SELECT MIN(PRECO_SUGERIDO)
                    FROM TB_SUGESTAO_COMPRA s
                    WHERE s.ID_PRESENTE = p.ID_PRESENTE) >= p_preco_min)
              AND (p_preco_max IS NULL OR p.PRECO <= p_preco_max OR
                   (SELECT MIN(PRECO_SUGERIDO)
                    FROM TB_SUGESTAO_COMPRA s
                    WHERE s.ID_PRESENTE = p.ID_PRESENTE) <= p_preco_max)
            ORDER BY p.DATA_CADASTRO DESC;

        RETURN v_cursor;
    END LISTAR_PRESENTES_OUTROS;

    -- ============================================================================
    -- LISTAR_PRESENTES_USUARIO
    -- ============================================================================
    FUNCTION LISTAR_PRESENTES_USUARIO(
        p_id_usuario_dono           IN NUMBER,
        p_id_usuario_visualizador   IN NUMBER
    ) RETURN t_cursor IS
        v_cursor t_cursor;
    BEGIN
        OPEN v_cursor FOR
            SELECT
                p.ID_PRESENTE,
                p.DESCRICAO,
                p.URL,
                p.PRECO,
                p.STATUS,
                p.DATA_CADASTRO,
                -- Usuario
                u.PRIMEIRO_NOME || ' ' || u.ULTIMO_NOME AS USUARIO_NOME,
                -- Imagem
                CASE WHEN p.IMAGEM_BASE64 IS NOT NULL THEN 'S' ELSE 'N' END AS TEM_IMAGEM,
                -- Estatisticas
                (SELECT COUNT(*)
                 FROM TB_SUGESTAO_COMPRA s
                 WHERE s.ID_PRESENTE = p.ID_PRESENTE) AS TOTAL_SUGESTOES,
                (SELECT MIN(PRECO_SUGERIDO)
                 FROM TB_SUGESTAO_COMPRA s
                 WHERE s.ID_PRESENTE = p.ID_PRESENTE
                   AND PRECO_SUGERIDO IS NOT NULL) AS MELHOR_PRECO,
                -- Compra
                c.DATA_COMPRA,
                CASE
                    WHEN c.ID_COMPRADOR = p_id_usuario_visualizador THEN 'S'
                    ELSE 'N'
                END AS COMPRADO_POR_MIM
            FROM TB_PRESENTE p
            INNER JOIN TB_USUARIO u ON p.ID_USUARIO = u.ID_USUARIO
            LEFT JOIN TB_COMPRA c ON p.ID_PRESENTE = c.ID_PRESENTE
            WHERE p.ID_USUARIO = p_id_usuario_dono
            ORDER BY p.DATA_CADASTRO DESC;

        RETURN v_cursor;
    END LISTAR_PRESENTES_USUARIO;

    -- ============================================================================
    -- OBTER_IMAGEM_BASE64
    -- ============================================================================
    FUNCTION OBTER_IMAGEM_BASE64(
        p_id_presente       IN NUMBER
    ) RETURN CLOB IS
        v_imagem CLOB;
    BEGIN
        SELECT IMAGEM_BASE64 INTO v_imagem
        FROM TB_PRESENTE
        WHERE ID_PRESENTE = p_id_presente;

        RETURN v_imagem;
    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            RETURN NULL;
    END OBTER_IMAGEM_BASE64;

    -- ============================================================================
    -- CONTAR_PRESENTES
    -- ============================================================================
    FUNCTION CONTAR_PRESENTES(
        p_id_usuario        IN NUMBER,
        p_status            IN VARCHAR2 DEFAULT NULL
    ) RETURN NUMBER IS
        v_count NUMBER;
    BEGIN
        SELECT COUNT(*)
        INTO v_count
        FROM TB_PRESENTE
        WHERE ID_USUARIO = p_id_usuario
          AND (p_status IS NULL OR STATUS = p_status);

        RETURN v_count;
    END CONTAR_PRESENTES;

    -- ============================================================================
    -- IS_DONO_PRESENTE
    -- ============================================================================
    FUNCTION IS_DONO_PRESENTE(
        p_id_presente       IN NUMBER,
        p_id_usuario        IN NUMBER
    ) RETURN BOOLEAN IS
        v_id_dono NUMBER;
    BEGIN
        SELECT ID_USUARIO INTO v_id_dono
        FROM TB_PRESENTE
        WHERE ID_PRESENTE = p_id_presente;

        RETURN v_id_dono = p_id_usuario;
    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            RETURN FALSE;
    END IS_DONO_PRESENTE;

    -- ============================================================================
    -- OBTER_ESTATISTICAS
    -- ============================================================================
    FUNCTION OBTER_ESTATISTICAS(
        p_id_presente       IN NUMBER
    ) RETURN t_cursor IS
        v_cursor t_cursor;
    BEGIN
        OPEN v_cursor FOR
            SELECT
                p.ID_PRESENTE,
                p.STATUS,
                (SELECT COUNT(*)
                 FROM TB_SUGESTAO_COMPRA s
                 WHERE s.ID_PRESENTE = p.ID_PRESENTE) AS TOTAL_SUGESTOES,
                (SELECT MIN(PRECO_SUGERIDO)
                 FROM TB_SUGESTAO_COMPRA s
                 WHERE s.ID_PRESENTE = p.ID_PRESENTE
                   AND PRECO_SUGERIDO IS NOT NULL) AS MELHOR_PRECO,
                (SELECT MAX(PRECO_SUGERIDO)
                 FROM TB_SUGESTAO_COMPRA s
                 WHERE s.ID_PRESENTE = p.ID_PRESENTE
                   AND PRECO_SUGERIDO IS NOT NULL) AS PIOR_PRECO,
                (SELECT AVG(PRECO_SUGERIDO)
                 FROM TB_SUGESTAO_COMPRA s
                 WHERE s.ID_PRESENTE = p.ID_PRESENTE
                   AND PRECO_SUGERIDO IS NOT NULL) AS PRECO_MEDIO
            FROM TB_PRESENTE p
            WHERE ID_PRESENTE = p_id_presente;

        RETURN v_cursor;
    END OBTER_ESTATISTICAS;

END PKG_PRESENTE;
/
