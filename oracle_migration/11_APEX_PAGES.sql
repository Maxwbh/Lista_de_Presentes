-- ==============================================================================
-- DEFINICAO DE PAGINAS APEX - LISTA DE PRESENTES
-- Oracle APEX 24 / Oracle 26
-- Data: 2025-11-21
-- Desenvolvedor: Maxwell da Silva Oliveira (@maxwbh)
-- Email: maxwbh@gmail.com
-- Empresa: M&S do Brasil LTDA - msbrasil.inf.br
-- ==============================================================================
--
-- Este arquivo contem as instrucoes para criar as paginas da aplicacao APEX
-- Use como referencia para criar as paginas manualmente no App Builder
--
-- ==============================================================================

/*
================================================================================
ESTRUTURA DE PAGINAS DA APLICACAO
================================================================================

Pagina  | Nome                    | Tipo              | Autenticacao
--------|-------------------------|-------------------|-------------
1       | Home / Dashboard        | Normal            | Sim
2       | Login                   | Login             | Nao
3       | Registro                | Normal            | Nao
9999    | Global Page             | Global            | -
--------|-----------------------------|-------------------|-------------
10      | Meus Presentes          | Normal            | Sim
11      | Adicionar Presente      | Modal Dialog      | Sim
12      | Editar Presente         | Modal Dialog      | Sim
13      | Detalhe Presente        | Modal Dialog      | Sim
--------|-------------------------|-------------------|-------------
20      | Presentes Disponiveis   | Normal            | Sim
21      | Comprar Presente        | Modal Dialog      | Sim
22      | Lista de Usuario        | Normal            | Sim
--------|-------------------------|-------------------|-------------
30      | Notificacoes            | Normal            | Sim
--------|-------------------------|-------------------|-------------
40      | Meu Perfil              | Normal            | Sim
41      | Alterar Senha           | Modal Dialog      | Sim
--------|-------------------------|-------------------|-------------
50      | Admin - Usuarios        | Normal            | Admin
51      | Admin - Dashboard       | Normal            | Admin
--------|-------------------------|-------------------|-------------
100     | Sobre                   | Normal            | Nao

================================================================================
*/


-- ==============================================================================
-- PAGINA 1: HOME / DASHBOARD
-- ==============================================================================
/*
TITULO: Dashboard
TIPO: Normal Page
TEMPLATE: Standard

REGIOES:
---------
1. Boas-vindas (Static Content)
   - Tipo: Static Content
   - Template: Hero
   - SQL: N/A
   - Conteudo HTML:
*/

-- HTML para regiao de boas-vindas
/*
<div class="t-HeroRegion-wrap">
    <div class="t-HeroRegion-col t-HeroRegion-col--content">
        <h1 class="t-HeroRegion-title">Bem-vindo, &APP_USER.!</h1>
        <p class="t-HeroRegion-desc">Gerencie sua lista de presentes e veja o que seus amigos desejam.</p>
    </div>
</div>
*/

/*
2. Cards de Estatisticas (Cards Region)
   - Tipo: Cards
   - Template: Standard
   - Source SQL:
*/
-- SQL para cards de estatisticas
SELECT
    'fa-gift' AS CARD_ICON,
    presentes_ativos AS CARD_VALUE,
    'Presentes Ativos' AS CARD_LABEL,
    'f?p=&APP_ID.:10:&SESSION.' AS CARD_LINK
FROM VW_APEX_DASHBOARD
WHERE ID_USUARIO = FN_APEX_GET_USER_ID
UNION ALL
SELECT
    'fa-check-circle',
    presentes_comprados,
    'Presentes Comprados',
    'f?p=&APP_ID.:10:&SESSION.::NO::P10_STATUS:COMPRADO'
FROM VW_APEX_DASHBOARD
WHERE ID_USUARIO = FN_APEX_GET_USER_ID
UNION ALL
SELECT
    'fa-bell',
    notif_nao_lidas,
    'Notificacoes',
    'f?p=&APP_ID.:30:&SESSION.'
FROM VW_APEX_DASHBOARD
WHERE ID_USUARIO = FN_APEX_GET_USER_ID
UNION ALL
SELECT
    'fa-shopping-cart',
    compras_realizadas,
    'Compras Realizadas',
    'f?p=&APP_ID.:20:&SESSION.'
FROM VW_APEX_DASHBOARD
WHERE ID_USUARIO = FN_APEX_GET_USER_ID;


/*
3. Ultimos Presentes Adicionados (Classic Report)
   - Tipo: Classic Report
   - Template: Standard
   - Source SQL:
*/
SELECT
    ID,
    DESCRICAO,
    FN_APEX_FORMATAR_PRECO(PRECO) AS PRECO_FORMATADO,
    FN_APEX_BADGE_STATUS(STATUS) AS STATUS_BADGE,
    TO_CHAR(DATA_CADASTRO, 'DD/MM/YYYY') AS DATA
FROM VW_APEX_MEUS_PRESENTES
WHERE ID_USUARIO = FN_APEX_GET_USER_ID
ORDER BY DATA_CADASTRO DESC
FETCH FIRST 5 ROWS ONLY;


/*
4. Ultimas Notificacoes (Classic Report)
   - Tipo: Classic Report
   - Template: Standard
   - Source SQL:
*/
SELECT
    ID,
    MENSAGEM,
    DATA_FORMATADA,
    CASE WHEN LIDA = 'N' THEN 'u-color-danger' ELSE '' END AS ROW_CLASS
FROM VW_APEX_NOTIFICACOES
WHERE ID_USUARIO = FN_APEX_GET_USER_ID
ORDER BY DATA_NOTIFICACAO DESC
FETCH FIRST 5 ROWS ONLY;


-- ==============================================================================
-- PAGINA 10: MEUS PRESENTES
-- ==============================================================================
/*
TITULO: Meus Presentes
TIPO: Normal Page (Interactive Report)
TEMPLATE: Standard

ITEMS:
------
P10_STATUS - Select List (filtro)
  - LOV: STATIC:Todos;,Ativos;ATIVO,Comprados;COMPRADO

BOTOES:
-------
BTN_ADICIONAR - Redirect to Page 11 (Modal)

REGIOES:
--------
1. Meus Presentes (Interactive Report)
   - Source SQL:
*/
SELECT
    p.ID,
    p.DESCRICAO,
    p.URL,
    FN_APEX_FORMATAR_PRECO(p.PRECO) AS PRECO,
    FN_APEX_BADGE_STATUS(p.STATUS) AS STATUS,
    p.TEM_IMAGEM,
    p.TOTAL_SUGESTOES,
    FN_APEX_FORMATAR_PRECO(p.MELHOR_PRECO) AS MELHOR_PRECO,
    TO_CHAR(p.DATA_CADASTRO, 'DD/MM/YYYY HH24:MI') AS DATA_CADASTRO,
    p.COMPRADOR_NOME,
    TO_CHAR(p.DATA_COMPRA, 'DD/MM/YYYY') AS DATA_COMPRA,
    -- Acoes
    APEX_PAGE.GET_URL(
        p_page => 12,
        p_items => 'P12_ID',
        p_values => p.ID
    ) AS LINK_EDITAR,
    APEX_PAGE.GET_URL(
        p_page => 13,
        p_items => 'P13_ID',
        p_values => p.ID
    ) AS LINK_DETALHE
FROM VW_APEX_MEUS_PRESENTES p
WHERE p.ID_USUARIO = FN_APEX_GET_USER_ID
  AND (:P10_STATUS IS NULL OR p.STATUS = :P10_STATUS)
ORDER BY p.DATA_CADASTRO DESC;


-- ==============================================================================
-- PAGINA 11: ADICIONAR PRESENTE (Modal)
-- ==============================================================================
/*
TITULO: Adicionar Presente
TIPO: Modal Dialog
TEMPLATE: Inline Dialog

ITEMS:
------
P11_DESCRICAO - Textarea (Required)
P11_URL - Text Field
P11_PRECO - Number Field
P11_IMAGEM - File Browse (BLOB column)

BOTOES:
-------
BTN_SALVAR - Submit Page
BTN_CANCELAR - Close Dialog

PROCESSOS:
----------
1. Inserir Presente (On Submit)
*/
-- Processo PL/SQL para inserir presente
DECLARE
    v_id NUMBER;
    v_imagem_base64 CLOB;
    v_imagem_nome VARCHAR2(255);
    v_imagem_tipo VARCHAR2(100);
BEGIN
    -- Converter imagem para base64 se houver
    IF :P11_IMAGEM IS NOT NULL THEN
        SELECT
            APEX_WEB_SERVICE.BLOB2CLOBBASE64(BLOB_CONTENT),
            FILENAME,
            MIME_TYPE
        INTO v_imagem_base64, v_imagem_nome, v_imagem_tipo
        FROM APEX_APPLICATION_TEMP_FILES
        WHERE NAME = :P11_IMAGEM;
    END IF;

    -- Chamar procedure APEX
    PRC_APEX_ADICIONAR_PRESENTE(
        p_descricao     => :P11_DESCRICAO,
        p_url           => :P11_URL,
        p_preco         => :P11_PRECO,
        p_imagem_base64 => v_imagem_base64,
        p_imagem_nome   => v_imagem_nome,
        p_imagem_tipo   => v_imagem_tipo,
        p_id_presente   => v_id
    );

    -- Mensagem de sucesso
    APEX_APPLICATION.G_PRINT_SUCCESS_MESSAGE := 'Presente adicionado com sucesso!';
END;


-- ==============================================================================
-- PAGINA 12: EDITAR PRESENTE (Modal)
-- ==============================================================================
/*
TITULO: Editar Presente
TIPO: Modal Dialog
TEMPLATE: Inline Dialog

ITEMS:
------
P12_ID - Hidden (Primary Key)
P12_DESCRICAO - Textarea
P12_URL - Text Field
P12_PRECO - Number Field
P12_IMAGEM - File Browse

PRE-RENDERING PROCESS:
---------------------
Carregar dados do presente
*/
-- Processo para carregar dados
SELECT
    DESCRICAO,
    URL,
    PRECO
INTO
    :P12_DESCRICAO,
    :P12_URL,
    :P12_PRECO
FROM LCP_PRESENTE
WHERE ID = :P12_ID
  AND ID_USUARIO = FN_APEX_GET_USER_ID;

-- Processo para atualizar
BEGIN
    PKG_PRESENTE.ATUALIZAR_PRESENTE(
        p_id_presente   => :P12_ID,
        p_id_usuario    => FN_APEX_GET_USER_ID,
        p_descricao     => :P12_DESCRICAO,
        p_url           => :P12_URL,
        p_preco         => :P12_PRECO
    );

    APEX_APPLICATION.G_PRINT_SUCCESS_MESSAGE := 'Presente atualizado com sucesso!';
END;


-- ==============================================================================
-- PAGINA 20: PRESENTES DISPONIVEIS
-- ==============================================================================
/*
TITULO: Presentes Disponiveis
TIPO: Normal Page (Cards)
TEMPLATE: Standard

ITEMS:
------
P20_BUSCA - Text Field (filtro)
P20_PRECO_MIN - Number Field
P20_PRECO_MAX - Number Field

REGIOES:
--------
1. Presentes Disponiveis (Cards)
   - Source SQL:
*/
SELECT
    p.ID AS CARD_ID,
    p.DESCRICAO AS CARD_TITLE,
    p.NOME_DONO AS CARD_SUBTITLE,
    FN_APEX_FORMATAR_PRECO(COALESCE(p.MELHOR_PRECO, p.PRECO)) AS CARD_TEXT,
    CASE WHEN p.TEM_IMAGEM = 'S'
        THEN 'f?p=&APP_ID.:0:&SESSION.:APPLICATION_PROCESS=GET_IMAGEM:::P_ID:' || p.ID
        ELSE '#APP_FILES#images/gift-default.png'
    END AS CARD_IMAGE,
    APEX_PAGE.GET_URL(
        p_page => 21,
        p_items => 'P21_ID',
        p_values => p.ID
    ) AS CARD_LINK,
    'fa-gift' AS CARD_ICON,
    CASE WHEN p.TOTAL_SUGESTOES > 0
        THEN p.TOTAL_SUGESTOES || ' sugestoes'
        ELSE 'Sem sugestoes'
    END AS CARD_BADGE
FROM VW_APEX_PRESENTES_OUTROS p
WHERE p.ID_USUARIO != FN_APEX_GET_USER_ID
  AND (:P20_BUSCA IS NULL OR UPPER(p.DESCRICAO) LIKE '%' || UPPER(:P20_BUSCA) || '%')
  AND (:P20_PRECO_MIN IS NULL OR COALESCE(p.MELHOR_PRECO, p.PRECO) >= :P20_PRECO_MIN)
  AND (:P20_PRECO_MAX IS NULL OR COALESCE(p.MELHOR_PRECO, p.PRECO) <= :P20_PRECO_MAX)
ORDER BY p.DATA_CADASTRO DESC;


-- ==============================================================================
-- PAGINA 21: COMPRAR PRESENTE (Modal)
-- ==============================================================================
/*
TITULO: Comprar Presente
TIPO: Modal Dialog

ITEMS:
------
P21_ID - Hidden
P21_DESCRICAO - Display Only
P21_DONO - Display Only
P21_PRECO - Display Only

BOTOES:
-------
BTN_CONFIRMAR_COMPRA - Submit
BTN_CANCELAR - Close Dialog

PROCESSO:
---------
*/
DECLARE
    v_id_compra NUMBER;
BEGIN
    PRC_APEX_COMPRAR_PRESENTE(
        p_id_presente => :P21_ID,
        p_id_compra   => v_id_compra
    );

    APEX_APPLICATION.G_PRINT_SUCCESS_MESSAGE := 'Presente marcado como comprado! O dono sera notificado.';
END;


-- ==============================================================================
-- PAGINA 30: NOTIFICACOES
-- ==============================================================================
/*
TITULO: Notificacoes
TIPO: Normal Page
TEMPLATE: Standard

BOTOES:
-------
BTN_MARCAR_TODAS_LIDAS - Submit

REGIOES:
--------
1. Notificacoes (Classic Report)
   - Source SQL:
*/
SELECT
    n.ID,
    n.MENSAGEM,
    n.LIDA,
    n.DATA_FORMATADA,
    CASE WHEN n.LIDA = 'N'
        THEN '<span class="fa fa-circle u-color-danger"></span>'
        ELSE '<span class="fa fa-check-circle u-color-success"></span>'
    END AS ICON_STATUS,
    APEX_PAGE.GET_URL(
        p_page => 30,
        p_request => 'MARCAR_LIDA',
        p_items => 'P30_ID_NOTIF',
        p_values => n.ID
    ) AS LINK_MARCAR_LIDA
FROM VW_APEX_NOTIFICACOES n
WHERE n.ID_USUARIO = FN_APEX_GET_USER_ID
ORDER BY n.DATA_NOTIFICACAO DESC;

-- Processo para marcar como lida
BEGIN
    IF :REQUEST = 'MARCAR_LIDA' AND :P30_ID_NOTIF IS NOT NULL THEN
        PKG_NOTIFICACAO.MARCAR_LIDA(:P30_ID_NOTIF);
    ELSIF :REQUEST = 'MARCAR_TODAS' THEN
        PKG_NOTIFICACAO.MARCAR_TODAS_LIDAS(FN_APEX_GET_USER_ID);
    END IF;
END;


-- ==============================================================================
-- PAGINA 40: MEU PERFIL
-- ==============================================================================
/*
TITULO: Meu Perfil
TIPO: Normal Page
TEMPLATE: Standard

ITEMS:
------
P40_ID - Hidden
P40_USERNAME - Display Only
P40_EMAIL - Text Field
P40_PRIMEIRO_NOME - Text Field
P40_ULTIMO_NOME - Text Field
P40_TELEFONE - Text Field
P40_DATA_CADASTRO - Display Only

BOTOES:
-------
BTN_SALVAR - Submit
BTN_ALTERAR_SENHA - Redirect to Page 41

PRE-RENDERING:
--------------
*/
DECLARE
    v_usuario PKG_USUARIO.t_usuario;
BEGIN
    v_usuario := PKG_USUARIO.BUSCAR_POR_ID(FN_APEX_GET_USER_ID);

    :P40_ID := v_usuario.id_usuario;
    :P40_USERNAME := v_usuario.username;
    :P40_EMAIL := v_usuario.email;
    :P40_PRIMEIRO_NOME := v_usuario.primeiro_nome;
    :P40_ULTIMO_NOME := v_usuario.ultimo_nome;
    :P40_TELEFONE := v_usuario.telefone;
    :P40_DATA_CADASTRO := TO_CHAR(v_usuario.data_cadastro, 'DD/MM/YYYY');
END;

-- Processo para atualizar perfil
BEGIN
    PKG_USUARIO.ATUALIZAR_USUARIO(
        p_id_usuario    => :P40_ID,
        p_primeiro_nome => :P40_PRIMEIRO_NOME,
        p_ultimo_nome   => :P40_ULTIMO_NOME,
        p_telefone      => :P40_TELEFONE,
        p_email         => :P40_EMAIL
    );

    APEX_APPLICATION.G_PRINT_SUCCESS_MESSAGE := 'Perfil atualizado com sucesso!';
END;


-- ==============================================================================
-- PAGINA 2: LOGIN
-- ==============================================================================
/*
TITULO: Login
TIPO: Login Page
TEMPLATE: Login

Configurar autenticacao customizada:
- Authentication Function: return FN_APEX_AUTENTICAR
- Username: P2_USERNAME
- Password: P2_PASSWORD

Link para registro: Pagina 3
*/


-- ==============================================================================
-- PAGINA 3: REGISTRO
-- ==============================================================================
/*
TITULO: Criar Conta
TIPO: Normal Page (Public)
TEMPLATE: Standard

ITEMS:
------
P3_USERNAME - Text Field (Required)
P3_EMAIL - Text Field (Required)
P3_SENHA - Password (Required)
P3_CONFIRMA_SENHA - Password (Required)
P3_PRIMEIRO_NOME - Text Field (Required)
P3_ULTIMO_NOME - Text Field (Required)
P3_TELEFONE - Text Field

VALIDACOES:
-----------
- Senha = Confirma Senha
- Email valido

PROCESSO:
---------
*/
DECLARE
    v_id NUMBER;
BEGIN
    -- Validar senhas
    IF :P3_SENHA != :P3_CONFIRMA_SENHA THEN
        RAISE_APPLICATION_ERROR(-20001, 'As senhas nao conferem');
    END IF;

    -- Registrar usuario
    PRC_APEX_REGISTRAR_USUARIO(
        p_username      => :P3_USERNAME,
        p_email         => :P3_EMAIL,
        p_senha         => :P3_SENHA,
        p_primeiro_nome => :P3_PRIMEIRO_NOME,
        p_ultimo_nome   => :P3_ULTIMO_NOME,
        p_telefone      => :P3_TELEFONE,
        p_id_usuario    => v_id
    );

    -- Redirecionar para login
    APEX_APPLICATION.G_PRINT_SUCCESS_MESSAGE := 'Conta criada com sucesso! Faca login para continuar.';
END;


-- ==============================================================================
-- PAGINA 9999: GLOBAL PAGE
-- ==============================================================================
/*
TITULO: Global Page
TIPO: Global Page

REGIOES:
--------
1. Badge de Notificacoes (Navigation Bar)
   - Condicao: Usuario logado
   - SQL: SELECT FN_APEX_NOTIF_COUNT FROM DUAL

2. Menu do Usuario (Navigation Bar List)
   - Itens: Meu Perfil, Notificacoes, Sair

JAVASCRIPT GLOBAL:
------------------
*/
-- JavaScript para PWA e Push Notifications
/*
// Registrar Service Worker para PWA
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/pwa/sw.js')
        .then(registration => {
            console.log('ServiceWorker registrado:', registration.scope);
        })
        .catch(error => {
            console.log('Erro ao registrar ServiceWorker:', error);
        });
}

// Solicitar permissao para notificacoes
function solicitarPermissaoNotificacao() {
    if ('Notification' in window) {
        Notification.requestPermission().then(permission => {
            if (permission === 'granted') {
                registrarPushSubscription();
            }
        });
    }
}

// Registrar subscription para push
function registrarPushSubscription() {
    navigator.serviceWorker.ready.then(registration => {
        registration.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY)
        }).then(subscription => {
            // Enviar subscription para o servidor
            apex.server.process('REGISTRAR_PUSH', {
                x01: JSON.stringify(subscription)
            });
        });
    });
}
*/


-- ==============================================================================
-- APPLICATION PROCESS: GET_IMAGEM
-- ==============================================================================
/*
Nome: GET_IMAGEM
Tipo: On Demand (AJAX Callback)
*/
DECLARE
    v_imagem CLOB;
    v_mime VARCHAR2(100);
BEGIN
    SELECT IMAGEM_BASE64, IMAGEM_TIPO
    INTO v_imagem, v_mime
    FROM LCP_PRESENTE
    WHERE ID = :P_ID;

    IF v_imagem IS NOT NULL THEN
        OWA_UTIL.MIME_HEADER(v_mime, FALSE);
        HTP.P(v_imagem);
    END IF;
END;


-- ==============================================================================
-- APPLICATION PROCESS: REGISTRAR_PUSH
-- ==============================================================================
/*
Nome: REGISTRAR_PUSH
Tipo: On Demand (AJAX Callback)
*/
DECLARE
    v_subscription_json CLOB := APEX_APPLICATION.G_X01;
    v_endpoint VARCHAR2(1000);
    v_p256dh VARCHAR2(500);
    v_auth VARCHAR2(500);
    v_id NUMBER;
BEGIN
    -- Parse JSON
    v_endpoint := JSON_VALUE(v_subscription_json, '$.endpoint');
    v_p256dh := JSON_VALUE(v_subscription_json, '$.keys.p256dh');
    v_auth := JSON_VALUE(v_subscription_json, '$.keys.auth');

    -- Registrar
    v_id := PKG_PUSH_NOTIFICATION.REGISTRAR_SUBSCRIPTION(
        p_id_usuario => FN_APEX_GET_USER_ID,
        p_endpoint   => v_endpoint,
        p_p256dh_key => v_p256dh,
        p_auth_key   => v_auth
    );

    HTP.P('{"success": true, "id": ' || v_id || '}');
EXCEPTION
    WHEN OTHERS THEN
        HTP.P('{"success": false, "error": "' || SQLERRM || '"}');
END;


-- ==============================================================================
-- FIM DO ARQUIVO
-- ==============================================================================

PROMPT
PROMPT ========================================
PROMPT Definicoes de Paginas APEX documentadas
PROMPT ========================================
PROMPT
PROMPT Use este arquivo como referencia para criar
PROMPT as paginas no Oracle APEX App Builder.
PROMPT
PROMPT Paginas definidas:
PROMPT   1  - Dashboard
PROMPT   2  - Login
PROMPT   3  - Registro
PROMPT   10 - Meus Presentes
PROMPT   11 - Adicionar Presente (Modal)
PROMPT   12 - Editar Presente (Modal)
PROMPT   20 - Presentes Disponiveis
PROMPT   21 - Comprar Presente (Modal)
PROMPT   30 - Notificacoes
PROMPT   40 - Meu Perfil
PROMPT   9999 - Global Page
PROMPT ========================================
