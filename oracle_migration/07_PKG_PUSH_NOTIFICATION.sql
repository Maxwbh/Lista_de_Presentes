-- ==============================================================================
-- PACKAGE: PKG_PUSH_NOTIFICATION
-- Descricao: Gerenciamento de Push Notifications para APEX PWA
-- Desenvolvedor: Maxwell da Silva Oliveira (@maxwbh)
-- Email: maxwbh@gmail.com
-- Empresa: M&S do Brasil LTDA - msbrasil.inf.br
-- Data: 2025-11-21
-- ==============================================================================

-- ==============================================================================
-- TABELA: LCP_PUSH_SUBSCRIPTION
-- Descricao: Armazena subscricoes de push notification dos usuarios
-- ==============================================================================
CREATE TABLE LCP_PUSH_SUBSCRIPTION (
    ID                  NUMBER(10)      NOT NULL,
    ID_USUARIO          NUMBER(10)      NOT NULL,
    ENDPOINT            VARCHAR2(1000)  NOT NULL,
    P256DH_KEY          VARCHAR2(500),
    AUTH_KEY            VARCHAR2(500),
    USER_AGENT          VARCHAR2(500),
    IP_ADDRESS          VARCHAR2(50),
    ATIVO               CHAR(1)         DEFAULT 'S' NOT NULL,
    DATA_SUBSCRIPTION   DATE            DEFAULT SYSDATE NOT NULL,
    DATA_ULTIMO_ENVIO   DATE,
    TOTAL_ENVIADOS      NUMBER(10)      DEFAULT 0,
    TOTAL_ERROS         NUMBER(10)      DEFAULT 0,
    CONSTRAINT PK_PUSH_SUBSCRIPTION PRIMARY KEY (ID),
    CONSTRAINT FK_PUSH_SUBSCRIPTION_USR FOREIGN KEY (ID_USUARIO)
        REFERENCES LCP_USUARIO(ID) ON DELETE CASCADE,
    CONSTRAINT UK_PUSH_ENDPOINT UNIQUE (ENDPOINT),
    CONSTRAINT CK_PUSH_ATIVO CHECK (ATIVO IN ('S', 'N'))
);

-- Comentarios
COMMENT ON TABLE LCP_PUSH_SUBSCRIPTION IS 'Tabela de subscricoes de push notifications';
COMMENT ON COLUMN LCP_PUSH_SUBSCRIPTION.ENDPOINT IS 'URL do endpoint da subscription (FCM, APNS, etc)';
COMMENT ON COLUMN LCP_PUSH_SUBSCRIPTION.P256DH_KEY IS 'Chave publica P256DH para criptografia';
COMMENT ON COLUMN LCP_PUSH_SUBSCRIPTION.AUTH_KEY IS 'Chave de autenticacao';

-- Sequence
CREATE SEQUENCE SEQ_LCP_PUSH_SUBSCRIPTION START WITH 1 INCREMENT BY 1 NOCACHE;


-- ==============================================================================
-- TABELA: LCP_PUSH_LOG
-- Descricao: Log de envios de push notifications
-- ==============================================================================
CREATE TABLE LCP_PUSH_LOG (
    ID                  NUMBER(10)      NOT NULL,
    ID_SUBSCRIPTION     NUMBER(10)      NOT NULL,
    ID_NOTIFICACAO      NUMBER(10),
    TITULO              VARCHAR2(200),
    MENSAGEM            CLOB,
    STATUS              VARCHAR2(20)    NOT NULL,
    ERRO_MENSAGEM       CLOB,
    DATA_ENVIO          DATE            DEFAULT SYSDATE NOT NULL,
    CONSTRAINT PK_PUSH_LOG PRIMARY KEY (ID),
    CONSTRAINT FK_PUSH_LOG_SUBSCRIPTION FOREIGN KEY (ID_SUBSCRIPTION)
        REFERENCES LCP_PUSH_SUBSCRIPTION(ID) ON DELETE CASCADE,
    CONSTRAINT FK_PUSH_LOG_NOTIFICACAO FOREIGN KEY (ID_NOTIFICACAO)
        REFERENCES LCP_NOTIFICACAO(ID) ON DELETE SET NULL,
    CONSTRAINT CK_PUSH_LOG_STATUS CHECK (STATUS IN ('ENVIADO', 'ERRO', 'PENDENTE'))
);

-- Comentarios
COMMENT ON TABLE LCP_PUSH_LOG IS 'Log de envios de push notifications';
COMMENT ON COLUMN LCP_PUSH_LOG.STATUS IS 'Status do envio (ENVIADO/ERRO/PENDENTE)';

-- Sequence
CREATE SEQUENCE SEQ_LCP_PUSH_LOG START WITH 1 INCREMENT BY 1 NOCACHE;


-- ==============================================================================
-- PACKAGE SPECIFICATION
-- ==============================================================================
CREATE OR REPLACE PACKAGE PKG_PUSH_NOTIFICATION AS

    -- Tipos
    TYPE t_cursor IS REF CURSOR;

    -- Excecoes customizadas
    EX_SUBSCRIPTION_NAO_ENCONTRADA  EXCEPTION;
    EX_ENDPOINT_DUPLICADO           EXCEPTION;
    EX_USUARIO_SEM_SUBSCRIPTION     EXCEPTION;

    PRAGMA EXCEPTION_INIT(EX_SUBSCRIPTION_NAO_ENCONTRADA, -20501);
    PRAGMA EXCEPTION_INIT(EX_ENDPOINT_DUPLICADO, -20502);
    PRAGMA EXCEPTION_INIT(EX_USUARIO_SEM_SUBSCRIPTION, -20503);

    /**
     * Registra nova subscription de push notification
     * @param p_id_usuario ID do usuario
     * @param p_endpoint URL do endpoint da subscription
     * @param p_p256dh_key Chave publica P256DH
     * @param p_auth_key Chave de autenticacao
     * @param p_user_agent User agent do browser
     * @param p_ip_address IP do cliente
     * @return ID da subscription criada
     */
    FUNCTION REGISTRAR_SUBSCRIPTION(
        p_id_usuario        IN NUMBER,
        p_endpoint          IN VARCHAR2,
        p_p256dh_key        IN VARCHAR2 DEFAULT NULL,
        p_auth_key          IN VARCHAR2 DEFAULT NULL,
        p_user_agent        IN VARCHAR2 DEFAULT NULL,
        p_ip_address        IN VARCHAR2 DEFAULT NULL
    ) RETURN NUMBER;

    /**
     * Remove subscription (unsubscribe)
     * @param p_id_subscription ID da subscription
     */
    PROCEDURE REMOVER_SUBSCRIPTION(
        p_id_subscription   IN NUMBER
    );

    /**
     * Remove subscription por endpoint
     * @param p_endpoint URL do endpoint
     */
    PROCEDURE REMOVER_SUBSCRIPTION_POR_ENDPOINT(
        p_endpoint          IN VARCHAR2
    );

    /**
     * Envia push notification para um usuario
     * @param p_id_usuario ID do usuario
     * @param p_titulo Titulo da notificacao
     * @param p_mensagem Mensagem da notificacao
     * @param p_id_notificacao ID da notificacao do sistema (opcional)
     * @return Quantidade de subscriptions que receberam
     */
    FUNCTION ENVIAR_PUSH_USUARIO(
        p_id_usuario        IN NUMBER,
        p_titulo            IN VARCHAR2,
        p_mensagem          IN CLOB,
        p_id_notificacao    IN NUMBER DEFAULT NULL
    ) RETURN NUMBER;

    /**
     * Envia push notification para uma subscription especifica
     * @param p_id_subscription ID da subscription
     * @param p_titulo Titulo da notificacao
     * @param p_mensagem Mensagem da notificacao
     * @param p_id_notificacao ID da notificacao do sistema (opcional)
     */
    PROCEDURE ENVIAR_PUSH_SUBSCRIPTION(
        p_id_subscription   IN NUMBER,
        p_titulo            IN VARCHAR2,
        p_mensagem          IN CLOB,
        p_id_notificacao    IN NUMBER DEFAULT NULL
    );

    /**
     * Envia push para todos usuarios ativos
     * Usado para notificacoes em broadcast
     * @param p_titulo Titulo da notificacao
     * @param p_mensagem Mensagem da notificacao
     * @return Quantidade de subscriptions que receberam
     */
    FUNCTION ENVIAR_PUSH_BROADCAST(
        p_titulo            IN VARCHAR2,
        p_mensagem          IN CLOB
    ) RETURN NUMBER;

    /**
     * Lista subscriptions de um usuario
     * @param p_id_usuario ID do usuario
     * @param p_apenas_ativas TRUE para apenas ativas
     * @return Cursor com subscriptions
     */
    FUNCTION LISTAR_SUBSCRIPTIONS_USUARIO(
        p_id_usuario        IN NUMBER,
        p_apenas_ativas     IN BOOLEAN DEFAULT TRUE
    ) RETURN t_cursor;

    /**
     * Verifica se usuario tem subscriptions ativas
     * @param p_id_usuario ID do usuario
     * @return TRUE se tem subscriptions ativas
     */
    FUNCTION TEM_SUBSCRIPTION_ATIVA(
        p_id_usuario        IN NUMBER
    ) RETURN BOOLEAN;

    /**
     * Ativa/Desativa subscription
     * @param p_id_subscription ID da subscription
     * @param p_ativo S ou N
     */
    PROCEDURE ALTERAR_STATUS_SUBSCRIPTION(
        p_id_subscription   IN NUMBER,
        p_ativo             IN CHAR
    );

    /**
     * Registra erro no envio de push
     * Util para desativar subscriptions com muitos erros
     * @param p_id_subscription ID da subscription
     * @param p_erro_mensagem Mensagem de erro
     */
    PROCEDURE REGISTRAR_ERRO_ENVIO(
        p_id_subscription   IN NUMBER,
        p_erro_mensagem     IN CLOB
    );

    /**
     * Limpa subscriptions inativas ha mais de X dias
     * @param p_dias_inatividade Dias de inatividade
     * @return Quantidade de subscriptions removidas
     */
    FUNCTION LIMPAR_SUBSCRIPTIONS_INATIVAS(
        p_dias_inatividade  IN NUMBER DEFAULT 90
    ) RETURN NUMBER;

    /**
     * Obtem estatisticas de push notifications
     * @return Cursor com estatisticas
     */
    FUNCTION OBTER_ESTATISTICAS RETURN t_cursor;

END PKG_PUSH_NOTIFICATION;
/


-- ==============================================================================
-- PACKAGE BODY
-- ==============================================================================
CREATE OR REPLACE PACKAGE BODY PKG_PUSH_NOTIFICATION AS

    -- ============================================================================
    -- REGISTRAR_SUBSCRIPTION
    -- ============================================================================
    FUNCTION REGISTRAR_SUBSCRIPTION(
        p_id_usuario        IN NUMBER,
        p_endpoint          IN VARCHAR2,
        p_p256dh_key        IN VARCHAR2 DEFAULT NULL,
        p_auth_key          IN VARCHAR2 DEFAULT NULL,
        p_user_agent        IN VARCHAR2 DEFAULT NULL,
        p_ip_address        IN VARCHAR2 DEFAULT NULL
    ) RETURN NUMBER IS
        v_id_subscription   NUMBER;
        v_count             NUMBER;
    BEGIN
        -- Validar se usuario existe
        SELECT COUNT(*) INTO v_count
        FROM LCP_USUARIO
        WHERE ID = p_id_usuario
          AND ATIVO = 'S';

        IF v_count = 0 THEN
            RAISE_APPLICATION_ERROR(-20001, 'Usuario nao encontrado ou inativo');
        END IF;

        -- Verificar se endpoint ja existe
        BEGIN
            SELECT ID INTO v_id_subscription
            FROM LCP_PUSH_SUBSCRIPTION
            WHERE ENDPOINT = p_endpoint;

            -- Endpoint existe - atualizar usuario e reativar se necessario
            UPDATE LCP_PUSH_SUBSCRIPTION
            SET ID_USUARIO = p_id_usuario,
                P256DH_KEY = NVL(p_p256dh_key, P256DH_KEY),
                AUTH_KEY = NVL(p_auth_key, AUTH_KEY),
                USER_AGENT = NVL(p_user_agent, USER_AGENT),
                IP_ADDRESS = NVL(p_ip_address, IP_ADDRESS),
                ATIVO = 'S',
                DATA_SUBSCRIPTION = SYSDATE
            WHERE ID = v_id_subscription;

            COMMIT;
            RETURN v_id_subscription;

        EXCEPTION
            WHEN NO_DATA_FOUND THEN
                -- Endpoint nao existe - criar novo
                NULL;
        END;

        -- Inserir nova subscription
        INSERT INTO LCP_PUSH_SUBSCRIPTION (
            ID,
            ID_USUARIO,
            ENDPOINT,
            P256DH_KEY,
            AUTH_KEY,
            USER_AGENT,
            IP_ADDRESS,
            ATIVO,
            DATA_SUBSCRIPTION,
            TOTAL_ENVIADOS,
            TOTAL_ERROS
        ) VALUES (
            SEQ_LCP_PUSH_SUBSCRIPTION.NEXTVAL,
            p_id_usuario,
            p_endpoint,
            p_p256dh_key,
            p_auth_key,
            p_user_agent,
            p_ip_address,
            'S',
            SYSDATE,
            0,
            0
        ) RETURNING ID INTO v_id_subscription;

        COMMIT;

        RETURN v_id_subscription;
    EXCEPTION
        WHEN OTHERS THEN
            ROLLBACK;
            RAISE;
    END REGISTRAR_SUBSCRIPTION;

    -- ============================================================================
    -- REMOVER_SUBSCRIPTION
    -- ============================================================================
    PROCEDURE REMOVER_SUBSCRIPTION(
        p_id_subscription   IN NUMBER
    ) IS
    BEGIN
        DELETE FROM LCP_PUSH_SUBSCRIPTION
        WHERE ID = p_id_subscription;

        IF SQL%ROWCOUNT = 0 THEN
            RAISE EX_SUBSCRIPTION_NAO_ENCONTRADA;
        END IF;

        COMMIT;
    EXCEPTION
        WHEN EX_SUBSCRIPTION_NAO_ENCONTRADA THEN
            RAISE_APPLICATION_ERROR(-20501, 'Subscription nao encontrada');
        WHEN OTHERS THEN
            ROLLBACK;
            RAISE;
    END REMOVER_SUBSCRIPTION;

    -- ============================================================================
    -- REMOVER_SUBSCRIPTION_POR_ENDPOINT
    -- ============================================================================
    PROCEDURE REMOVER_SUBSCRIPTION_POR_ENDPOINT(
        p_endpoint          IN VARCHAR2
    ) IS
    BEGIN
        DELETE FROM LCP_PUSH_SUBSCRIPTION
        WHERE ENDPOINT = p_endpoint;

        IF SQL%ROWCOUNT = 0 THEN
            RAISE EX_SUBSCRIPTION_NAO_ENCONTRADA;
        END IF;

        COMMIT;
    EXCEPTION
        WHEN EX_SUBSCRIPTION_NAO_ENCONTRADA THEN
            RAISE_APPLICATION_ERROR(-20501, 'Subscription nao encontrada');
        WHEN OTHERS THEN
            ROLLBACK;
            RAISE;
    END REMOVER_SUBSCRIPTION_POR_ENDPOINT;

    -- ============================================================================
    -- ENVIAR_PUSH_USUARIO
    -- ============================================================================
    FUNCTION ENVIAR_PUSH_USUARIO(
        p_id_usuario        IN NUMBER,
        p_titulo            IN VARCHAR2,
        p_mensagem          IN CLOB,
        p_id_notificacao    IN NUMBER DEFAULT NULL
    ) RETURN NUMBER IS
        v_count             NUMBER := 0;
        CURSOR c_subscriptions IS
            SELECT ID AS ID_SUBSCRIPTION
            FROM LCP_PUSH_SUBSCRIPTION
            WHERE ID_USUARIO = p_id_usuario
              AND ATIVO = 'S';
    BEGIN
        -- Enviar para todas subscriptions ativas do usuario
        FOR rec IN c_subscriptions LOOP
            BEGIN
                ENVIAR_PUSH_SUBSCRIPTION(
                    p_id_subscription => rec.ID_SUBSCRIPTION,
                    p_titulo => p_titulo,
                    p_mensagem => p_mensagem,
                    p_id_notificacao => p_id_notificacao
                );
                v_count := v_count + 1;
            EXCEPTION
                WHEN OTHERS THEN
                    -- Log do erro mas continua enviando para outras subscriptions
                    REGISTRAR_ERRO_ENVIO(
                        p_id_subscription => rec.ID_SUBSCRIPTION,
                        p_erro_mensagem => SQLERRM
                    );
            END;
        END LOOP;

        RETURN v_count;
    END ENVIAR_PUSH_USUARIO;

    -- ============================================================================
    -- ENVIAR_PUSH_SUBSCRIPTION
    -- ============================================================================
    PROCEDURE ENVIAR_PUSH_SUBSCRIPTION(
        p_id_subscription   IN NUMBER,
        p_titulo            IN VARCHAR2,
        p_mensagem          IN CLOB,
        p_id_notificacao    IN NUMBER DEFAULT NULL
    ) IS
        v_endpoint          VARCHAR2(1000);
        v_p256dh_key        VARCHAR2(500);
        v_auth_key          VARCHAR2(500);
        v_id_log            NUMBER;
    BEGIN
        -- Buscar dados da subscription
        SELECT ENDPOINT, P256DH_KEY, AUTH_KEY
        INTO v_endpoint, v_p256dh_key, v_auth_key
        FROM LCP_PUSH_SUBSCRIPTION
        WHERE ID = p_id_subscription
          AND ATIVO = 'S';

        -- IMPORTANTE: Esta e a parte que integra com o servico externo
        -- No APEX, voce usaria APEX_PWA.SEND_PUSH_NOTIFICATION
        -- Exemplo:
        /*
        APEX_PWA.SEND_PUSH_NOTIFICATION(
            p_subscription_id => p_id_subscription,
            p_title => p_titulo,
            p_body => p_mensagem,
            p_target_url => '/notificacoes'
        );
        */

        -- Por enquanto, apenas registrar no log como PENDENTE
        -- O APEX ira processar em background
        INSERT INTO LCP_PUSH_LOG (
            ID,
            ID_SUBSCRIPTION,
            ID_NOTIFICACAO,
            TITULO,
            MENSAGEM,
            STATUS,
            DATA_ENVIO
        ) VALUES (
            SEQ_LCP_PUSH_LOG.NEXTVAL,
            p_id_subscription,
            p_id_notificacao,
            p_titulo,
            p_mensagem,
            'PENDENTE',
            SYSDATE
        ) RETURNING ID INTO v_id_log;

        -- Atualizar estatisticas da subscription
        UPDATE LCP_PUSH_SUBSCRIPTION
        SET DATA_ULTIMO_ENVIO = SYSDATE,
            TOTAL_ENVIADOS = TOTAL_ENVIADOS + 1
        WHERE ID = p_id_subscription;

        COMMIT;

    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            RAISE EX_SUBSCRIPTION_NAO_ENCONTRADA;
        WHEN OTHERS THEN
            ROLLBACK;
            -- Registrar erro
            REGISTRAR_ERRO_ENVIO(
                p_id_subscription => p_id_subscription,
                p_erro_mensagem => SQLERRM
            );
            RAISE;
    END ENVIAR_PUSH_SUBSCRIPTION;

    -- ============================================================================
    -- ENVIAR_PUSH_BROADCAST
    -- ============================================================================
    FUNCTION ENVIAR_PUSH_BROADCAST(
        p_titulo            IN VARCHAR2,
        p_mensagem          IN CLOB
    ) RETURN NUMBER IS
        v_count             NUMBER := 0;
        CURSOR c_usuarios IS
            SELECT DISTINCT ID_USUARIO
            FROM LCP_PUSH_SUBSCRIPTION
            WHERE ATIVO = 'S';
    BEGIN
        -- Enviar para todos usuarios com subscription ativa
        FOR rec IN c_usuarios LOOP
            BEGIN
                v_count := v_count + ENVIAR_PUSH_USUARIO(
                    p_id_usuario => rec.ID_USUARIO,
                    p_titulo => p_titulo,
                    p_mensagem => p_mensagem
                );
            EXCEPTION
                WHEN OTHERS THEN
                    -- Continua enviando para outros usuarios
                    NULL;
            END;
        END LOOP;

        RETURN v_count;
    END ENVIAR_PUSH_BROADCAST;

    -- ============================================================================
    -- LISTAR_SUBSCRIPTIONS_USUARIO
    -- ============================================================================
    FUNCTION LISTAR_SUBSCRIPTIONS_USUARIO(
        p_id_usuario        IN NUMBER,
        p_apenas_ativas     IN BOOLEAN DEFAULT TRUE
    ) RETURN t_cursor IS
        v_cursor t_cursor;
    BEGIN
        IF p_apenas_ativas THEN
            OPEN v_cursor FOR
                SELECT
                    ID AS ID_SUBSCRIPTION,
                    ID_USUARIO,
                    ENDPOINT,
                    USER_AGENT,
                    IP_ADDRESS,
                    ATIVO,
                    DATA_SUBSCRIPTION,
                    DATA_ULTIMO_ENVIO,
                    TOTAL_ENVIADOS,
                    TOTAL_ERROS
                FROM LCP_PUSH_SUBSCRIPTION
                WHERE ID_USUARIO = p_id_usuario
                  AND ATIVO = 'S'
                ORDER BY DATA_SUBSCRIPTION DESC;
        ELSE
            OPEN v_cursor FOR
                SELECT
                    ID AS ID_SUBSCRIPTION,
                    ID_USUARIO,
                    ENDPOINT,
                    USER_AGENT,
                    IP_ADDRESS,
                    ATIVO,
                    DATA_SUBSCRIPTION,
                    DATA_ULTIMO_ENVIO,
                    TOTAL_ENVIADOS,
                    TOTAL_ERROS
                FROM LCP_PUSH_SUBSCRIPTION
                WHERE ID_USUARIO = p_id_usuario
                ORDER BY DATA_SUBSCRIPTION DESC;
        END IF;

        RETURN v_cursor;
    END LISTAR_SUBSCRIPTIONS_USUARIO;

    -- ============================================================================
    -- TEM_SUBSCRIPTION_ATIVA
    -- ============================================================================
    FUNCTION TEM_SUBSCRIPTION_ATIVA(
        p_id_usuario        IN NUMBER
    ) RETURN BOOLEAN IS
        v_count NUMBER;
    BEGIN
        SELECT COUNT(*) INTO v_count
        FROM LCP_PUSH_SUBSCRIPTION
        WHERE ID_USUARIO = p_id_usuario
          AND ATIVO = 'S';

        RETURN v_count > 0;
    END TEM_SUBSCRIPTION_ATIVA;

    -- ============================================================================
    -- ALTERAR_STATUS_SUBSCRIPTION
    -- ============================================================================
    PROCEDURE ALTERAR_STATUS_SUBSCRIPTION(
        p_id_subscription   IN NUMBER,
        p_ativo             IN CHAR
    ) IS
    BEGIN
        UPDATE LCP_PUSH_SUBSCRIPTION
        SET ATIVO = p_ativo
        WHERE ID = p_id_subscription;

        IF SQL%ROWCOUNT = 0 THEN
            RAISE EX_SUBSCRIPTION_NAO_ENCONTRADA;
        END IF;

        COMMIT;
    EXCEPTION
        WHEN EX_SUBSCRIPTION_NAO_ENCONTRADA THEN
            RAISE_APPLICATION_ERROR(-20501, 'Subscription nao encontrada');
        WHEN OTHERS THEN
            ROLLBACK;
            RAISE;
    END ALTERAR_STATUS_SUBSCRIPTION;

    -- ============================================================================
    -- REGISTRAR_ERRO_ENVIO
    -- ============================================================================
    PROCEDURE REGISTRAR_ERRO_ENVIO(
        p_id_subscription   IN NUMBER,
        p_erro_mensagem     IN CLOB
    ) IS
        v_total_erros NUMBER;
    BEGIN
        -- Incrementar contador de erros
        UPDATE LCP_PUSH_SUBSCRIPTION
        SET TOTAL_ERROS = TOTAL_ERROS + 1
        WHERE ID = p_id_subscription
        RETURNING TOTAL_ERROS INTO v_total_erros;

        -- Se muitos erros consecutivos, desativar subscription
        IF v_total_erros >= 10 THEN
            UPDATE LCP_PUSH_SUBSCRIPTION
            SET ATIVO = 'N'
            WHERE ID = p_id_subscription;
        END IF;

        -- Registrar no log
        INSERT INTO LCP_PUSH_LOG (
            ID,
            ID_SUBSCRIPTION,
            TITULO,
            MENSAGEM,
            STATUS,
            ERRO_MENSAGEM,
            DATA_ENVIO
        ) VALUES (
            SEQ_LCP_PUSH_LOG.NEXTVAL,
            p_id_subscription,
            'ERRO',
            'Erro ao enviar push notification',
            'ERRO',
            p_erro_mensagem,
            SYSDATE
        );

        COMMIT;
    EXCEPTION
        WHEN OTHERS THEN
            ROLLBACK;
            -- Nao propagar erro para nao quebrar fluxo principal
            NULL;
    END REGISTRAR_ERRO_ENVIO;

    -- ============================================================================
    -- LIMPAR_SUBSCRIPTIONS_INATIVAS
    -- ============================================================================
    FUNCTION LIMPAR_SUBSCRIPTIONS_INATIVAS(
        p_dias_inatividade  IN NUMBER DEFAULT 90
    ) RETURN NUMBER IS
        v_count NUMBER;
    BEGIN
        DELETE FROM LCP_PUSH_SUBSCRIPTION
        WHERE ATIVO = 'N'
          AND DATA_SUBSCRIPTION < SYSDATE - p_dias_inatividade;

        v_count := SQL%ROWCOUNT;
        COMMIT;

        RETURN v_count;
    EXCEPTION
        WHEN OTHERS THEN
            ROLLBACK;
            RAISE;
    END LIMPAR_SUBSCRIPTIONS_INATIVAS;

    -- ============================================================================
    -- OBTER_ESTATISTICAS
    -- ============================================================================
    FUNCTION OBTER_ESTATISTICAS RETURN t_cursor IS
        v_cursor t_cursor;
    BEGIN
        OPEN v_cursor FOR
            SELECT
                (SELECT COUNT(*) FROM LCP_PUSH_SUBSCRIPTION WHERE ATIVO = 'S') AS TOTAL_SUBSCRIPTIONS_ATIVAS,
                (SELECT COUNT(*) FROM LCP_PUSH_SUBSCRIPTION WHERE ATIVO = 'N') AS TOTAL_SUBSCRIPTIONS_INATIVAS,
                (SELECT COUNT(DISTINCT ID_USUARIO) FROM LCP_PUSH_SUBSCRIPTION WHERE ATIVO = 'S') AS TOTAL_USUARIOS_COM_PUSH,
                (SELECT SUM(TOTAL_ENVIADOS) FROM LCP_PUSH_SUBSCRIPTION) AS TOTAL_PUSH_ENVIADOS,
                (SELECT SUM(TOTAL_ERROS) FROM LCP_PUSH_SUBSCRIPTION) AS TOTAL_PUSH_ERROS,
                (SELECT COUNT(*) FROM LCP_PUSH_LOG WHERE STATUS = 'ENVIADO') AS TOTAL_LOG_ENVIADOS,
                (SELECT COUNT(*) FROM LCP_PUSH_LOG WHERE STATUS = 'ERRO') AS TOTAL_LOG_ERROS,
                (SELECT COUNT(*) FROM LCP_PUSH_LOG WHERE STATUS = 'PENDENTE') AS TOTAL_LOG_PENDENTES
            FROM DUAL;

        RETURN v_cursor;
    END OBTER_ESTATISTICAS;

END PKG_PUSH_NOTIFICATION;
/
