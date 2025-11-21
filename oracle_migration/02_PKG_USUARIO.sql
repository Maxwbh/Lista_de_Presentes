-- ==============================================================================
-- PACKAGE: PKG_USUARIO
-- Descricao: Gerenciamento de usuarios do sistema
-- Desenvolvedor: Maxwell da Silva Oliveira (@maxwbh)
-- Email: maxwbh@gmail.com
-- Empresa: M&S do Brasil LTDA - msbrasil.inf.br
-- Data: 2025-11-21
-- ==============================================================================

-- ==============================================================================
-- SPECIFICATION
-- ==============================================================================
CREATE OR REPLACE PACKAGE PKG_USUARIO AS

    -- Tipos de retorno
    TYPE t_cursor IS REF CURSOR;

    -- Record type para usuario
    TYPE t_usuario IS RECORD (
        id_usuario          LCP_USUARIO.ID%TYPE,
        username            LCP_USUARIO.USERNAME%TYPE,
        email               LCP_USUARIO.EMAIL%TYPE,
        primeiro_nome       LCP_USUARIO.PRIMEIRO_NOME%TYPE,
        ultimo_nome         LCP_USUARIO.ULTIMO_NOME%TYPE,
        telefone            LCP_USUARIO.TELEFONE%TYPE,
        ativo               LCP_USUARIO.ATIVO%TYPE,
        is_superuser        LCP_USUARIO.IS_SUPERUSER%TYPE,
        data_cadastro       LCP_USUARIO.DATA_CADASTRO%TYPE
    );

    -- Excecoes customizadas
    EX_USUARIO_NAO_ENCONTRADO   EXCEPTION;
    EX_EMAIL_DUPLICADO          EXCEPTION;
    EX_USERNAME_DUPLICADO       EXCEPTION;
    EX_SENHA_INVALIDA           EXCEPTION;
    EX_USUARIO_INATIVO          EXCEPTION;

    PRAGMA EXCEPTION_INIT(EX_USUARIO_NAO_ENCONTRADO, -20001);
    PRAGMA EXCEPTION_INIT(EX_EMAIL_DUPLICADO, -20002);
    PRAGMA EXCEPTION_INIT(EX_USERNAME_DUPLICADO, -20003);
    PRAGMA EXCEPTION_INIT(EX_SENHA_INVALIDA, -20004);
    PRAGMA EXCEPTION_INIT(EX_USUARIO_INATIVO, -20005);

    /**
     * Registra novo usuario no sistema
     * @param p_username Nome de usuario
     * @param p_email Email do usuario
     * @param p_senha Senha em texto plano (sera hasheada)
     * @param p_primeiro_nome Primeiro nome
     * @param p_ultimo_nome Ultimo nome
     * @param p_telefone Telefone (opcional)
     * @return ID do usuario criado
     */
    FUNCTION REGISTRAR_USUARIO(
        p_username          IN VARCHAR2,
        p_email             IN VARCHAR2,
        p_senha             IN VARCHAR2,
        p_primeiro_nome     IN VARCHAR2,
        p_ultimo_nome       IN VARCHAR2,
        p_telefone          IN VARCHAR2 DEFAULT NULL
    ) RETURN NUMBER;

    /**
     * Autentica usuario no sistema
     * @param p_email Email do usuario
     * @param p_senha Senha em texto plano
     * @return ID do usuario autenticado
     * @throws EX_USUARIO_NAO_ENCONTRADO Se usuario nao existe
     * @throws EX_SENHA_INVALIDA Se senha incorreta
     * @throws EX_USUARIO_INATIVO Se usuario esta inativo
     */
    FUNCTION AUTENTICAR_USUARIO(
        p_email             IN VARCHAR2,
        p_senha             IN VARCHAR2
    ) RETURN NUMBER;

    /**
     * Valida credenciais do usuario
     * @param p_id_usuario ID do usuario
     * @param p_senha Senha em texto plano
     * @return TRUE se senha valida, FALSE caso contrario
     */
    FUNCTION VALIDAR_SENHA(
        p_id_usuario        IN NUMBER,
        p_senha             IN VARCHAR2
    ) RETURN BOOLEAN;

    /**
     * Atualiza dados do usuario
     * @param p_id_usuario ID do usuario
     * @param p_primeiro_nome Primeiro nome (opcional)
     * @param p_ultimo_nome Ultimo nome (opcional)
     * @param p_telefone Telefone (opcional)
     * @param p_email Email (opcional)
     */
    PROCEDURE ATUALIZAR_USUARIO(
        p_id_usuario        IN NUMBER,
        p_primeiro_nome     IN VARCHAR2 DEFAULT NULL,
        p_ultimo_nome       IN VARCHAR2 DEFAULT NULL,
        p_telefone          IN VARCHAR2 DEFAULT NULL,
        p_email             IN VARCHAR2 DEFAULT NULL
    );

    /**
     * Altera senha do usuario
     * @param p_id_usuario ID do usuario
     * @param p_senha_atual Senha atual para validacao
     * @param p_senha_nova Nova senha
     */
    PROCEDURE ALTERAR_SENHA(
        p_id_usuario        IN NUMBER,
        p_senha_atual       IN VARCHAR2,
        p_senha_nova        IN VARCHAR2
    );

    /**
     * Ativa/Desativa usuario
     * @param p_id_usuario ID do usuario
     * @param p_ativo S ou N
     */
    PROCEDURE ALTERAR_STATUS(
        p_id_usuario        IN NUMBER,
        p_ativo             IN CHAR
    );

    /**
     * Busca usuario por ID
     * @param p_id_usuario ID do usuario
     * @return Record com dados do usuario
     */
    FUNCTION BUSCAR_POR_ID(
        p_id_usuario        IN NUMBER
    ) RETURN t_usuario;

    /**
     * Busca usuario por email
     * @param p_email Email do usuario
     * @return Record com dados do usuario
     */
    FUNCTION BUSCAR_POR_EMAIL(
        p_email             IN VARCHAR2
    ) RETURN t_usuario;

    /**
     * Lista todos usuarios ativos
     * @return Cursor com usuarios
     */
    FUNCTION LISTAR_USUARIOS_ATIVOS RETURN t_cursor;

    /**
     * Lista usuarios exceto o informado
     * @param p_id_usuario_excluir ID do usuario a excluir da lista
     * @return Cursor com usuarios
     */
    FUNCTION LISTAR_OUTROS_USUARIOS(
        p_id_usuario_excluir IN NUMBER
    ) RETURN t_cursor;

    /**
     * Verifica se usuario e administrador
     * @param p_id_usuario ID do usuario
     * @return TRUE se superuser, FALSE caso contrario
     */
    FUNCTION IS_SUPERUSER(
        p_id_usuario        IN NUMBER
    ) RETURN BOOLEAN;

    /**
     * Registra data/hora do ultimo login
     * @param p_id_usuario ID do usuario
     */
    PROCEDURE REGISTRAR_LOGIN(
        p_id_usuario        IN NUMBER
    );

    /**
     * Exclui usuario (soft delete - marca como inativo)
     * @param p_id_usuario ID do usuario
     */
    PROCEDURE EXCLUIR_USUARIO(
        p_id_usuario        IN NUMBER
    );

END PKG_USUARIO;
/


-- ==============================================================================
-- BODY
-- ==============================================================================
CREATE OR REPLACE PACKAGE BODY PKG_USUARIO AS

    /**
     * Funcao interna para hash de senha
     * Utiliza DBMS_CRYPTO para gerar hash SHA-256
     */
    FUNCTION HASH_SENHA(p_senha IN VARCHAR2) RETURN VARCHAR2 IS
        v_hash RAW(2000);
    BEGIN
        -- Usar SHA-256 para hash da senha
        v_hash := DBMS_CRYPTO.HASH(
            src => UTL_I18N.STRING_TO_RAW(p_senha, 'AL32UTF8'),
            typ => DBMS_CRYPTO.HASH_SH256
        );
        RETURN RAWTOHEX(v_hash);
    END HASH_SENHA;

    /**
     * Funcao interna para validar email
     */
    FUNCTION VALIDAR_EMAIL(p_email IN VARCHAR2) RETURN BOOLEAN IS
    BEGIN
        RETURN REGEXP_LIKE(p_email, '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');
    END VALIDAR_EMAIL;

    -- ============================================================================
    -- REGISTRAR_USUARIO
    -- ============================================================================
    FUNCTION REGISTRAR_USUARIO(
        p_username          IN VARCHAR2,
        p_email             IN VARCHAR2,
        p_senha             IN VARCHAR2,
        p_primeiro_nome     IN VARCHAR2,
        p_ultimo_nome       IN VARCHAR2,
        p_telefone          IN VARCHAR2 DEFAULT NULL
    ) RETURN NUMBER IS
        v_id_usuario        NUMBER;
        v_senha_hash        VARCHAR2(255);
        v_count             NUMBER;
    BEGIN
        -- Validar email
        IF NOT VALIDAR_EMAIL(p_email) THEN
            RAISE_APPLICATION_ERROR(-20010, 'Email invalido');
        END IF;

        -- Verificar email duplicado
        SELECT COUNT(*) INTO v_count
        FROM LCP_USUARIO
        WHERE UPPER(EMAIL) = UPPER(p_email);

        IF v_count > 0 THEN
            RAISE EX_EMAIL_DUPLICADO;
        END IF;

        -- Verificar username duplicado
        SELECT COUNT(*) INTO v_count
        FROM LCP_USUARIO
        WHERE UPPER(USERNAME) = UPPER(p_username);

        IF v_count > 0 THEN
            RAISE EX_USERNAME_DUPLICADO;
        END IF;

        -- Gerar hash da senha
        v_senha_hash := HASH_SENHA(p_senha);

        -- Inserir usuario
        INSERT INTO LCP_USUARIO (
            ID,
            USERNAME,
            EMAIL,
            SENHA_HASH,
            PRIMEIRO_NOME,
            ULTIMO_NOME,
            TELEFONE,
            ATIVO,
            IS_SUPERUSER,
            IS_STAFF,
            DATA_CADASTRO
        ) VALUES (
            SEQ_LCP_USUARIO.NEXTVAL,
            p_username,
            LOWER(p_email),
            v_senha_hash,
            p_primeiro_nome,
            p_ultimo_nome,
            p_telefone,
            'S',
            'N',
            'N',
            SYSDATE
        ) RETURNING ID INTO v_id_usuario;

        COMMIT;

        RETURN v_id_usuario;
    EXCEPTION
        WHEN EX_EMAIL_DUPLICADO THEN
            RAISE_APPLICATION_ERROR(-20002, 'Email ja cadastrado no sistema');
        WHEN EX_USERNAME_DUPLICADO THEN
            RAISE_APPLICATION_ERROR(-20003, 'Nome de usuario ja existe');
        WHEN OTHERS THEN
            ROLLBACK;
            RAISE;
    END REGISTRAR_USUARIO;

    -- ============================================================================
    -- AUTENTICAR_USUARIO
    -- ============================================================================
    FUNCTION AUTENTICAR_USUARIO(
        p_email             IN VARCHAR2,
        p_senha             IN VARCHAR2
    ) RETURN NUMBER IS
        v_id_usuario        NUMBER;
        v_senha_hash        VARCHAR2(255);
        v_ativo             CHAR(1);
        v_senha_hash_input  VARCHAR2(255);
    BEGIN
        -- Gerar hash da senha informada
        v_senha_hash_input := HASH_SENHA(p_senha);

        -- Buscar usuario
        BEGIN
            SELECT ID, SENHA_HASH, ATIVO
            INTO v_id_usuario, v_senha_hash, v_ativo
            FROM LCP_USUARIO
            WHERE UPPER(EMAIL) = UPPER(p_email);
        EXCEPTION
            WHEN NO_DATA_FOUND THEN
                RAISE EX_USUARIO_NAO_ENCONTRADO;
        END;

        -- Verificar se usuario esta ativo
        IF v_ativo = 'N' THEN
            RAISE EX_USUARIO_INATIVO;
        END IF;

        -- Validar senha
        IF v_senha_hash != v_senha_hash_input THEN
            RAISE EX_SENHA_INVALIDA;
        END IF;

        -- Registrar login
        REGISTRAR_LOGIN(v_id_usuario);

        RETURN v_id_usuario;
    EXCEPTION
        WHEN EX_USUARIO_NAO_ENCONTRADO THEN
            RAISE_APPLICATION_ERROR(-20001, 'Usuario nao encontrado');
        WHEN EX_SENHA_INVALIDA THEN
            RAISE_APPLICATION_ERROR(-20004, 'Senha invalida');
        WHEN EX_USUARIO_INATIVO THEN
            RAISE_APPLICATION_ERROR(-20005, 'Usuario inativo');
        WHEN OTHERS THEN
            RAISE;
    END AUTENTICAR_USUARIO;

    -- ============================================================================
    -- VALIDAR_SENHA
    -- ============================================================================
    FUNCTION VALIDAR_SENHA(
        p_id_usuario        IN NUMBER,
        p_senha             IN VARCHAR2
    ) RETURN BOOLEAN IS
        v_senha_hash        VARCHAR2(255);
        v_senha_hash_input  VARCHAR2(255);
    BEGIN
        -- Buscar hash armazenado
        SELECT SENHA_HASH INTO v_senha_hash
        FROM LCP_USUARIO
        WHERE ID = p_id_usuario;

        -- Gerar hash da senha informada
        v_senha_hash_input := HASH_SENHA(p_senha);

        -- Comparar
        RETURN v_senha_hash = v_senha_hash_input;
    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            RETURN FALSE;
    END VALIDAR_SENHA;

    -- ============================================================================
    -- ATUALIZAR_USUARIO
    -- ============================================================================
    PROCEDURE ATUALIZAR_USUARIO(
        p_id_usuario        IN NUMBER,
        p_primeiro_nome     IN VARCHAR2 DEFAULT NULL,
        p_ultimo_nome       IN VARCHAR2 DEFAULT NULL,
        p_telefone          IN VARCHAR2 DEFAULT NULL,
        p_email             IN VARCHAR2 DEFAULT NULL
    ) IS
        v_count NUMBER;
    BEGIN
        -- Verificar se usuario existe
        SELECT COUNT(*) INTO v_count
        FROM LCP_USUARIO
        WHERE ID = p_id_usuario;

        IF v_count = 0 THEN
            RAISE EX_USUARIO_NAO_ENCONTRADO;
        END IF;

        -- Atualizar campos informados
        UPDATE LCP_USUARIO
        SET PRIMEIRO_NOME = NVL(p_primeiro_nome, PRIMEIRO_NOME),
            ULTIMO_NOME = NVL(p_ultimo_nome, ULTIMO_NOME),
            TELEFONE = NVL(p_telefone, TELEFONE),
            EMAIL = NVL(LOWER(p_email), EMAIL),
            DATA_ALTERACAO = SYSDATE
        WHERE ID = p_id_usuario;

        COMMIT;
    EXCEPTION
        WHEN EX_USUARIO_NAO_ENCONTRADO THEN
            RAISE_APPLICATION_ERROR(-20001, 'Usuario nao encontrado');
        WHEN OTHERS THEN
            ROLLBACK;
            RAISE;
    END ATUALIZAR_USUARIO;

    -- ============================================================================
    -- ALTERAR_SENHA
    -- ============================================================================
    PROCEDURE ALTERAR_SENHA(
        p_id_usuario        IN NUMBER,
        p_senha_atual       IN VARCHAR2,
        p_senha_nova        IN VARCHAR2
    ) IS
        v_senha_valida      BOOLEAN;
        v_senha_hash_nova   VARCHAR2(255);
    BEGIN
        -- Validar senha atual
        v_senha_valida := VALIDAR_SENHA(p_id_usuario, p_senha_atual);

        IF NOT v_senha_valida THEN
            RAISE EX_SENHA_INVALIDA;
        END IF;

        -- Gerar hash da nova senha
        v_senha_hash_nova := HASH_SENHA(p_senha_nova);

        -- Atualizar senha
        UPDATE LCP_USUARIO
        SET SENHA_HASH = v_senha_hash_nova,
            DATA_ALTERACAO = SYSDATE
        WHERE ID = p_id_usuario;

        COMMIT;
    EXCEPTION
        WHEN EX_SENHA_INVALIDA THEN
            RAISE_APPLICATION_ERROR(-20004, 'Senha atual invalida');
        WHEN OTHERS THEN
            ROLLBACK;
            RAISE;
    END ALTERAR_SENHA;

    -- ============================================================================
    -- ALTERAR_STATUS
    -- ============================================================================
    PROCEDURE ALTERAR_STATUS(
        p_id_usuario        IN NUMBER,
        p_ativo             IN CHAR
    ) IS
    BEGIN
        UPDATE LCP_USUARIO
        SET ATIVO = p_ativo,
            DATA_ALTERACAO = SYSDATE
        WHERE ID = p_id_usuario;

        IF SQL%ROWCOUNT = 0 THEN
            RAISE EX_USUARIO_NAO_ENCONTRADO;
        END IF;

        COMMIT;
    EXCEPTION
        WHEN EX_USUARIO_NAO_ENCONTRADO THEN
            RAISE_APPLICATION_ERROR(-20001, 'Usuario nao encontrado');
        WHEN OTHERS THEN
            ROLLBACK;
            RAISE;
    END ALTERAR_STATUS;

    -- ============================================================================
    -- BUSCAR_POR_ID
    -- ============================================================================
    FUNCTION BUSCAR_POR_ID(
        p_id_usuario        IN NUMBER
    ) RETURN t_usuario IS
        v_usuario t_usuario;
    BEGIN
        SELECT ID, USERNAME, EMAIL, PRIMEIRO_NOME, ULTIMO_NOME,
               TELEFONE, ATIVO, IS_SUPERUSER, DATA_CADASTRO
        INTO v_usuario
        FROM LCP_USUARIO
        WHERE ID = p_id_usuario;

        RETURN v_usuario;
    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            RAISE_APPLICATION_ERROR(-20001, 'Usuario nao encontrado');
    END BUSCAR_POR_ID;

    -- ============================================================================
    -- BUSCAR_POR_EMAIL
    -- ============================================================================
    FUNCTION BUSCAR_POR_EMAIL(
        p_email             IN VARCHAR2
    ) RETURN t_usuario IS
        v_usuario t_usuario;
    BEGIN
        SELECT ID, USERNAME, EMAIL, PRIMEIRO_NOME, ULTIMO_NOME,
               TELEFONE, ATIVO, IS_SUPERUSER, DATA_CADASTRO
        INTO v_usuario
        FROM LCP_USUARIO
        WHERE UPPER(EMAIL) = UPPER(p_email);

        RETURN v_usuario;
    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            RAISE_APPLICATION_ERROR(-20001, 'Usuario nao encontrado');
    END BUSCAR_POR_EMAIL;

    -- ============================================================================
    -- LISTAR_USUARIOS_ATIVOS
    -- ============================================================================
    FUNCTION LISTAR_USUARIOS_ATIVOS RETURN t_cursor IS
        v_cursor t_cursor;
    BEGIN
        OPEN v_cursor FOR
            SELECT ID, USERNAME, EMAIL, PRIMEIRO_NOME, ULTIMO_NOME,
                   TELEFONE, ATIVO, IS_SUPERUSER, DATA_CADASTRO
            FROM LCP_USUARIO
            WHERE ATIVO = 'S'
            ORDER BY PRIMEIRO_NOME, ULTIMO_NOME;

        RETURN v_cursor;
    END LISTAR_USUARIOS_ATIVOS;

    -- ============================================================================
    -- LISTAR_OUTROS_USUARIOS
    -- ============================================================================
    FUNCTION LISTAR_OUTROS_USUARIOS(
        p_id_usuario_excluir IN NUMBER
    ) RETURN t_cursor IS
        v_cursor t_cursor;
    BEGIN
        OPEN v_cursor FOR
            SELECT ID, USERNAME, EMAIL, PRIMEIRO_NOME, ULTIMO_NOME,
                   TELEFONE, ATIVO, IS_SUPERUSER, DATA_CADASTRO
            FROM LCP_USUARIO
            WHERE ATIVO = 'S'
              AND ID != p_id_usuario_excluir
            ORDER BY PRIMEIRO_NOME, ULTIMO_NOME;

        RETURN v_cursor;
    END LISTAR_OUTROS_USUARIOS;

    -- ============================================================================
    -- IS_SUPERUSER
    -- ============================================================================
    FUNCTION IS_SUPERUSER(
        p_id_usuario        IN NUMBER
    ) RETURN BOOLEAN IS
        v_is_superuser CHAR(1);
    BEGIN
        SELECT IS_SUPERUSER INTO v_is_superuser
        FROM LCP_USUARIO
        WHERE ID = p_id_usuario;

        RETURN v_is_superuser = 'S';
    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            RETURN FALSE;
    END IS_SUPERUSER;

    -- ============================================================================
    -- REGISTRAR_LOGIN
    -- ============================================================================
    PROCEDURE REGISTRAR_LOGIN(
        p_id_usuario        IN NUMBER
    ) IS
    BEGIN
        UPDATE LCP_USUARIO
        SET DATA_LOGIN = SYSDATE
        WHERE ID = p_id_usuario;

        COMMIT;
    END REGISTRAR_LOGIN;

    -- ============================================================================
    -- EXCLUIR_USUARIO
    -- ============================================================================
    PROCEDURE EXCLUIR_USUARIO(
        p_id_usuario        IN NUMBER
    ) IS
    BEGIN
        -- Soft delete - apenas marca como inativo
        ALTERAR_STATUS(p_id_usuario, 'N');
    END EXCLUIR_USUARIO;

END PKG_USUARIO;
/
