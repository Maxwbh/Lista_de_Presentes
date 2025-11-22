-- ==============================================================================
-- SCRIPT DE CRIACAO DE TABELAS - LISTA DE PRESENTES
-- Oracle 26 / Apex 24
-- Data: 2025-11-21
-- Desenvolvedor: Maxwell da Silva Oliveira (@maxwbh)
-- Email: maxwbh@gmail.com
-- Empresa: M&S do Brasil LTDA - msbrasil.inf.br
-- ==============================================================================

-- ==============================================================================
-- TABELA: LCP_USUARIO
-- Descricao: Armazena informacoes dos usuarios do sistema
-- Prefixo: LCP = Lista de Compras de Presentes
-- ==============================================================================
CREATE TABLE LCP_USUARIO (
    ID                  NUMBER(10)      NOT NULL,
    USERNAME            VARCHAR2(150)   NOT NULL,
    EMAIL               VARCHAR2(255)   NOT NULL,
    SENHA_HASH          VARCHAR2(255)   NOT NULL,
    PRIMEIRO_NOME       VARCHAR2(150),
    ULTIMO_NOME         VARCHAR2(150),
    TELEFONE            VARCHAR2(20),
    ATIVO               CHAR(1)         DEFAULT 'S' NOT NULL,
    IS_SUPERUSER        CHAR(1)         DEFAULT 'N' NOT NULL,
    IS_STAFF            CHAR(1)         DEFAULT 'N' NOT NULL,
    DATA_CADASTRO       DATE            DEFAULT SYSDATE NOT NULL,
    DATA_LOGIN          DATE,
    DATA_ALTERACAO      DATE            DEFAULT SYSDATE NOT NULL,
    CONSTRAINT PK_LCP_USUARIO PRIMARY KEY (ID),
    CONSTRAINT UK_LCP_USUARIO_EMAIL UNIQUE (EMAIL),
    CONSTRAINT UK_LCP_USUARIO_USERNAME UNIQUE (USERNAME),
    CONSTRAINT CK_LCP_USUARIO_ATIVO CHECK (ATIVO IN ('S', 'N')),
    CONSTRAINT CK_LCP_USUARIO_SUPERUSER CHECK (IS_SUPERUSER IN ('S', 'N')),
    CONSTRAINT CK_LCP_USUARIO_STAFF CHECK (IS_STAFF IN ('S', 'N'))
);

-- Comentarios da tabela
COMMENT ON TABLE LCP_USUARIO IS 'Tabela de usuarios do sistema de lista de presentes';
COMMENT ON COLUMN LCP_USUARIO.ID IS 'Chave primaria - Identificador unico do usuario';
COMMENT ON COLUMN LCP_USUARIO.USERNAME IS 'Nome de usuario para login';
COMMENT ON COLUMN LCP_USUARIO.EMAIL IS 'Email do usuario (usado como login principal)';
COMMENT ON COLUMN LCP_USUARIO.SENHA_HASH IS 'Hash da senha do usuario (SHA-256)';
COMMENT ON COLUMN LCP_USUARIO.ATIVO IS 'Indica se usuario esta ativo (S/N)';
COMMENT ON COLUMN LCP_USUARIO.IS_SUPERUSER IS 'Indica se usuario e administrador (S/N)';

-- Sequence
CREATE SEQUENCE SEQ_LCP_USUARIO START WITH 1 INCREMENT BY 1 NOCACHE;


-- ==============================================================================
-- TABELA: LCP_PRESENTE
-- Descricao: Armazena os presentes cadastrados pelos usuarios
-- ==============================================================================
CREATE TABLE LCP_PRESENTE (
    ID                  NUMBER(10)      NOT NULL,
    ID_USUARIO          NUMBER(10)      NOT NULL,
    DESCRICAO           CLOB            NOT NULL,
    URL                 VARCHAR2(1000),
    PRECO               NUMBER(10,2),
    STATUS              VARCHAR2(20)    DEFAULT 'ATIVO' NOT NULL,
    -- Campos de imagem
    IMAGEM_BASE64       CLOB,
    IMAGEM_NOME         VARCHAR2(255),
    IMAGEM_TIPO         VARCHAR2(50),
    -- Auditoria
    DATA_CADASTRO       DATE            DEFAULT SYSDATE NOT NULL,
    DATA_ALTERACAO      DATE            DEFAULT SYSDATE NOT NULL,
    CONSTRAINT PK_LCP_PRESENTE PRIMARY KEY (ID),
    CONSTRAINT FK_LCP_PRESENTE_USUARIO FOREIGN KEY (ID_USUARIO)
        REFERENCES LCP_USUARIO(ID) ON DELETE CASCADE,
    CONSTRAINT CK_LCP_PRESENTE_STATUS CHECK (STATUS IN ('ATIVO', 'COMPRADO')),
    CONSTRAINT CK_LCP_PRESENTE_PRECO CHECK (PRECO >= 0)
);

-- Comentarios
COMMENT ON TABLE LCP_PRESENTE IS 'Tabela de presentes desejados pelos usuarios';
COMMENT ON COLUMN LCP_PRESENTE.ID IS 'Chave primaria - Identificador unico do presente';
COMMENT ON COLUMN LCP_PRESENTE.ID_USUARIO IS 'Chave estrangeira - Usuario dono do presente';
COMMENT ON COLUMN LCP_PRESENTE.STATUS IS 'Status do presente (ATIVO/COMPRADO)';
COMMENT ON COLUMN LCP_PRESENTE.IMAGEM_BASE64 IS 'Imagem do presente codificada em Base64';
COMMENT ON COLUMN LCP_PRESENTE.IMAGEM_TIPO IS 'MIME type da imagem (image/jpeg, image/png, etc)';

-- Sequence
CREATE SEQUENCE SEQ_LCP_PRESENTE START WITH 1 INCREMENT BY 1 NOCACHE;


-- ==============================================================================
-- TABELA: LCP_COMPRA
-- Descricao: Registra as compras de presentes
-- ==============================================================================
CREATE TABLE LCP_COMPRA (
    ID                  NUMBER(10)      NOT NULL,
    ID_PRESENTE         NUMBER(10)      NOT NULL,
    ID_COMPRADOR        NUMBER(10)      NOT NULL,
    DATA_COMPRA         DATE            DEFAULT SYSDATE NOT NULL,
    CONSTRAINT PK_LCP_COMPRA PRIMARY KEY (ID),
    CONSTRAINT UK_LCP_COMPRA_PRESENTE UNIQUE (ID_PRESENTE),
    CONSTRAINT FK_LCP_COMPRA_PRESENTE FOREIGN KEY (ID_PRESENTE)
        REFERENCES LCP_PRESENTE(ID) ON DELETE CASCADE,
    CONSTRAINT FK_LCP_COMPRA_COMPRADOR FOREIGN KEY (ID_COMPRADOR)
        REFERENCES LCP_USUARIO(ID) ON DELETE CASCADE
);

-- Comentarios
COMMENT ON TABLE LCP_COMPRA IS 'Tabela de registro de compras de presentes';
COMMENT ON COLUMN LCP_COMPRA.ID IS 'Chave primaria - Identificador unico da compra';
COMMENT ON COLUMN LCP_COMPRA.ID_PRESENTE IS 'Chave estrangeira - Presente comprado';
COMMENT ON COLUMN LCP_COMPRA.ID_COMPRADOR IS 'Chave estrangeira - Usuario que comprou';

-- Sequence
CREATE SEQUENCE SEQ_LCP_COMPRA START WITH 1 INCREMENT BY 1 NOCACHE;


-- ==============================================================================
-- TABELA: LCP_SUGESTAO_COMPRA
-- Descricao: Armazena sugestoes de onde comprar os presentes
-- ==============================================================================
CREATE TABLE LCP_SUGESTAO_COMPRA (
    ID                  NUMBER(10)      NOT NULL,
    ID_PRESENTE         NUMBER(10)      NOT NULL,
    LOCAL_COMPRA        VARCHAR2(200)   NOT NULL,
    URL_COMPRA          VARCHAR2(1000)  NOT NULL,
    PRECO_SUGERIDO      NUMBER(10,2),
    DATA_BUSCA          DATE            DEFAULT SYSDATE NOT NULL,
    CONSTRAINT PK_LCP_SUGESTAO_COMPRA PRIMARY KEY (ID),
    CONSTRAINT FK_LCP_SUGESTAO_PRESENTE FOREIGN KEY (ID_PRESENTE)
        REFERENCES LCP_PRESENTE(ID) ON DELETE CASCADE,
    CONSTRAINT CK_LCP_SUGESTAO_PRECO CHECK (PRECO_SUGERIDO IS NULL OR PRECO_SUGERIDO >= 0)
);

-- Comentarios
COMMENT ON TABLE LCP_SUGESTAO_COMPRA IS 'Tabela de sugestoes de onde comprar presentes';
COMMENT ON COLUMN LCP_SUGESTAO_COMPRA.ID IS 'Chave primaria - Identificador unico da sugestao';
COMMENT ON COLUMN LCP_SUGESTAO_COMPRA.LOCAL_COMPRA IS 'Nome da loja/local de compra';
COMMENT ON COLUMN LCP_SUGESTAO_COMPRA.URL_COMPRA IS 'URL do produto na loja';
COMMENT ON COLUMN LCP_SUGESTAO_COMPRA.PRECO_SUGERIDO IS 'Preco encontrado na loja';

-- Sequence
CREATE SEQUENCE SEQ_LCP_SUGESTAO_COMPRA START WITH 1 INCREMENT BY 1 NOCACHE;


-- ==============================================================================
-- TABELA: LCP_NOTIFICACAO
-- Descricao: Armazena notificacoes para os usuarios
-- ==============================================================================
CREATE TABLE LCP_NOTIFICACAO (
    ID                  NUMBER(10)      NOT NULL,
    ID_USUARIO          NUMBER(10)      NOT NULL,
    MENSAGEM            CLOB            NOT NULL,
    LIDA                CHAR(1)         DEFAULT 'N' NOT NULL,
    DATA_NOTIFICACAO    DATE            DEFAULT SYSDATE NOT NULL,
    DATA_LEITURA        DATE,
    CONSTRAINT PK_LCP_NOTIFICACAO PRIMARY KEY (ID),
    CONSTRAINT FK_LCP_NOTIFICACAO_USUARIO FOREIGN KEY (ID_USUARIO)
        REFERENCES LCP_USUARIO(ID) ON DELETE CASCADE,
    CONSTRAINT CK_LCP_NOTIFICACAO_LIDA CHECK (LIDA IN ('S', 'N'))
);

-- Comentarios
COMMENT ON TABLE LCP_NOTIFICACAO IS 'Tabela de notificacoes para usuarios';
COMMENT ON COLUMN LCP_NOTIFICACAO.ID IS 'Chave primaria - Identificador unico da notificacao';
COMMENT ON COLUMN LCP_NOTIFICACAO.LIDA IS 'Indica se notificacao foi lida (S/N)';

-- Sequence
CREATE SEQUENCE SEQ_LCP_NOTIFICACAO START WITH 1 INCREMENT BY 1 NOCACHE;


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
    CONSTRAINT PK_LCP_PUSH_SUBSCRIPTION PRIMARY KEY (ID),
    CONSTRAINT FK_LCP_PUSH_SUBSCRIPTION_USR FOREIGN KEY (ID_USUARIO)
        REFERENCES LCP_USUARIO(ID) ON DELETE CASCADE,
    CONSTRAINT UK_LCP_PUSH_ENDPOINT UNIQUE (ENDPOINT),
    CONSTRAINT CK_LCP_PUSH_ATIVO CHECK (ATIVO IN ('S', 'N'))
);

-- Comentarios
COMMENT ON TABLE LCP_PUSH_SUBSCRIPTION IS 'Tabela de subscricoes de push notifications';
COMMENT ON COLUMN LCP_PUSH_SUBSCRIPTION.ID IS 'Chave primaria - Identificador unico da subscription';
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
    CONSTRAINT PK_LCP_PUSH_LOG PRIMARY KEY (ID),
    CONSTRAINT FK_LCP_PUSH_LOG_SUBSCRIPTION FOREIGN KEY (ID_SUBSCRIPTION)
        REFERENCES LCP_PUSH_SUBSCRIPTION(ID) ON DELETE CASCADE,
    CONSTRAINT FK_LCP_PUSH_LOG_NOTIFICACAO FOREIGN KEY (ID_NOTIFICACAO)
        REFERENCES LCP_NOTIFICACAO(ID) ON DELETE SET NULL,
    CONSTRAINT CK_LCP_PUSH_LOG_STATUS CHECK (STATUS IN ('ENVIADO', 'ERRO', 'PENDENTE'))
);

-- Comentarios
COMMENT ON TABLE LCP_PUSH_LOG IS 'Log de envios de push notifications';
COMMENT ON COLUMN LCP_PUSH_LOG.ID IS 'Chave primaria - Identificador unico do log';
COMMENT ON COLUMN LCP_PUSH_LOG.STATUS IS 'Status do envio (ENVIADO/ERRO/PENDENTE)';

-- Sequence
CREATE SEQUENCE SEQ_LCP_PUSH_LOG START WITH 1 INCREMENT BY 1 NOCACHE;


-- ==============================================================================
-- TABELA: LCP_LOG_AUDITORIA
-- Descricao: Tabela para auditoria de operacoes
-- ==============================================================================
CREATE TABLE LCP_LOG_AUDITORIA (
    ID                  NUMBER(10)      NOT NULL,
    TABELA              VARCHAR2(50)    NOT NULL,
    ID_REGISTRO         NUMBER(10),
    OPERACAO            VARCHAR2(10)    NOT NULL,
    USUARIO_BD          VARCHAR2(100)   DEFAULT USER NOT NULL,
    ID_USUARIO_APP      NUMBER(10),
    DATA_OPERACAO       DATE            DEFAULT SYSDATE NOT NULL,
    DADOS_ANTES         CLOB,
    DADOS_DEPOIS        CLOB,
    CONSTRAINT PK_LCP_LOG_AUDITORIA PRIMARY KEY (ID),
    CONSTRAINT CK_LCP_LOG_OPERACAO CHECK (OPERACAO IN ('INSERT', 'UPDATE', 'DELETE'))
);

-- Comentarios
COMMENT ON TABLE LCP_LOG_AUDITORIA IS 'Tabela de auditoria de operacoes do sistema';
COMMENT ON COLUMN LCP_LOG_AUDITORIA.ID IS 'Chave primaria - Identificador unico do log';
COMMENT ON COLUMN LCP_LOG_AUDITORIA.TABELA IS 'Nome da tabela auditada';
COMMENT ON COLUMN LCP_LOG_AUDITORIA.OPERACAO IS 'Tipo de operacao (INSERT/UPDATE/DELETE)';

-- Sequence
CREATE SEQUENCE SEQ_LCP_LOG_AUDITORIA START WITH 1 INCREMENT BY 1 NOCACHE;


-- ==============================================================================
-- VIEWS
-- ==============================================================================

-- View de Presentes com informacoes completas
CREATE OR REPLACE VIEW VW_LCP_PRESENTES_COMPLETO AS
SELECT
    p.ID,
    p.DESCRICAO,
    p.URL,
    p.PRECO,
    p.STATUS,
    p.DATA_CADASTRO,
    -- Usuario
    p.ID_USUARIO,
    u.EMAIL AS USUARIO_EMAIL,
    u.PRIMEIRO_NOME || ' ' || u.ULTIMO_NOME AS USUARIO_NOME,
    -- Compra (se houver)
    c.ID AS ID_COMPRA,
    c.DATA_COMPRA,
    c.ID_COMPRADOR,
    comp.PRIMEIRO_NOME || ' ' || comp.ULTIMO_NOME AS COMPRADOR_NOME,
    -- Estatisticas
    (SELECT COUNT(*)
     FROM LCP_SUGESTAO_COMPRA s
     WHERE s.ID_PRESENTE = p.ID) AS TOTAL_SUGESTOES,
    (SELECT MIN(PRECO_SUGERIDO)
     FROM LCP_SUGESTAO_COMPRA s
     WHERE s.ID_PRESENTE = p.ID
       AND PRECO_SUGERIDO IS NOT NULL) AS MELHOR_PRECO
FROM LCP_PRESENTE p
INNER JOIN LCP_USUARIO u ON p.ID_USUARIO = u.ID
LEFT JOIN LCP_COMPRA c ON p.ID = c.ID_PRESENTE
LEFT JOIN LCP_USUARIO comp ON c.ID_COMPRADOR = comp.ID;

COMMENT ON VIEW VW_LCP_PRESENTES_COMPLETO IS 'View consolidada de presentes com informacoes de usuario e compra';

-- View de Dashboard
CREATE OR REPLACE VIEW VW_LCP_DASHBOARD AS
SELECT
    (SELECT COUNT(*) FROM LCP_USUARIO WHERE ATIVO = 'S') AS TOTAL_USUARIOS,
    (SELECT COUNT(*) FROM LCP_PRESENTE WHERE STATUS = 'ATIVO') AS TOTAL_PRESENTES_ATIVOS,
    (SELECT COUNT(*) FROM LCP_PRESENTE WHERE STATUS = 'COMPRADO') AS TOTAL_PRESENTES_COMPRADOS,
    (SELECT COUNT(*) FROM LCP_COMPRA WHERE TRUNC(DATA_COMPRA) = TRUNC(SYSDATE)) AS COMPRAS_HOJE,
    (SELECT COUNT(*) FROM LCP_NOTIFICACAO WHERE LIDA = 'N') AS NOTIFICACOES_NAO_LIDAS,
    (SELECT COUNT(*) FROM LCP_PUSH_SUBSCRIPTION WHERE ATIVO = 'S') AS PUSH_SUBSCRIPTIONS_ATIVAS
FROM DUAL;

COMMENT ON VIEW VW_LCP_DASHBOARD IS 'View de dashboard com estatisticas gerais do sistema';

-- View de Estatisticas por Usuario
CREATE OR REPLACE VIEW VW_LCP_USUARIO_ESTATISTICAS AS
SELECT
    u.ID,
    u.EMAIL,
    u.PRIMEIRO_NOME || ' ' || u.ULTIMO_NOME AS NOME_COMPLETO,
    u.DATA_CADASTRO,
    COUNT(p.ID) AS TOTAL_PRESENTES,
    SUM(CASE WHEN p.STATUS = 'ATIVO' THEN 1 ELSE 0 END) AS PRESENTES_ATIVOS,
    SUM(CASE WHEN p.STATUS = 'COMPRADO' THEN 1 ELSE 0 END) AS PRESENTES_COMPRADOS,
    (SELECT COUNT(*)
     FROM LCP_NOTIFICACAO n
     WHERE n.ID_USUARIO = u.ID
       AND n.LIDA = 'N') AS NOTIFICACOES_NAO_LIDAS,
    (SELECT COUNT(*)
     FROM LCP_PUSH_SUBSCRIPTION ps
     WHERE ps.ID_USUARIO = u.ID
       AND ps.ATIVO = 'S') AS PUSH_SUBSCRIPTIONS_ATIVAS
FROM LCP_USUARIO u
LEFT JOIN LCP_PRESENTE p ON u.ID = p.ID_USUARIO
WHERE u.ATIVO = 'S'
GROUP BY u.ID, u.EMAIL, u.PRIMEIRO_NOME, u.ULTIMO_NOME, u.DATA_CADASTRO;

COMMENT ON VIEW VW_LCP_USUARIO_ESTATISTICAS IS 'View de estatisticas por usuario';

-- View de Estatisticas de Push Notifications
CREATE OR REPLACE VIEW VW_LCP_PUSH_ESTATISTICAS AS
SELECT
    u.ID AS ID_USUARIO,
    u.PRIMEIRO_NOME || ' ' || u.ULTIMO_NOME AS NOME_USUARIO,
    u.EMAIL,
    COUNT(ps.ID) AS TOTAL_SUBSCRIPTIONS,
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
FROM LCP_USUARIO u
LEFT JOIN LCP_PUSH_SUBSCRIPTION ps ON u.ID = ps.ID_USUARIO
WHERE u.ATIVO = 'S'
GROUP BY u.ID, u.PRIMEIRO_NOME, u.ULTIMO_NOME, u.EMAIL;

COMMENT ON VIEW VW_LCP_PUSH_ESTATISTICAS IS 'Estatisticas de push notifications por usuario';


-- ==============================================================================
-- FIM DO SCRIPT DDL
-- ==============================================================================
