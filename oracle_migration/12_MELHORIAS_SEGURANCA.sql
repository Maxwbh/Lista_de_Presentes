-- ==============================================================================
-- MELHORIAS DE SEGURANCA
-- Gestao de sessao, reset de senha, rate limiting e auditoria
-- Desenvolvedor: Maxwell da Silva Oliveira (@maxwbh)
-- Email: maxwbh@gmail.com
-- Empresa: M&S do Brasil LTDA - msbrasil.inf.br
-- Data: 2025-11-22
-- ==============================================================================

-- ==============================================================================
-- TABELAS DE SUPORTE
-- ==============================================================================

-- Tabela de sessoes de usuario
CREATE TABLE LCP_SESSAO (
    ID                  NUMBER PRIMARY KEY,
    ID_USUARIO          NUMBER NOT NULL,
    TOKEN_SESSAO        VARCHAR2(100) NOT NULL,
    IP_ADDRESS          VARCHAR2(50),
    USER_AGENT          VARCHAR2(500),
    DATA_LOGIN          TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL,
    ULTIMA_ATIVIDADE    TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL,
    DATA_LOGOUT         TIMESTAMP,
    DATA_EXPIRACAO      TIMESTAMP NOT NULL,
    ATIVO               CHAR(1) DEFAULT 'S' CHECK (ATIVO IN ('S', 'N')),
    CONSTRAINT FK_SESSAO_USUARIO FOREIGN KEY (ID_USUARIO)
        REFERENCES LCP_USUARIO(ID) ON DELETE CASCADE,
    CONSTRAINT UK_SESSAO_TOKEN UNIQUE (TOKEN_SESSAO)
);

CREATE SEQUENCE SEQ_LCP_SESSAO START WITH 1 INCREMENT BY 1;

-- Tabela de reset de senha
CREATE TABLE LCP_RESET_SENHA (
    ID                  NUMBER PRIMARY KEY,
    ID_USUARIO          NUMBER NOT NULL,
    TOKEN_RESET         VARCHAR2(100) NOT NULL,
    DATA_CRIACAO        TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL,
    DATA_EXPIRACAO      TIMESTAMP NOT NULL,
    USADO               CHAR(1) DEFAULT 'N' CHECK (USADO IN ('S', 'N')),
    DATA_USO            TIMESTAMP,
    IP_SOLICITACAO      VARCHAR2(50),
    CONSTRAINT FK_RESET_USUARIO FOREIGN KEY (ID_USUARIO)
        REFERENCES LCP_USUARIO(ID) ON DELETE CASCADE,
    CONSTRAINT UK_RESET_TOKEN UNIQUE (TOKEN_RESET)
);

CREATE SEQUENCE SEQ_LCP_RESET_SENHA START WITH 1 INCREMENT BY 1;

-- Tabela de rate limiting
CREATE TABLE LCP_RATE_LIMIT (
    ID                  NUMBER PRIMARY KEY,
    IDENTIFICADOR       VARCHAR2(200) NOT NULL,  -- IP ou USER_ID
    ENDPOINT            VARCHAR2(100) NOT NULL,
    CONTADOR            NUMBER DEFAULT 1,
    JANELA_INICIO       TIMESTAMP NOT NULL,
    CONSTRAINT UK_RATE_LIMIT UNIQUE (IDENTIFICADOR, ENDPOINT, JANELA_INICIO)
);

CREATE SEQUENCE SEQ_LCP_RATE_LIMIT START WITH 1 INCREMENT BY 1;

-- Tabela de log de jobs
CREATE TABLE LCP_JOB_LOG (
    ID                  NUMBER PRIMARY KEY,
    NOME_JOB            VARCHAR2(100) NOT NULL,
    DATA_INICIO         TIMESTAMP NOT NULL,
    DATA_FIM            TIMESTAMP,
    STATUS              VARCHAR2(20) CHECK (STATUS IN ('EXECUTANDO', 'SUCESSO', 'ERRO', 'TIMEOUT')),
    MENSAGEM_ERRO       CLOB,
    REGISTROS_PROCESSADOS NUMBER DEFAULT 0
);

CREATE SEQUENCE SEQ_LCP_JOB_LOG START WITH 1 INCREMENT BY 1;

-- Tabela de configuracoes da aplicacao
CREATE TABLE LCP_CONFIG (
    CHAVE               VARCHAR2(100) PRIMARY KEY,
    VALOR               VARCHAR2(4000),
    DESCRICAO           VARCHAR2(500),
    DATA_ALTERACAO      TIMESTAMP DEFAULT SYSTIMESTAMP
);

-- Inserir configuracao VAPID
INSERT INTO LCP_CONFIG (CHAVE, VALOR, DESCRICAO) VALUES (
    'VAPID_PUBLIC_KEY',
    NULL,  -- Sera configurado pelo administrador
    'Chave publica VAPID para Push Notifications'
);

INSERT INTO LCP_CONFIG (CHAVE, VALOR, DESCRICAO) VALUES (
    'SESSAO_TIMEOUT_HORAS',
    '8',
    'Tempo em horas para expiracao da sessao'
);

INSERT INTO LCP_CONFIG (CHAVE, VALOR, DESCRICAO) VALUES (
    'RESET_SENHA_TIMEOUT_MINUTOS',
    '60',
    'Tempo em minutos para expiracao do token de reset'
);

INSERT INTO LCP_CONFIG (CHAVE, VALOR, DESCRICAO) VALUES (
    'RATE_LIMIT_REQUESTS',
    '100',
    'Numero maximo de requests por minuto'
);

COMMIT;

-- ==============================================================================
-- TRIGGERS PARA AUTO-INCREMENT
-- ==============================================================================

CREATE OR REPLACE TRIGGER TRG_LCP_SESSAO_BI
BEFORE INSERT ON LCP_SESSAO
FOR EACH ROW
BEGIN
    IF :NEW.ID IS NULL THEN
        :NEW.ID := SEQ_LCP_SESSAO.NEXTVAL;
    END IF;
END;
/

CREATE OR REPLACE TRIGGER TRG_LCP_RESET_SENHA_BI
BEFORE INSERT ON LCP_RESET_SENHA
FOR EACH ROW
BEGIN
    IF :NEW.ID IS NULL THEN
        :NEW.ID := SEQ_LCP_RESET_SENHA.NEXTVAL;
    END IF;
END;
/

CREATE OR REPLACE TRIGGER TRG_LCP_RATE_LIMIT_BI
BEFORE INSERT ON LCP_RATE_LIMIT
FOR EACH ROW
BEGIN
    IF :NEW.ID IS NULL THEN
        :NEW.ID := SEQ_LCP_RATE_LIMIT.NEXTVAL;
    END IF;
END;
/

CREATE OR REPLACE TRIGGER TRG_LCP_JOB_LOG_BI
BEFORE INSERT ON LCP_JOB_LOG
FOR EACH ROW
BEGIN
    IF :NEW.ID IS NULL THEN
        :NEW.ID := SEQ_LCP_JOB_LOG.NEXTVAL;
    END IF;
END;
/

-- ==============================================================================
-- PACKAGE: PKG_SESSAO
-- Gerenciamento de sessoes de usuario
-- ==============================================================================

CREATE OR REPLACE PACKAGE PKG_SESSAO AS

    -- Tipos
    TYPE t_cursor IS REF CURSOR;

    /**
     * Cria nova sessao para usuario
     * @param p_id_usuario ID do usuario
     * @param p_ip_address IP do cliente
     * @param p_user_agent User Agent do navegador
     * @return Token da sessao
     */
    FUNCTION CRIAR_SESSAO(
        p_id_usuario    IN NUMBER,
        p_ip_address    IN VARCHAR2 DEFAULT NULL,
        p_user_agent    IN VARCHAR2 DEFAULT NULL
    ) RETURN VARCHAR2;

    /**
     * Valida sessao existente
     * @param p_token Token da sessao
     * @return ID do usuario se valido, NULL se invalido
     */
    FUNCTION VALIDAR_SESSAO(
        p_token         IN VARCHAR2
    ) RETURN NUMBER;

    /**
     * Atualiza ultima atividade da sessao
     * @param p_token Token da sessao
     */
    PROCEDURE ATUALIZAR_ATIVIDADE(
        p_token         IN VARCHAR2
    );

    /**
     * Encerra sessao (logout)
     * @param p_token Token da sessao
     */
    PROCEDURE ENCERRAR_SESSAO(
        p_token         IN VARCHAR2
    );

    /**
     * Encerra todas sessoes do usuario
     * @param p_id_usuario ID do usuario
     */
    PROCEDURE ENCERRAR_TODAS_SESSOES(
        p_id_usuario    IN NUMBER
    );

    /**
     * Lista sessoes ativas do usuario
     * @param p_id_usuario ID do usuario
     * @return Cursor com sessoes
     */
    FUNCTION LISTAR_SESSOES(
        p_id_usuario    IN NUMBER
    ) RETURN t_cursor;

    /**
     * Limpa sessoes expiradas (job)
     * @return Quantidade de sessoes removidas
     */
    FUNCTION LIMPAR_SESSOES_EXPIRADAS RETURN NUMBER;

END PKG_SESSAO;
/

CREATE OR REPLACE PACKAGE BODY PKG_SESSAO AS

    -- ============================================================================
    -- CRIAR_SESSAO
    -- ============================================================================
    FUNCTION CRIAR_SESSAO(
        p_id_usuario    IN NUMBER,
        p_ip_address    IN VARCHAR2 DEFAULT NULL,
        p_user_agent    IN VARCHAR2 DEFAULT NULL
    ) RETURN VARCHAR2 IS
        v_token         VARCHAR2(100);
        v_timeout       NUMBER;
    BEGIN
        -- Gerar token unico
        v_token := RAWTOHEX(DBMS_CRYPTO.RANDOMBYTES(32));

        -- Obter timeout de configuracao
        BEGIN
            SELECT TO_NUMBER(VALOR) INTO v_timeout
            FROM LCP_CONFIG
            WHERE CHAVE = 'SESSAO_TIMEOUT_HORAS';
        EXCEPTION
            WHEN OTHERS THEN
                v_timeout := 8; -- Default 8 horas
        END;

        -- Inserir sessao
        INSERT INTO LCP_SESSAO (
            ID_USUARIO,
            TOKEN_SESSAO,
            IP_ADDRESS,
            USER_AGENT,
            DATA_LOGIN,
            ULTIMA_ATIVIDADE,
            DATA_EXPIRACAO,
            ATIVO
        ) VALUES (
            p_id_usuario,
            v_token,
            p_ip_address,
            SUBSTR(p_user_agent, 1, 500),
            SYSTIMESTAMP,
            SYSTIMESTAMP,
            SYSTIMESTAMP + NUMTODSINTERVAL(v_timeout, 'HOUR'),
            'S'
        );

        COMMIT;
        RETURN v_token;
    END CRIAR_SESSAO;

    -- ============================================================================
    -- VALIDAR_SESSAO
    -- ============================================================================
    FUNCTION VALIDAR_SESSAO(
        p_token         IN VARCHAR2
    ) RETURN NUMBER IS
        v_id_usuario    NUMBER;
    BEGIN
        SELECT ID_USUARIO INTO v_id_usuario
        FROM LCP_SESSAO
        WHERE TOKEN_SESSAO = p_token
          AND ATIVO = 'S'
          AND DATA_EXPIRACAO > SYSTIMESTAMP
          AND DATA_LOGOUT IS NULL;

        -- Atualizar ultima atividade
        UPDATE LCP_SESSAO
        SET ULTIMA_ATIVIDADE = SYSTIMESTAMP
        WHERE TOKEN_SESSAO = p_token;

        COMMIT;
        RETURN v_id_usuario;
    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            RETURN NULL;
    END VALIDAR_SESSAO;

    -- ============================================================================
    -- ATUALIZAR_ATIVIDADE
    -- ============================================================================
    PROCEDURE ATUALIZAR_ATIVIDADE(
        p_token         IN VARCHAR2
    ) IS
    BEGIN
        UPDATE LCP_SESSAO
        SET ULTIMA_ATIVIDADE = SYSTIMESTAMP
        WHERE TOKEN_SESSAO = p_token
          AND ATIVO = 'S';
        COMMIT;
    END ATUALIZAR_ATIVIDADE;

    -- ============================================================================
    -- ENCERRAR_SESSAO
    -- ============================================================================
    PROCEDURE ENCERRAR_SESSAO(
        p_token         IN VARCHAR2
    ) IS
    BEGIN
        UPDATE LCP_SESSAO
        SET DATA_LOGOUT = SYSTIMESTAMP,
            ATIVO = 'N'
        WHERE TOKEN_SESSAO = p_token;
        COMMIT;
    END ENCERRAR_SESSAO;

    -- ============================================================================
    -- ENCERRAR_TODAS_SESSOES
    -- ============================================================================
    PROCEDURE ENCERRAR_TODAS_SESSOES(
        p_id_usuario    IN NUMBER
    ) IS
    BEGIN
        UPDATE LCP_SESSAO
        SET DATA_LOGOUT = SYSTIMESTAMP,
            ATIVO = 'N'
        WHERE ID_USUARIO = p_id_usuario
          AND ATIVO = 'S';
        COMMIT;
    END ENCERRAR_TODAS_SESSOES;

    -- ============================================================================
    -- LISTAR_SESSOES
    -- ============================================================================
    FUNCTION LISTAR_SESSOES(
        p_id_usuario    IN NUMBER
    ) RETURN t_cursor IS
        v_cursor t_cursor;
    BEGIN
        OPEN v_cursor FOR
            SELECT ID, TOKEN_SESSAO, IP_ADDRESS, USER_AGENT,
                   DATA_LOGIN, ULTIMA_ATIVIDADE, DATA_EXPIRACAO
            FROM LCP_SESSAO
            WHERE ID_USUARIO = p_id_usuario
              AND ATIVO = 'S'
              AND DATA_EXPIRACAO > SYSTIMESTAMP
            ORDER BY ULTIMA_ATIVIDADE DESC;
        RETURN v_cursor;
    END LISTAR_SESSOES;

    -- ============================================================================
    -- LIMPAR_SESSOES_EXPIRADAS
    -- ============================================================================
    FUNCTION LIMPAR_SESSOES_EXPIRADAS RETURN NUMBER IS
        v_count NUMBER;
    BEGIN
        DELETE FROM LCP_SESSAO
        WHERE DATA_EXPIRACAO < SYSTIMESTAMP
           OR (ATIVO = 'N' AND DATA_LOGOUT < SYSTIMESTAMP - 30);

        v_count := SQL%ROWCOUNT;
        COMMIT;
        RETURN v_count;
    END LIMPAR_SESSOES_EXPIRADAS;

END PKG_SESSAO;
/

-- ==============================================================================
-- PACKAGE: PKG_RESET_SENHA
-- Gerenciamento de reset de senha
-- ==============================================================================

CREATE OR REPLACE PACKAGE PKG_RESET_SENHA AS

    /**
     * Solicita reset de senha
     * @param p_email Email do usuario
     * @param p_ip_address IP do solicitante
     * @return Token de reset (para enviar por email)
     */
    FUNCTION SOLICITAR_RESET(
        p_email         IN VARCHAR2,
        p_ip_address    IN VARCHAR2 DEFAULT NULL
    ) RETURN VARCHAR2;

    /**
     * Valida token de reset
     * @param p_token Token de reset
     * @return ID do usuario se valido, NULL se invalido
     */
    FUNCTION VALIDAR_TOKEN(
        p_token         IN VARCHAR2
    ) RETURN NUMBER;

    /**
     * Executa reset de senha
     * @param p_token Token de reset
     * @param p_nova_senha Nova senha
     */
    PROCEDURE EXECUTAR_RESET(
        p_token         IN VARCHAR2,
        p_nova_senha    IN VARCHAR2
    );

    /**
     * Limpa tokens expirados
     * @return Quantidade removida
     */
    FUNCTION LIMPAR_TOKENS_EXPIRADOS RETURN NUMBER;

END PKG_RESET_SENHA;
/

CREATE OR REPLACE PACKAGE BODY PKG_RESET_SENHA AS

    -- ============================================================================
    -- SOLICITAR_RESET
    -- ============================================================================
    FUNCTION SOLICITAR_RESET(
        p_email         IN VARCHAR2,
        p_ip_address    IN VARCHAR2 DEFAULT NULL
    ) RETURN VARCHAR2 IS
        v_id_usuario    NUMBER;
        v_token         VARCHAR2(100);
        v_timeout       NUMBER;
    BEGIN
        -- Buscar usuario pelo email
        BEGIN
            SELECT ID INTO v_id_usuario
            FROM LCP_USUARIO
            WHERE UPPER(EMAIL) = UPPER(TRIM(p_email))
              AND ATIVO = 'S';
        EXCEPTION
            WHEN NO_DATA_FOUND THEN
                -- Por seguranca, nao informar se email existe ou nao
                -- Retornar NULL silenciosamente
                RETURN NULL;
        END;

        -- Invalidar tokens anteriores
        UPDATE LCP_RESET_SENHA
        SET USADO = 'S',
            DATA_USO = SYSTIMESTAMP
        WHERE ID_USUARIO = v_id_usuario
          AND USADO = 'N';

        -- Gerar novo token
        v_token := RAWTOHEX(DBMS_CRYPTO.RANDOMBYTES(32));

        -- Obter timeout de configuracao
        BEGIN
            SELECT TO_NUMBER(VALOR) INTO v_timeout
            FROM LCP_CONFIG
            WHERE CHAVE = 'RESET_SENHA_TIMEOUT_MINUTOS';
        EXCEPTION
            WHEN OTHERS THEN
                v_timeout := 60; -- Default 60 minutos
        END;

        -- Inserir token
        INSERT INTO LCP_RESET_SENHA (
            ID_USUARIO,
            TOKEN_RESET,
            DATA_CRIACAO,
            DATA_EXPIRACAO,
            IP_SOLICITACAO
        ) VALUES (
            v_id_usuario,
            v_token,
            SYSTIMESTAMP,
            SYSTIMESTAMP + NUMTODSINTERVAL(v_timeout, 'MINUTE'),
            p_ip_address
        );

        COMMIT;
        RETURN v_token;
    END SOLICITAR_RESET;

    -- ============================================================================
    -- VALIDAR_TOKEN
    -- ============================================================================
    FUNCTION VALIDAR_TOKEN(
        p_token         IN VARCHAR2
    ) RETURN NUMBER IS
        v_id_usuario    NUMBER;
    BEGIN
        SELECT ID_USUARIO INTO v_id_usuario
        FROM LCP_RESET_SENHA
        WHERE TOKEN_RESET = p_token
          AND USADO = 'N'
          AND DATA_EXPIRACAO > SYSTIMESTAMP;

        RETURN v_id_usuario;
    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            RETURN NULL;
    END VALIDAR_TOKEN;

    -- ============================================================================
    -- EXECUTAR_RESET
    -- ============================================================================
    PROCEDURE EXECUTAR_RESET(
        p_token         IN VARCHAR2,
        p_nova_senha    IN VARCHAR2
    ) IS
        v_id_usuario    NUMBER;
    BEGIN
        -- Validar token
        v_id_usuario := VALIDAR_TOKEN(p_token);

        IF v_id_usuario IS NULL THEN
            RAISE_APPLICATION_ERROR(-20701, 'Token invalido ou expirado');
        END IF;

        -- Atualizar senha
        UPDATE LCP_USUARIO
        SET SENHA_HASH = PKG_USUARIO.HASH_SENHA(p_nova_senha),
            DATA_ALTERACAO = SYSDATE
        WHERE ID = v_id_usuario;

        -- Marcar token como usado
        UPDATE LCP_RESET_SENHA
        SET USADO = 'S',
            DATA_USO = SYSTIMESTAMP
        WHERE TOKEN_RESET = p_token;

        -- Encerrar todas as sessoes do usuario
        PKG_SESSAO.ENCERRAR_TODAS_SESSOES(v_id_usuario);

        -- Criar notificacao
        PKG_NOTIFICACAO.CRIAR_NOTIFICACAO(
            p_id_usuario => v_id_usuario,
            p_mensagem => 'Sua senha foi alterada com sucesso.'
        );

        COMMIT;
    END EXECUTAR_RESET;

    -- ============================================================================
    -- LIMPAR_TOKENS_EXPIRADOS
    -- ============================================================================
    FUNCTION LIMPAR_TOKENS_EXPIRADOS RETURN NUMBER IS
        v_count NUMBER;
    BEGIN
        DELETE FROM LCP_RESET_SENHA
        WHERE DATA_EXPIRACAO < SYSTIMESTAMP
           OR USADO = 'S';

        v_count := SQL%ROWCOUNT;
        COMMIT;
        RETURN v_count;
    END LIMPAR_TOKENS_EXPIRADOS;

END PKG_RESET_SENHA;
/

-- ==============================================================================
-- PACKAGE: PKG_RATE_LIMIT
-- Controle de rate limiting
-- ==============================================================================

CREATE OR REPLACE PACKAGE PKG_RATE_LIMIT AS

    /**
     * Verifica se request esta dentro do limite
     * @param p_identificador IP ou User ID
     * @param p_endpoint Nome do endpoint
     * @return TRUE se permitido, FALSE se bloqueado
     */
    FUNCTION VERIFICAR_LIMITE(
        p_identificador IN VARCHAR2,
        p_endpoint      IN VARCHAR2
    ) RETURN BOOLEAN;

    /**
     * Registra um request
     * @param p_identificador IP ou User ID
     * @param p_endpoint Nome do endpoint
     */
    PROCEDURE REGISTRAR_REQUEST(
        p_identificador IN VARCHAR2,
        p_endpoint      IN VARCHAR2
    );

    /**
     * Limpa registros antigos
     * @return Quantidade removida
     */
    FUNCTION LIMPAR_REGISTROS_ANTIGOS RETURN NUMBER;

END PKG_RATE_LIMIT;
/

CREATE OR REPLACE PACKAGE BODY PKG_RATE_LIMIT AS

    -- ============================================================================
    -- VERIFICAR_LIMITE
    -- ============================================================================
    FUNCTION VERIFICAR_LIMITE(
        p_identificador IN VARCHAR2,
        p_endpoint      IN VARCHAR2
    ) RETURN BOOLEAN IS
        v_count         NUMBER;
        v_max_requests  NUMBER;
        v_janela_inicio TIMESTAMP;
    BEGIN
        -- Obter limite de configuracao
        BEGIN
            SELECT TO_NUMBER(VALOR) INTO v_max_requests
            FROM LCP_CONFIG
            WHERE CHAVE = 'RATE_LIMIT_REQUESTS';
        EXCEPTION
            WHEN OTHERS THEN
                v_max_requests := 100; -- Default 100 requests
        END;

        -- Janela de 1 minuto
        v_janela_inicio := SYSTIMESTAMP - NUMTODSINTERVAL(1, 'MINUTE');

        -- Contar requests na janela
        SELECT NVL(SUM(CONTADOR), 0) INTO v_count
        FROM LCP_RATE_LIMIT
        WHERE IDENTIFICADOR = p_identificador
          AND ENDPOINT = p_endpoint
          AND JANELA_INICIO >= v_janela_inicio;

        RETURN v_count < v_max_requests;
    END VERIFICAR_LIMITE;

    -- ============================================================================
    -- REGISTRAR_REQUEST
    -- ============================================================================
    PROCEDURE REGISTRAR_REQUEST(
        p_identificador IN VARCHAR2,
        p_endpoint      IN VARCHAR2
    ) IS
        v_janela_inicio TIMESTAMP;
    BEGIN
        -- Truncar para minuto atual
        v_janela_inicio := TRUNC(SYSTIMESTAMP, 'MI');

        -- Tentar incrementar contador existente
        UPDATE LCP_RATE_LIMIT
        SET CONTADOR = CONTADOR + 1
        WHERE IDENTIFICADOR = p_identificador
          AND ENDPOINT = p_endpoint
          AND JANELA_INICIO = v_janela_inicio;

        -- Se nao existe, inserir novo
        IF SQL%ROWCOUNT = 0 THEN
            INSERT INTO LCP_RATE_LIMIT (
                IDENTIFICADOR, ENDPOINT, CONTADOR, JANELA_INICIO
            ) VALUES (
                p_identificador, p_endpoint, 1, v_janela_inicio
            );
        END IF;

        COMMIT;
    EXCEPTION
        WHEN DUP_VAL_ON_INDEX THEN
            -- Concorrencia: tentar update novamente
            UPDATE LCP_RATE_LIMIT
            SET CONTADOR = CONTADOR + 1
            WHERE IDENTIFICADOR = p_identificador
              AND ENDPOINT = p_endpoint
              AND JANELA_INICIO = v_janela_inicio;
            COMMIT;
    END REGISTRAR_REQUEST;

    -- ============================================================================
    -- LIMPAR_REGISTROS_ANTIGOS
    -- ============================================================================
    FUNCTION LIMPAR_REGISTROS_ANTIGOS RETURN NUMBER IS
        v_count NUMBER;
    BEGIN
        -- Remover registros com mais de 1 hora
        DELETE FROM LCP_RATE_LIMIT
        WHERE JANELA_INICIO < SYSTIMESTAMP - NUMTODSINTERVAL(1, 'HOUR');

        v_count := SQL%ROWCOUNT;
        COMMIT;
        RETURN v_count;
    END LIMPAR_REGISTROS_ANTIGOS;

END PKG_RATE_LIMIT;
/

-- ==============================================================================
-- FUNCOES APEX PARA CONFIG
-- ==============================================================================

/**
 * Retorna configuracao da aplicacao para o frontend
 * Usado pelo PWA para obter VAPID key
 */
CREATE OR REPLACE FUNCTION FN_APEX_GET_CONFIG(
    p_chave IN VARCHAR2
) RETURN VARCHAR2 IS
    v_valor VARCHAR2(4000);
BEGIN
    SELECT VALOR INTO v_valor
    FROM LCP_CONFIG
    WHERE CHAVE = p_chave;

    RETURN v_valor;
EXCEPTION
    WHEN NO_DATA_FOUND THEN
        RETURN NULL;
END FN_APEX_GET_CONFIG;
/

/**
 * Procedure APEX para retornar config PWA em JSON
 */
CREATE OR REPLACE PROCEDURE PRC_APEX_GET_PWA_CONFIG IS
    v_vapid_key VARCHAR2(4000);
BEGIN
    v_vapid_key := FN_APEX_GET_CONFIG('VAPID_PUBLIC_KEY');

    -- Retornar JSON
    HTP.P('{"vapidPublicKey":"' || NVL(v_vapid_key, '') || '"}');
EXCEPTION
    WHEN OTHERS THEN
        HTP.P('{"error":"' || SQLERRM || '"}');
END PRC_APEX_GET_PWA_CONFIG;
/

-- ==============================================================================
-- JOBS PARA LIMPEZA
-- ==============================================================================

-- Job para limpar sessoes expiradas (a cada hora)
BEGIN
    DBMS_SCHEDULER.CREATE_JOB(
        job_name        => 'JOB_LIMPAR_SESSOES',
        job_type        => 'PLSQL_BLOCK',
        job_action      => 'BEGIN PKG_SESSAO.LIMPAR_SESSOES_EXPIRADAS; END;',
        start_date      => SYSTIMESTAMP,
        repeat_interval => 'FREQ=HOURLY; INTERVAL=1',
        enabled         => FALSE,
        comments        => 'Limpa sessoes expiradas a cada hora'
    );
EXCEPTION
    WHEN OTHERS THEN
        IF SQLCODE != -27477 THEN RAISE; END IF;
END;
/

-- Job para limpar tokens de reset (a cada hora)
BEGIN
    DBMS_SCHEDULER.CREATE_JOB(
        job_name        => 'JOB_LIMPAR_RESET_TOKENS',
        job_type        => 'PLSQL_BLOCK',
        job_action      => 'BEGIN PKG_RESET_SENHA.LIMPAR_TOKENS_EXPIRADOS; END;',
        start_date      => SYSTIMESTAMP,
        repeat_interval => 'FREQ=HOURLY; INTERVAL=1',
        enabled         => FALSE,
        comments        => 'Limpa tokens de reset expirados a cada hora'
    );
EXCEPTION
    WHEN OTHERS THEN
        IF SQLCODE != -27477 THEN RAISE; END IF;
END;
/

-- Job para limpar rate limit (a cada hora)
BEGIN
    DBMS_SCHEDULER.CREATE_JOB(
        job_name        => 'JOB_LIMPAR_RATE_LIMIT',
        job_type        => 'PLSQL_BLOCK',
        job_action      => 'BEGIN PKG_RATE_LIMIT.LIMPAR_REGISTROS_ANTIGOS; END;',
        start_date      => SYSTIMESTAMP,
        repeat_interval => 'FREQ=HOURLY; INTERVAL=1',
        enabled         => FALSE,
        comments        => 'Limpa registros de rate limit antigos a cada hora'
    );
EXCEPTION
    WHEN OTHERS THEN
        IF SQLCODE != -27477 THEN RAISE; END IF;
END;
/

PROMPT Melhorias de seguranca instaladas com sucesso!
PROMPT Jobs criados (desabilitados por padrao). Para habilitar:
PROMPT   EXEC DBMS_SCHEDULER.ENABLE('JOB_LIMPAR_SESSOES');
PROMPT   EXEC DBMS_SCHEDULER.ENABLE('JOB_LIMPAR_RESET_TOKENS');
PROMPT   EXEC DBMS_SCHEDULER.ENABLE('JOB_LIMPAR_RATE_LIMIT');
