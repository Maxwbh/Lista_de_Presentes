-- ==============================================================================
-- SCRIPT: INTEGRACAO PUSH NOTIFICATIONS COM APEX
-- Descricao: Integra push notifications com sistema de notificacoes existente
-- Desenvolvedor: Maxwell da Silva Oliveira (@maxwbh)
-- Email: maxwbh@gmail.com
-- Empresa: M&S do Brasil LTDA - msbrasil.inf.br
-- Data: 2025-11-21
-- ==============================================================================

-- ==============================================================================
-- TRIGGER: Enviar push quando criar notificacao
-- ==============================================================================
CREATE OR REPLACE TRIGGER TRG_NOTIFICACAO_PUSH
AFTER INSERT ON TB_NOTIFICACAO
FOR EACH ROW
DECLARE
    v_count NUMBER;
BEGIN
    -- Verificar se usuario tem push notifications habilitadas
    IF PKG_PUSH_NOTIFICATION.TEM_SUBSCRIPTION_ATIVA(:NEW.ID_USUARIO) THEN
        -- Enviar push notification (async - nao bloqueia insercao)
        BEGIN
            v_count := PKG_PUSH_NOTIFICATION.ENVIAR_PUSH_USUARIO(
                p_id_usuario => :NEW.ID_USUARIO,
                p_titulo => 'Nova Notificacao',
                p_mensagem => SUBSTR(:NEW.MENSAGEM, 1, 200),
                p_id_notificacao => :NEW.ID_NOTIFICACAO
            );
        EXCEPTION
            WHEN OTHERS THEN
                -- Nao propagar erro - push e opcional
                NULL;
        END;
    END IF;
END;
/

-- ==============================================================================
-- PROCEDURE: Enviar push para compra realizada
-- ==============================================================================
CREATE OR REPLACE PROCEDURE PRC_PUSH_COMPRA_REALIZADA(
    p_id_presente       IN NUMBER,
    p_id_comprador      IN NUMBER
) IS
    v_descricao         CLOB;
    v_id_usuario_dono   NUMBER;
    v_nome_comprador    VARCHAR2(200);
BEGIN
    -- Buscar dados
    SELECT p.DESCRICAO, p.ID_USUARIO,
           comp.PRIMEIRO_NOME || ' ' || comp.ULTIMO_NOME
    INTO v_descricao, v_id_usuario_dono, v_nome_comprador
    FROM TB_PRESENTE p
    INNER JOIN TB_USUARIO comp ON comp.ID_USUARIO = p_id_comprador
    WHERE p.ID_PRESENTE = p_id_presente;

    -- Enviar push notification
    IF PKG_PUSH_NOTIFICATION.TEM_SUBSCRIPTION_ATIVA(v_id_usuario_dono) THEN
        BEGIN
            PKG_PUSH_NOTIFICATION.ENVIAR_PUSH_USUARIO(
                p_id_usuario => v_id_usuario_dono,
                p_titulo => '🎁 Presente Comprado!',
                p_mensagem => v_nome_comprador || ' comprou: ' || SUBSTR(v_descricao, 1, 100)
            );
        EXCEPTION
            WHEN OTHERS THEN
                NULL;
        END;
    END IF;
END;
/

-- ==============================================================================
-- PROCEDURE: Enviar push para novo presente disponivel
-- ==============================================================================
CREATE OR REPLACE PROCEDURE PRC_PUSH_NOVO_PRESENTE(
    p_id_presente       IN NUMBER
) IS
    v_descricao         CLOB;
    v_preco             NUMBER;
    v_nome_usuario      VARCHAR2(200);
    v_count             NUMBER;
BEGIN
    -- Buscar dados do presente
    SELECT p.DESCRICAO, p.PRECO,
           u.PRIMEIRO_NOME || ' ' || u.ULTIMO_NOME
    INTO v_descricao, v_preco, v_nome_usuario
    FROM TB_PRESENTE p
    INNER JOIN TB_USUARIO u ON p.ID_USUARIO = u.ID_USUARIO
    WHERE p.ID_PRESENTE = p_id_presente;

    -- Enviar broadcast (opcional - pode ser muito volume)
    -- Apenas se for presente de valor alto
    IF v_preco IS NOT NULL AND v_preco > 1000 THEN
        BEGIN
            v_count := PKG_PUSH_NOTIFICATION.ENVIAR_PUSH_BROADCAST(
                p_titulo => '🎁 Novo Presente Disponivel',
                p_mensagem => v_nome_usuario || ' adicionou: ' || SUBSTR(v_descricao, 1, 100)
            );
        EXCEPTION
            WHEN OTHERS THEN
                NULL;
        END;
    END IF;
END;
/

-- ==============================================================================
-- VIEW: Estatisticas de Push Notifications
-- ==============================================================================
CREATE OR REPLACE VIEW VW_PUSH_ESTATISTICAS AS
SELECT
    u.ID_USUARIO,
    u.PRIMEIRO_NOME || ' ' || u.ULTIMO_NOME AS NOME_USUARIO,
    u.EMAIL,
    COUNT(ps.ID_SUBSCRIPTION) AS TOTAL_SUBSCRIPTIONS,
    SUM(CASE WHEN ps.ATIVO = 'S' THEN 1 ELSE 0 END) AS SUBSCRIPTIONS_ATIVAS,
    MAX(ps.DATA_ULTIMO_ENVIO) AS ULTIMO_PUSH_ENVIADO,
    SUM(ps.TOTAL_ENVIADOS) AS TOTAL_PUSH_ENVIADOS,
    SUM(ps.TOTAL_ERROS) AS TOTAL_PUSH_ERROS,
    ROUND(
        CASE
            WHEN SUM(ps.TOTAL_ENVIADOS) > 0
            THEN (SUM(ps.TOTAL_ENVIADOS) - SUM(ps.TOTAL_ERROS)) / SUM(ps.TOTAL_ENVIADOS) * 100
            ELSE 0
        END,
        2
    ) AS TAXA_SUCESSO_PCT
FROM TB_USUARIO u
LEFT JOIN TB_PUSH_SUBSCRIPTION ps ON u.ID_USUARIO = ps.ID_USUARIO
WHERE u.ATIVO = 'S'
GROUP BY u.ID_USUARIO, u.PRIMEIRO_NOME, u.ULTIMO_NOME, u.EMAIL;

COMMENT ON VIEW VW_PUSH_ESTATISTICAS IS 'Estatisticas de push notifications por usuario';

-- ==============================================================================
-- PROCEDURES APEX PARA SERVICE WORKER
-- ==============================================================================

/**
 * Procedure para ser chamada pelo Service Worker do APEX PWA
 * Registra subscription quando usuario habilita push notifications
 */
CREATE OR REPLACE PROCEDURE APEX_REGISTRAR_PUSH_SUBSCRIPTION(
    p_user_id           IN NUMBER,
    p_endpoint          IN VARCHAR2,
    p_p256dh_key        IN VARCHAR2 DEFAULT NULL,
    p_auth_key          IN VARCHAR2 DEFAULT NULL
) IS
    v_id_subscription   NUMBER;
    v_user_agent        VARCHAR2(500);
    v_ip_address        VARCHAR2(50);
BEGIN
    -- Obter informacoes do contexto APEX
    v_user_agent := NVL(OWA_UTIL.GET_CGI_ENV('HTTP_USER_AGENT'), 'Unknown');
    v_ip_address := NVL(OWA_UTIL.GET_CGI_ENV('REMOTE_ADDR'), 'Unknown');

    -- Registrar subscription
    v_id_subscription := PKG_PUSH_NOTIFICATION.REGISTRAR_SUBSCRIPTION(
        p_id_usuario => p_user_id,
        p_endpoint => p_endpoint,
        p_p256dh_key => p_p256dh_key,
        p_auth_key => p_auth_key,
        p_user_agent => v_user_agent,
        p_ip_address => v_ip_address
    );

    -- Retornar sucesso para APEX
    HTP.P('{"success":true,"subscription_id":' || v_id_subscription || '}');
EXCEPTION
    WHEN OTHERS THEN
        HTP.P('{"success":false,"error":"' || REPLACE(SQLERRM, '"', '\"') || '"}');
END;
/

/**
 * Procedure para ser chamada quando usuario desabilita push notifications
 */
CREATE OR REPLACE PROCEDURE APEX_REMOVER_PUSH_SUBSCRIPTION(
    p_endpoint          IN VARCHAR2
) IS
BEGIN
    PKG_PUSH_NOTIFICATION.REMOVER_SUBSCRIPTION_POR_ENDPOINT(
        p_endpoint => p_endpoint
    );

    HTP.P('{"success":true}');
EXCEPTION
    WHEN OTHERS THEN
        HTP.P('{"success":false,"error":"' || REPLACE(SQLERRM, '"', '\"') || '"}');
END;
/

/**
 * Procedure para processar fila de push notifications pendentes
 * Deve ser chamada por job agendado
 */
CREATE OR REPLACE PROCEDURE APEX_PROCESSAR_PUSH_PENDENTES IS
    CURSOR c_pendentes IS
        SELECT
            l.ID_LOG,
            l.ID_SUBSCRIPTION,
            l.TITULO,
            l.MENSAGEM,
            s.ENDPOINT,
            s.P256DH_KEY,
            s.AUTH_KEY
        FROM TB_PUSH_LOG l
        INNER JOIN TB_PUSH_SUBSCRIPTION s ON l.ID_SUBSCRIPTION = s.ID_SUBSCRIPTION
        WHERE l.STATUS = 'PENDENTE'
          AND s.ATIVO = 'S'
        ORDER BY l.DATA_ENVIO
        FETCH FIRST 100 ROWS ONLY;

    v_sucesso BOOLEAN;
BEGIN
    FOR rec IN c_pendentes LOOP
        BEGIN
            -- IMPORTANTE: Aqui voce chamaria APEX_PWA.SEND_PUSH_NOTIFICATION
            -- Exemplo:
            /*
            APEX_PWA.SEND_PUSH_NOTIFICATION(
                p_subscription_id => rec.ID_SUBSCRIPTION,
                p_title => rec.TITULO,
                p_body => rec.MENSAGEM,
                p_target_url => '/notificacoes'
            );
            */

            -- Por enquanto, apenas marcar como enviado
            UPDATE TB_PUSH_LOG
            SET STATUS = 'ENVIADO'
            WHERE ID_LOG = rec.ID_LOG;

            COMMIT;

        EXCEPTION
            WHEN OTHERS THEN
                -- Marcar como erro
                UPDATE TB_PUSH_LOG
                SET STATUS = 'ERRO',
                    ERRO_MENSAGEM = SQLERRM
                WHERE ID_LOG = rec.ID_LOG;

                -- Registrar erro na subscription
                PKG_PUSH_NOTIFICATION.REGISTRAR_ERRO_ENVIO(
                    p_id_subscription => rec.ID_SUBSCRIPTION,
                    p_erro_mensagem => SQLERRM
                );

                COMMIT;
        END;
    END LOOP;
END;
/

-- ==============================================================================
-- JOB: Processar push notifications pendentes
-- ==============================================================================
BEGIN
    DBMS_SCHEDULER.CREATE_JOB(
        job_name        => 'JOB_PROCESSAR_PUSH_PENDENTES',
        job_type        => 'PLSQL_BLOCK',
        job_action      => 'BEGIN APEX_PROCESSAR_PUSH_PENDENTES; END;',
        start_date      => SYSTIMESTAMP,
        repeat_interval => 'FREQ=MINUTELY; INTERVAL=1',
        enabled         => FALSE,
        comments        => 'Processa push notifications pendentes a cada 1 minuto'
    );
END;
/

-- ==============================================================================
-- JOB: Limpar subscriptions inativas
-- ==============================================================================
BEGIN
    DBMS_SCHEDULER.CREATE_JOB(
        job_name        => 'JOB_LIMPAR_PUSH_INATIVAS',
        job_type        => 'PLSQL_BLOCK',
        job_action      => 'DECLARE v_count NUMBER; BEGIN v_count := PKG_PUSH_NOTIFICATION.LIMPAR_SUBSCRIPTIONS_INATIVAS(90); END;',
        start_date      => SYSTIMESTAMP,
        repeat_interval => 'FREQ=DAILY; BYHOUR=3',
        enabled         => FALSE,
        comments        => 'Limpa subscriptions inativas com mais de 90 dias'
    );
END;
/

-- ==============================================================================
-- INSTRUCOES PARA HABILITAR OS JOBS
-- ==============================================================================
/*
Para habilitar os jobs, execute:

BEGIN
    DBMS_SCHEDULER.ENABLE('JOB_PROCESSAR_PUSH_PENDENTES');
    DBMS_SCHEDULER.ENABLE('JOB_LIMPAR_PUSH_INATIVAS');
END;
/

Para desabilitar:

BEGIN
    DBMS_SCHEDULER.DISABLE('JOB_PROCESSAR_PUSH_PENDENTES');
    DBMS_SCHEDULER.DISABLE('JOB_LIMPAR_PUSH_INATIVAS');
END;
/

Para remover:

BEGIN
    DBMS_SCHEDULER.DROP_JOB('JOB_PROCESSAR_PUSH_PENDENTES');
    DBMS_SCHEDULER.DROP_JOB('JOB_LIMPAR_PUSH_INATIVAS');
END;
/
*/

-- ==============================================================================
-- FIM DO SCRIPT DE INTEGRACAO
-- ==============================================================================
