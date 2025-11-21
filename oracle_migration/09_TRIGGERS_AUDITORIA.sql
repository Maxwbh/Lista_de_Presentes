-- ==============================================================================
-- TRIGGERS DE AUDITORIA E SEQUENCES
-- Oracle 26 / Apex 24
-- Data: 2025-11-21
-- Desenvolvedor: Maxwell da Silva Oliveira (@maxwbh)
-- Email: maxwbh@gmail.com
-- Empresa: M&S do Brasil LTDA - msbrasil.inf.br
-- ==============================================================================

-- ==============================================================================
-- PARTE 1: TRIGGERS PARA AUTO-INCREMENTO DE SEQUENCES
-- ==============================================================================

-- Trigger para LCP_USUARIO
CREATE OR REPLACE TRIGGER TRG_LCP_USUARIO_BI
BEFORE INSERT ON LCP_USUARIO
FOR EACH ROW
BEGIN
    IF :NEW.ID IS NULL THEN
        :NEW.ID := SEQ_LCP_USUARIO.NEXTVAL;
    END IF;
END;
/

-- Trigger para LCP_PRESENTE
CREATE OR REPLACE TRIGGER TRG_LCP_PRESENTE_BI
BEFORE INSERT ON LCP_PRESENTE
FOR EACH ROW
BEGIN
    IF :NEW.ID IS NULL THEN
        :NEW.ID := SEQ_LCP_PRESENTE.NEXTVAL;
    END IF;
END;
/

-- Trigger para LCP_COMPRA
CREATE OR REPLACE TRIGGER TRG_LCP_COMPRA_BI
BEFORE INSERT ON LCP_COMPRA
FOR EACH ROW
BEGIN
    IF :NEW.ID IS NULL THEN
        :NEW.ID := SEQ_LCP_COMPRA.NEXTVAL;
    END IF;
END;
/

-- Trigger para LCP_SUGESTAO_COMPRA
CREATE OR REPLACE TRIGGER TRG_LCP_SUGESTAO_COMPRA_BI
BEFORE INSERT ON LCP_SUGESTAO_COMPRA
FOR EACH ROW
BEGIN
    IF :NEW.ID IS NULL THEN
        :NEW.ID := SEQ_LCP_SUGESTAO_COMPRA.NEXTVAL;
    END IF;
END;
/

-- Trigger para LCP_NOTIFICACAO
CREATE OR REPLACE TRIGGER TRG_LCP_NOTIFICACAO_BI
BEFORE INSERT ON LCP_NOTIFICACAO
FOR EACH ROW
BEGIN
    IF :NEW.ID IS NULL THEN
        :NEW.ID := SEQ_LCP_NOTIFICACAO.NEXTVAL;
    END IF;
END;
/

-- Trigger para LCP_PUSH_SUBSCRIPTION
CREATE OR REPLACE TRIGGER TRG_LCP_PUSH_SUBSCRIPTION_BI
BEFORE INSERT ON LCP_PUSH_SUBSCRIPTION
FOR EACH ROW
BEGIN
    IF :NEW.ID IS NULL THEN
        :NEW.ID := SEQ_LCP_PUSH_SUBSCRIPTION.NEXTVAL;
    END IF;
END;
/

-- Trigger para LCP_PUSH_LOG
CREATE OR REPLACE TRIGGER TRG_LCP_PUSH_LOG_BI
BEFORE INSERT ON LCP_PUSH_LOG
FOR EACH ROW
BEGIN
    IF :NEW.ID IS NULL THEN
        :NEW.ID := SEQ_LCP_PUSH_LOG.NEXTVAL;
    END IF;
END;
/

-- Trigger para LCP_LOG_AUDITORIA
CREATE OR REPLACE TRIGGER TRG_LCP_LOG_AUDITORIA_BI
BEFORE INSERT ON LCP_LOG_AUDITORIA
FOR EACH ROW
BEGIN
    IF :NEW.ID IS NULL THEN
        :NEW.ID := SEQ_LCP_LOG_AUDITORIA.NEXTVAL;
    END IF;
END;
/


-- ==============================================================================
-- PARTE 2: TRIGGERS DE AUDITORIA
-- ==============================================================================

-- ==============================================================================
-- TRIGGER: AUDITORIA LCP_USUARIO
-- ==============================================================================
CREATE OR REPLACE TRIGGER TRG_AUDIT_LCP_USUARIO
AFTER INSERT OR UPDATE OR DELETE ON LCP_USUARIO
FOR EACH ROW
DECLARE
    v_operacao      VARCHAR2(10);
    v_dados_antes   CLOB;
    v_dados_depois  CLOB;
    v_id_registro   NUMBER;
    v_id_usuario    NUMBER;
BEGIN
    -- Determinar operacao
    IF INSERTING THEN
        v_operacao := 'INSERT';
        v_id_registro := :NEW.ID;
        v_id_usuario := :NEW.ID;
        v_dados_depois := 'ID: ' || :NEW.ID ||
                         ', EMAIL: ' || :NEW.EMAIL ||
                         ', USERNAME: ' || :NEW.USERNAME ||
                         ', ATIVO: ' || :NEW.ATIVO;
    ELSIF UPDATING THEN
        v_operacao := 'UPDATE';
        v_id_registro := :NEW.ID;
        v_id_usuario := :NEW.ID;
        v_dados_antes := 'ID: ' || :OLD.ID ||
                        ', EMAIL: ' || :OLD.EMAIL ||
                        ', USERNAME: ' || :OLD.USERNAME ||
                        ', ATIVO: ' || :OLD.ATIVO;
        v_dados_depois := 'ID: ' || :NEW.ID ||
                         ', EMAIL: ' || :NEW.EMAIL ||
                         ', USERNAME: ' || :NEW.USERNAME ||
                         ', ATIVO: ' || :NEW.ATIVO;
    ELSIF DELETING THEN
        v_operacao := 'DELETE';
        v_id_registro := :OLD.ID;
        v_id_usuario := :OLD.ID;
        v_dados_antes := 'ID: ' || :OLD.ID ||
                        ', EMAIL: ' || :OLD.EMAIL ||
                        ', USERNAME: ' || :OLD.USERNAME ||
                        ', ATIVO: ' || :OLD.ATIVO;
    END IF;

    -- Registrar auditoria
    INSERT INTO LCP_LOG_AUDITORIA (
        TABELA,
        ID_REGISTRO,
        OPERACAO,
        ID_USUARIO_APP,
        DADOS_ANTES,
        DADOS_DEPOIS
    ) VALUES (
        'LCP_USUARIO',
        v_id_registro,
        v_operacao,
        v_id_usuario,
        v_dados_antes,
        v_dados_depois
    );
END;
/


-- ==============================================================================
-- TRIGGER: AUDITORIA LCP_PRESENTE
-- ==============================================================================
CREATE OR REPLACE TRIGGER TRG_AUDIT_LCP_PRESENTE
AFTER INSERT OR UPDATE OR DELETE ON LCP_PRESENTE
FOR EACH ROW
DECLARE
    v_operacao      VARCHAR2(10);
    v_dados_antes   CLOB;
    v_dados_depois  CLOB;
    v_id_registro   NUMBER;
    v_id_usuario    NUMBER;
BEGIN
    IF INSERTING THEN
        v_operacao := 'INSERT';
        v_id_registro := :NEW.ID;
        v_id_usuario := :NEW.ID_USUARIO;
        v_dados_depois := 'ID: ' || :NEW.ID ||
                         ', ID_USUARIO: ' || :NEW.ID_USUARIO ||
                         ', DESCRICAO: ' || SUBSTR(:NEW.DESCRICAO, 1, 100) ||
                         ', STATUS: ' || :NEW.STATUS ||
                         ', PRECO: ' || :NEW.PRECO;
    ELSIF UPDATING THEN
        v_operacao := 'UPDATE';
        v_id_registro := :NEW.ID;
        v_id_usuario := :NEW.ID_USUARIO;
        v_dados_antes := 'ID: ' || :OLD.ID ||
                        ', STATUS: ' || :OLD.STATUS ||
                        ', PRECO: ' || :OLD.PRECO;
        v_dados_depois := 'ID: ' || :NEW.ID ||
                         ', STATUS: ' || :NEW.STATUS ||
                         ', PRECO: ' || :NEW.PRECO;
    ELSIF DELETING THEN
        v_operacao := 'DELETE';
        v_id_registro := :OLD.ID;
        v_id_usuario := :OLD.ID_USUARIO;
        v_dados_antes := 'ID: ' || :OLD.ID ||
                        ', ID_USUARIO: ' || :OLD.ID_USUARIO ||
                        ', STATUS: ' || :OLD.STATUS;
    END IF;

    INSERT INTO LCP_LOG_AUDITORIA (
        TABELA,
        ID_REGISTRO,
        OPERACAO,
        ID_USUARIO_APP,
        DADOS_ANTES,
        DADOS_DEPOIS
    ) VALUES (
        'LCP_PRESENTE',
        v_id_registro,
        v_operacao,
        v_id_usuario,
        v_dados_antes,
        v_dados_depois
    );
END;
/


-- ==============================================================================
-- TRIGGER: AUDITORIA LCP_COMPRA
-- ==============================================================================
CREATE OR REPLACE TRIGGER TRG_AUDIT_LCP_COMPRA
AFTER INSERT OR UPDATE OR DELETE ON LCP_COMPRA
FOR EACH ROW
DECLARE
    v_operacao      VARCHAR2(10);
    v_dados_antes   CLOB;
    v_dados_depois  CLOB;
    v_id_registro   NUMBER;
    v_id_usuario    NUMBER;
BEGIN
    IF INSERTING THEN
        v_operacao := 'INSERT';
        v_id_registro := :NEW.ID;
        v_id_usuario := :NEW.ID_COMPRADOR;
        v_dados_depois := 'ID: ' || :NEW.ID ||
                         ', ID_PRESENTE: ' || :NEW.ID_PRESENTE ||
                         ', ID_COMPRADOR: ' || :NEW.ID_COMPRADOR ||
                         ', DATA_COMPRA: ' || TO_CHAR(:NEW.DATA_COMPRA, 'DD/MM/YYYY HH24:MI:SS');
    ELSIF UPDATING THEN
        v_operacao := 'UPDATE';
        v_id_registro := :NEW.ID;
        v_id_usuario := :NEW.ID_COMPRADOR;
        v_dados_antes := 'ID: ' || :OLD.ID ||
                        ', ID_PRESENTE: ' || :OLD.ID_PRESENTE ||
                        ', ID_COMPRADOR: ' || :OLD.ID_COMPRADOR;
        v_dados_depois := 'ID: ' || :NEW.ID ||
                         ', ID_PRESENTE: ' || :NEW.ID_PRESENTE ||
                         ', ID_COMPRADOR: ' || :NEW.ID_COMPRADOR;
    ELSIF DELETING THEN
        v_operacao := 'DELETE';
        v_id_registro := :OLD.ID;
        v_id_usuario := :OLD.ID_COMPRADOR;
        v_dados_antes := 'ID: ' || :OLD.ID ||
                        ', ID_PRESENTE: ' || :OLD.ID_PRESENTE ||
                        ', ID_COMPRADOR: ' || :OLD.ID_COMPRADOR;
    END IF;

    INSERT INTO LCP_LOG_AUDITORIA (
        TABELA,
        ID_REGISTRO,
        OPERACAO,
        ID_USUARIO_APP,
        DADOS_ANTES,
        DADOS_DEPOIS
    ) VALUES (
        'LCP_COMPRA',
        v_id_registro,
        v_operacao,
        v_id_usuario,
        v_dados_antes,
        v_dados_depois
    );
END;
/


-- ==============================================================================
-- TRIGGER: AUDITORIA LCP_SUGESTAO_COMPRA
-- ==============================================================================
CREATE OR REPLACE TRIGGER TRG_AUDIT_LCP_SUGESTAO_COMPRA
AFTER INSERT OR UPDATE OR DELETE ON LCP_SUGESTAO_COMPRA
FOR EACH ROW
DECLARE
    v_operacao      VARCHAR2(10);
    v_dados_antes   CLOB;
    v_dados_depois  CLOB;
    v_id_registro   NUMBER;
BEGIN
    IF INSERTING THEN
        v_operacao := 'INSERT';
        v_id_registro := :NEW.ID;
        v_dados_depois := 'ID: ' || :NEW.ID ||
                         ', ID_PRESENTE: ' || :NEW.ID_PRESENTE ||
                         ', LOCAL_COMPRA: ' || :NEW.LOCAL_COMPRA ||
                         ', PRECO_SUGERIDO: ' || :NEW.PRECO_SUGERIDO;
    ELSIF UPDATING THEN
        v_operacao := 'UPDATE';
        v_id_registro := :NEW.ID;
        v_dados_antes := 'PRECO_SUGERIDO: ' || :OLD.PRECO_SUGERIDO;
        v_dados_depois := 'PRECO_SUGERIDO: ' || :NEW.PRECO_SUGERIDO;
    ELSIF DELETING THEN
        v_operacao := 'DELETE';
        v_id_registro := :OLD.ID;
        v_dados_antes := 'ID: ' || :OLD.ID ||
                        ', ID_PRESENTE: ' || :OLD.ID_PRESENTE ||
                        ', LOCAL_COMPRA: ' || :OLD.LOCAL_COMPRA;
    END IF;

    INSERT INTO LCP_LOG_AUDITORIA (
        TABELA,
        ID_REGISTRO,
        OPERACAO,
        DADOS_ANTES,
        DADOS_DEPOIS
    ) VALUES (
        'LCP_SUGESTAO_COMPRA',
        v_id_registro,
        v_operacao,
        v_dados_antes,
        v_dados_depois
    );
END;
/


-- ==============================================================================
-- TRIGGER: AUDITORIA LCP_NOTIFICACAO
-- ==============================================================================
CREATE OR REPLACE TRIGGER TRG_AUDIT_LCP_NOTIFICACAO
AFTER INSERT OR UPDATE OR DELETE ON LCP_NOTIFICACAO
FOR EACH ROW
DECLARE
    v_operacao      VARCHAR2(10);
    v_dados_antes   CLOB;
    v_dados_depois  CLOB;
    v_id_registro   NUMBER;
    v_id_usuario    NUMBER;
BEGIN
    IF INSERTING THEN
        v_operacao := 'INSERT';
        v_id_registro := :NEW.ID;
        v_id_usuario := :NEW.ID_USUARIO;
        v_dados_depois := 'ID: ' || :NEW.ID ||
                         ', ID_USUARIO: ' || :NEW.ID_USUARIO ||
                         ', LIDA: ' || :NEW.LIDA ||
                         ', MENSAGEM: ' || SUBSTR(:NEW.MENSAGEM, 1, 100);
    ELSIF UPDATING THEN
        v_operacao := 'UPDATE';
        v_id_registro := :NEW.ID;
        v_id_usuario := :NEW.ID_USUARIO;
        v_dados_antes := 'LIDA: ' || :OLD.LIDA;
        v_dados_depois := 'LIDA: ' || :NEW.LIDA;
    ELSIF DELETING THEN
        v_operacao := 'DELETE';
        v_id_registro := :OLD.ID;
        v_id_usuario := :OLD.ID_USUARIO;
        v_dados_antes := 'ID: ' || :OLD.ID ||
                        ', ID_USUARIO: ' || :OLD.ID_USUARIO ||
                        ', LIDA: ' || :OLD.LIDA;
    END IF;

    INSERT INTO LCP_LOG_AUDITORIA (
        TABELA,
        ID_REGISTRO,
        OPERACAO,
        ID_USUARIO_APP,
        DADOS_ANTES,
        DADOS_DEPOIS
    ) VALUES (
        'LCP_NOTIFICACAO',
        v_id_registro,
        v_operacao,
        v_id_usuario,
        v_dados_antes,
        v_dados_depois
    );
END;
/


-- ==============================================================================
-- TRIGGER: AUDITORIA LCP_PUSH_SUBSCRIPTION
-- ==============================================================================
CREATE OR REPLACE TRIGGER TRG_AUDIT_LCP_PUSH_SUBSCRIPTION
AFTER INSERT OR UPDATE OR DELETE ON LCP_PUSH_SUBSCRIPTION
FOR EACH ROW
DECLARE
    v_operacao      VARCHAR2(10);
    v_dados_antes   CLOB;
    v_dados_depois  CLOB;
    v_id_registro   NUMBER;
    v_id_usuario    NUMBER;
BEGIN
    IF INSERTING THEN
        v_operacao := 'INSERT';
        v_id_registro := :NEW.ID;
        v_id_usuario := :NEW.ID_USUARIO;
        v_dados_depois := 'ID: ' || :NEW.ID ||
                         ', ID_USUARIO: ' || :NEW.ID_USUARIO ||
                         ', ATIVO: ' || :NEW.ATIVO;
    ELSIF UPDATING THEN
        v_operacao := 'UPDATE';
        v_id_registro := :NEW.ID;
        v_id_usuario := :NEW.ID_USUARIO;
        v_dados_antes := 'ATIVO: ' || :OLD.ATIVO ||
                        ', TOTAL_ENVIADOS: ' || :OLD.TOTAL_ENVIADOS ||
                        ', TOTAL_ERROS: ' || :OLD.TOTAL_ERROS;
        v_dados_depois := 'ATIVO: ' || :NEW.ATIVO ||
                         ', TOTAL_ENVIADOS: ' || :NEW.TOTAL_ENVIADOS ||
                         ', TOTAL_ERROS: ' || :NEW.TOTAL_ERROS;
    ELSIF DELETING THEN
        v_operacao := 'DELETE';
        v_id_registro := :OLD.ID;
        v_id_usuario := :OLD.ID_USUARIO;
        v_dados_antes := 'ID: ' || :OLD.ID ||
                        ', ID_USUARIO: ' || :OLD.ID_USUARIO ||
                        ', ATIVO: ' || :OLD.ATIVO;
    END IF;

    INSERT INTO LCP_LOG_AUDITORIA (
        TABELA,
        ID_REGISTRO,
        OPERACAO,
        ID_USUARIO_APP,
        DADOS_ANTES,
        DADOS_DEPOIS
    ) VALUES (
        'LCP_PUSH_SUBSCRIPTION',
        v_id_registro,
        v_operacao,
        v_id_usuario,
        v_dados_antes,
        v_dados_depois
    );
END;
/


-- ==============================================================================
-- PARTE 3: COMENTARIOS DOS TRIGGERS
-- ==============================================================================

COMMENT ON TRIGGER TRG_LCP_USUARIO_BI IS 'Auto-incremento da PK da tabela LCP_USUARIO';
COMMENT ON TRIGGER TRG_LCP_PRESENTE_BI IS 'Auto-incremento da PK da tabela LCP_PRESENTE';
COMMENT ON TRIGGER TRG_LCP_COMPRA_BI IS 'Auto-incremento da PK da tabela LCP_COMPRA';
COMMENT ON TRIGGER TRG_LCP_SUGESTAO_COMPRA_BI IS 'Auto-incremento da PK da tabela LCP_SUGESTAO_COMPRA';
COMMENT ON TRIGGER TRG_LCP_NOTIFICACAO_BI IS 'Auto-incremento da PK da tabela LCP_NOTIFICACAO';
COMMENT ON TRIGGER TRG_LCP_PUSH_SUBSCRIPTION_BI IS 'Auto-incremento da PK da tabela LCP_PUSH_SUBSCRIPTION';
COMMENT ON TRIGGER TRG_LCP_PUSH_LOG_BI IS 'Auto-incremento da PK da tabela LCP_PUSH_LOG';
COMMENT ON TRIGGER TRG_LCP_LOG_AUDITORIA_BI IS 'Auto-incremento da PK da tabela LCP_LOG_AUDITORIA';

COMMENT ON TRIGGER TRG_AUDIT_LCP_USUARIO IS 'Auditoria de operacoes na tabela LCP_USUARIO';
COMMENT ON TRIGGER TRG_AUDIT_LCP_PRESENTE IS 'Auditoria de operacoes na tabela LCP_PRESENTE';
COMMENT ON TRIGGER TRG_AUDIT_LCP_COMPRA IS 'Auditoria de operacoes na tabela LCP_COMPRA';
COMMENT ON TRIGGER TRG_AUDIT_LCP_SUGESTAO_COMPRA IS 'Auditoria de operacoes na tabela LCP_SUGESTAO_COMPRA';
COMMENT ON TRIGGER TRG_AUDIT_LCP_NOTIFICACAO IS 'Auditoria de operacoes na tabela LCP_NOTIFICACAO';
COMMENT ON TRIGGER TRG_AUDIT_LCP_PUSH_SUBSCRIPTION IS 'Auditoria de operacoes na tabela LCP_PUSH_SUBSCRIPTION';


-- ==============================================================================
-- FIM DO SCRIPT DE TRIGGERS
-- ==============================================================================

PROMPT
PROMPT =====================================================================
PROMPT Triggers de Auditoria e Sequences instalados com sucesso!
PROMPT =====================================================================
PROMPT
PROMPT Triggers de Auto-incremento criados para:
PROMPT   - LCP_USUARIO
PROMPT   - LCP_PRESENTE
PROMPT   - LCP_COMPRA
PROMPT   - LCP_SUGESTAO_COMPRA
PROMPT   - LCP_NOTIFICACAO
PROMPT   - LCP_PUSH_SUBSCRIPTION
PROMPT   - LCP_PUSH_LOG
PROMPT   - LCP_LOG_AUDITORIA
PROMPT
PROMPT Triggers de Auditoria criados para:
PROMPT   - LCP_USUARIO (INSERT, UPDATE, DELETE)
PROMPT   - LCP_PRESENTE (INSERT, UPDATE, DELETE)
PROMPT   - LCP_COMPRA (INSERT, UPDATE, DELETE)
PROMPT   - LCP_SUGESTAO_COMPRA (INSERT, UPDATE, DELETE)
PROMPT   - LCP_NOTIFICACAO (INSERT, UPDATE, DELETE)
PROMPT   - LCP_PUSH_SUBSCRIPTION (INSERT, UPDATE, DELETE)
PROMPT
PROMPT Todos os logs serao gravados em LCP_LOG_AUDITORIA
PROMPT =====================================================================
