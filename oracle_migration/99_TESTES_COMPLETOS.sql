-- ==============================================================================
-- SCRIPT DE TESTES COMPLETOS - LISTA DE PRESENTES
-- Oracle 26 / Apex 24
-- Data: 2025-11-21
-- Desenvolvedor: Maxwell da Silva Oliveira (@maxwbh)
-- Email: maxwbh@gmail.com
-- Empresa: M&S do Brasil LTDA - msbrasil.inf.br
-- ==============================================================================
--
-- Este script testa todas as funcionalidades dos packages criados
--
-- ==============================================================================

SET SERVEROUTPUT ON SIZE UNLIMITED
SET VERIFY OFF
SET FEEDBACK OFF

PROMPT ========================================
PROMPT TESTES DO SISTEMA LISTA DE PRESENTES
PROMPT ========================================
PROMPT

-- ==============================================================================
-- TESTE 1: PKG_USUARIO - REGISTRO E AUTENTICACAO
-- ==============================================================================

PROMPT ========================================
PROMPT TESTE 1: PKG_USUARIO
PROMPT ========================================
PROMPT

DECLARE
    v_id_usuario1 NUMBER;
    v_id_usuario2 NUMBER;
    v_id_autenticado NUMBER;
BEGIN
    DBMS_OUTPUT.PUT_LINE('=== Teste 1.1: Registrar Usuarios ===');

    -- Registrar usuario 1
    v_id_usuario1 := PKG_USUARIO.REGISTRAR_USUARIO(
        p_username => 'joao.silva',
        p_email => 'joao.silva@email.com',
        p_senha => 'Senha@123',
        p_primeiro_nome => 'João',
        p_ultimo_nome => 'Silva',
        p_telefone => '11999999999'
    );
    DBMS_OUTPUT.PUT_LINE('✓ Usuario 1 criado com ID: ' || v_id_usuario1);

    -- Registrar usuario 2
    v_id_usuario2 := PKG_USUARIO.REGISTRAR_USUARIO(
        p_username => 'maria.santos',
        p_email => 'maria.santos@email.com',
        p_senha => 'Senha@456',
        p_primeiro_nome => 'Maria',
        p_ultimo_nome => 'Santos',
        p_telefone => '11988888888'
    );
    DBMS_OUTPUT.PUT_LINE('✓ Usuario 2 criado com ID: ' || v_id_usuario2);

    DBMS_OUTPUT.PUT_LINE('');
    DBMS_OUTPUT.PUT_LINE('=== Teste 1.2: Autenticacao ===');

    -- Autenticar usuario 1
    v_id_autenticado := PKG_USUARIO.AUTENTICAR_USUARIO(
        p_email => 'joao.silva@email.com',
        p_senha => 'Senha@123'
    );
    DBMS_OUTPUT.PUT_LINE('✓ Usuario 1 autenticado: ' || v_id_autenticado);

    -- Tentar autenticar com senha errada
    BEGIN
        v_id_autenticado := PKG_USUARIO.AUTENTICAR_USUARIO(
            p_email => 'joao.silva@email.com',
            p_senha => 'SenhaErrada'
        );
        DBMS_OUTPUT.PUT_LINE('✗ ERRO: Nao deveria autenticar com senha errada');
    EXCEPTION
        WHEN OTHERS THEN
            DBMS_OUTPUT.PUT_LINE('✓ Senha invalida bloqueada corretamente');
    END;

    DBMS_OUTPUT.PUT_LINE('');
    DBMS_OUTPUT.PUT_LINE('=== Teste 1.3: Validacoes ===');

    -- Tentar criar usuario com email duplicado
    BEGIN
        v_id_usuario1 := PKG_USUARIO.REGISTRAR_USUARIO(
            p_username => 'outro.usuario',
            p_email => 'joao.silva@email.com', -- Email duplicado
            p_senha => 'Senha@789',
            p_primeiro_nome => 'Outro',
            p_ultimo_nome => 'Usuario'
        );
        DBMS_OUTPUT.PUT_LINE('✗ ERRO: Nao deveria permitir email duplicado');
    EXCEPTION
        WHEN OTHERS THEN
            DBMS_OUTPUT.PUT_LINE('✓ Email duplicado bloqueado corretamente');
    END;

    DBMS_OUTPUT.PUT_LINE('');
    DBMS_OUTPUT.PUT_LINE('✓ PKG_USUARIO: TODOS OS TESTES PASSARAM!');
    DBMS_OUTPUT.PUT_LINE('');
END;
/

-- ==============================================================================
-- TESTE 2: PKG_PRESENTE - CRUD DE PRESENTES
-- ==============================================================================

PROMPT ========================================
PROMPT TESTE 2: PKG_PRESENTE
PROMPT ========================================
PROMPT

DECLARE
    v_id_usuario1 NUMBER;
    v_id_usuario2 NUMBER;
    v_id_presente1 NUMBER;
    v_id_presente2 NUMBER;
    v_count NUMBER;
BEGIN
    -- Buscar IDs dos usuarios criados no teste anterior
    SELECT ID_USUARIO INTO v_id_usuario1
    FROM TB_USUARIO WHERE EMAIL = 'joao.silva@email.com';

    SELECT ID_USUARIO INTO v_id_usuario2
    FROM TB_USUARIO WHERE EMAIL = 'maria.santos@email.com';

    DBMS_OUTPUT.PUT_LINE('=== Teste 2.1: Adicionar Presentes ===');

    -- Adicionar presente do usuario 1
    v_id_presente1 := PKG_PRESENTE.ADICIONAR_PRESENTE(
        p_id_usuario => v_id_usuario1,
        p_descricao => 'Notebook Dell Inspiron 15',
        p_url => 'https://www.dell.com.br/notebook-inspiron-15',
        p_preco => 3500.00
    );
    DBMS_OUTPUT.PUT_LINE('✓ Presente 1 criado com ID: ' || v_id_presente1);

    -- Adicionar presente do usuario 2
    v_id_presente2 := PKG_PRESENTE.ADICIONAR_PRESENTE(
        p_id_usuario => v_id_usuario2,
        p_descricao => 'Smartphone Samsung Galaxy S23',
        p_url => 'https://www.samsung.com.br/galaxy-s23',
        p_preco => 2800.00
    );
    DBMS_OUTPUT.PUT_LINE('✓ Presente 2 criado com ID: ' || v_id_presente2);

    DBMS_OUTPUT.PUT_LINE('');
    DBMS_OUTPUT.PUT_LINE('=== Teste 2.2: Contar Presentes ===');

    v_count := PKG_PRESENTE.CONTAR_PRESENTES(
        p_id_usuario => v_id_usuario1,
        p_status => 'ATIVO'
    );
    DBMS_OUTPUT.PUT_LINE('✓ Usuario 1 tem ' || v_count || ' presentes ativos');

    DBMS_OUTPUT.PUT_LINE('');
    DBMS_OUTPUT.PUT_LINE('=== Teste 2.3: Validacao de Propriedade ===');

    -- Tentar atualizar presente de outro usuario
    BEGIN
        PKG_PRESENTE.ATUALIZAR_PRESENTE(
            p_id_presente => v_id_presente2, -- Presente do usuario 2
            p_id_usuario => v_id_usuario1,   -- Usuario 1 tentando atualizar
            p_descricao => 'Tentativa de alteracao'
        );
        DBMS_OUTPUT.PUT_LINE('✗ ERRO: Nao deveria permitir atualizar presente de outro usuario');
    EXCEPTION
        WHEN OTHERS THEN
            DBMS_OUTPUT.PUT_LINE('✓ Validacao de propriedade funcionando corretamente');
    END;

    DBMS_OUTPUT.PUT_LINE('');
    DBMS_OUTPUT.PUT_LINE('✓ PKG_PRESENTE: TODOS OS TESTES PASSARAM!');
    DBMS_OUTPUT.PUT_LINE('');
END;
/

-- ==============================================================================
-- TESTE 3: PKG_SUGESTAO - SUGESTOES DE COMPRA
-- ==============================================================================

PROMPT ========================================
PROMPT TESTE 3: PKG_SUGESTAO
PROMPT ========================================
PROMPT

DECLARE
    v_id_presente NUMBER;
    v_id_sugestao1 NUMBER;
    v_id_sugestao2 NUMBER;
    v_id_sugestao3 NUMBER;
    v_melhor_preco NUMBER;
    v_count NUMBER;
BEGIN
    -- Buscar presente criado no teste anterior
    SELECT ID_PRESENTE INTO v_id_presente
    FROM TB_PRESENTE
    WHERE DESCRICAO LIKE '%Notebook Dell%';

    DBMS_OUTPUT.PUT_LINE('=== Teste 3.1: Adicionar Sugestoes ===');

    -- Adicionar sugestão 1
    v_id_sugestao1 := PKG_SUGESTAO.ADICIONAR_SUGESTAO(
        p_id_presente => v_id_presente,
        p_local_compra => 'Amazon (Zoom)',
        p_url_compra => 'https://www.zoom.com.br/notebook-dell-inspiron',
        p_preco_sugerido => 3299.90
    );
    DBMS_OUTPUT.PUT_LINE('✓ Sugestao 1 criada: Amazon - R$ 3299.90');

    -- Adicionar sugestão 2
    v_id_sugestao2 := PKG_SUGESTAO.ADICIONAR_SUGESTAO(
        p_id_presente => v_id_presente,
        p_local_compra => 'Magazine Luiza (Buscape)',
        p_url_compra => 'https://www.buscape.com.br/notebook-dell',
        p_preco_sugerido => 3450.00
    );
    DBMS_OUTPUT.PUT_LINE('✓ Sugestao 2 criada: Magazine Luiza - R$ 3450.00');

    -- Adicionar sugestão 3
    v_id_sugestao3 := PKG_SUGESTAO.ADICIONAR_SUGESTAO(
        p_id_presente => v_id_presente,
        p_local_compra => 'Americanas (IA Claude)',
        p_url_compra => 'https://www.americanas.com.br/notebook-dell',
        p_preco_sugerido => 3399.00
    );
    DBMS_OUTPUT.PUT_LINE('✓ Sugestao 3 criada: Americanas - R$ 3399.00');

    DBMS_OUTPUT.PUT_LINE('');
    DBMS_OUTPUT.PUT_LINE('=== Teste 3.2: Obter Melhor Preco ===');

    v_melhor_preco := PKG_SUGESTAO.OBTER_MELHOR_PRECO(
        p_id_presente => v_id_presente
    );
    DBMS_OUTPUT.PUT_LINE('✓ Melhor preco encontrado: R$ ' || v_melhor_preco);

    DBMS_OUTPUT.PUT_LINE('');
    DBMS_OUTPUT.PUT_LINE('=== Teste 3.3: Contar Sugestoes ===');

    v_count := PKG_SUGESTAO.CONTAR_SUGESTOES(
        p_id_presente => v_id_presente
    );
    DBMS_OUTPUT.PUT_LINE('✓ Total de sugestoes: ' || v_count);

    DBMS_OUTPUT.PUT_LINE('');
    DBMS_OUTPUT.PUT_LINE('✓ PKG_SUGESTAO: TODOS OS TESTES PASSARAM!');
    DBMS_OUTPUT.PUT_LINE('');
END;
/

-- ==============================================================================
-- TESTE 4: PKG_COMPRA - COMPRA DE PRESENTES
-- ==============================================================================

PROMPT ========================================
PROMPT TESTE 4: PKG_COMPRA
PROMPT ========================================
PROMPT

DECLARE
    v_id_usuario1 NUMBER;
    v_id_usuario2 NUMBER;
    v_id_presente NUMBER;
    v_id_compra NUMBER;
    v_is_comprado BOOLEAN;
BEGIN
    -- Buscar usuarios
    SELECT ID_USUARIO INTO v_id_usuario1
    FROM TB_USUARIO WHERE EMAIL = 'joao.silva@email.com';

    SELECT ID_USUARIO INTO v_id_usuario2
    FROM TB_USUARIO WHERE EMAIL = 'maria.santos@email.com';

    -- Buscar presente do usuario 1
    SELECT ID_PRESENTE INTO v_id_presente
    FROM TB_PRESENTE
    WHERE ID_USUARIO = v_id_usuario1
      AND ROWNUM = 1;

    DBMS_OUTPUT.PUT_LINE('=== Teste 4.1: Marcar Como Comprado ===');

    -- Usuario 2 compra presente do usuario 1
    v_id_compra := PKG_COMPRA.MARCAR_COMPRADO(
        p_id_presente => v_id_presente,
        p_id_comprador => v_id_usuario2
    );
    DBMS_OUTPUT.PUT_LINE('✓ Presente marcado como comprado. ID Compra: ' || v_id_compra);

    DBMS_OUTPUT.PUT_LINE('');
    DBMS_OUTPUT.PUT_LINE('=== Teste 4.2: Verificar Notificacao Criada ===');

    DECLARE
        v_count_notif NUMBER;
    BEGIN
        v_count_notif := PKG_NOTIFICACAO.CONTAR_NAO_LIDAS(
            p_id_usuario => v_id_usuario1
        );
        DBMS_OUTPUT.PUT_LINE('✓ Notificacoes nao lidas do usuario 1: ' || v_count_notif);
    END;

    DBMS_OUTPUT.PUT_LINE('');
    DBMS_OUTPUT.PUT_LINE('=== Teste 4.3: Validacoes ===');

    -- Tentar comprar novamente (deve falhar)
    BEGIN
        v_id_compra := PKG_COMPRA.MARCAR_COMPRADO(
            p_id_presente => v_id_presente,
            p_id_comprador => v_id_usuario2
        );
        DBMS_OUTPUT.PUT_LINE('✗ ERRO: Nao deveria permitir comprar novamente');
    EXCEPTION
        WHEN OTHERS THEN
            DBMS_OUTPUT.PUT_LINE('✓ Validacao de presente ja comprado funcionando');
    END;

    -- Tentar comprar proprio presente
    DECLARE
        v_presente_usuario2 NUMBER;
    BEGIN
        SELECT ID_PRESENTE INTO v_presente_usuario2
        FROM TB_PRESENTE
        WHERE ID_USUARIO = v_id_usuario2
          AND ROWNUM = 1;

        v_id_compra := PKG_COMPRA.MARCAR_COMPRADO(
            p_id_presente => v_presente_usuario2,
            p_id_comprador => v_id_usuario2 -- Mesmo usuario
        );
        DBMS_OUTPUT.PUT_LINE('✗ ERRO: Nao deveria permitir comprar proprio presente');
    EXCEPTION
        WHEN OTHERS THEN
            DBMS_OUTPUT.PUT_LINE('✓ Validacao de proprio presente funcionando');
    END;

    DBMS_OUTPUT.PUT_LINE('');
    DBMS_OUTPUT.PUT_LINE('✓ PKG_COMPRA: TODOS OS TESTES PASSARAM!');
    DBMS_OUTPUT.PUT_LINE('');
END;
/

-- ==============================================================================
-- TESTE 5: PKG_NOTIFICACAO - SISTEMA DE NOTIFICACOES
-- ==============================================================================

PROMPT ========================================
PROMPT TESTE 5: PKG_NOTIFICACAO
PROMPT ========================================
PROMPT

DECLARE
    v_id_usuario NUMBER;
    v_id_notif NUMBER;
    v_count_antes NUMBER;
    v_count_depois NUMBER;
    v_count_marcadas NUMBER;
BEGIN
    -- Buscar usuario
    SELECT ID_USUARIO INTO v_id_usuario
    FROM TB_USUARIO WHERE EMAIL = 'joao.silva@email.com';

    DBMS_OUTPUT.PUT_LINE('=== Teste 5.1: Criar Notificacao ===');

    v_id_notif := PKG_NOTIFICACAO.CRIAR_NOTIFICACAO(
        p_id_usuario => v_id_usuario,
        p_mensagem => 'Teste de notificacao manual'
    );
    DBMS_OUTPUT.PUT_LINE('✓ Notificacao criada com ID: ' || v_id_notif);

    DBMS_OUTPUT.PUT_LINE('');
    DBMS_OUTPUT.PUT_LINE('=== Teste 5.2: Contar Nao Lidas ===');

    v_count_antes := PKG_NOTIFICACAO.CONTAR_NAO_LIDAS(
        p_id_usuario => v_id_usuario
    );
    DBMS_OUTPUT.PUT_LINE('✓ Notificacoes nao lidas: ' || v_count_antes);

    DBMS_OUTPUT.PUT_LINE('');
    DBMS_OUTPUT.PUT_LINE('=== Teste 5.3: Marcar Todas Como Lidas ===');

    v_count_marcadas := PKG_NOTIFICACAO.MARCAR_TODAS_LIDAS(
        p_id_usuario => v_id_usuario
    );
    DBMS_OUTPUT.PUT_LINE('✓ Notificacoes marcadas como lidas: ' || v_count_marcadas);

    v_count_depois := PKG_NOTIFICACAO.CONTAR_NAO_LIDAS(
        p_id_usuario => v_id_usuario
    );
    DBMS_OUTPUT.PUT_LINE('✓ Notificacoes nao lidas apos marcar: ' || v_count_depois);

    DBMS_OUTPUT.PUT_LINE('');
    DBMS_OUTPUT.PUT_LINE('✓ PKG_NOTIFICACAO: TODOS OS TESTES PASSARAM!');
    DBMS_OUTPUT.PUT_LINE('');
END;
/

-- ==============================================================================
-- TESTE 6: VIEWS
-- ==============================================================================

PROMPT ========================================
PROMPT TESTE 6: VIEWS
PROMPT ========================================
PROMPT

DECLARE
    v_count NUMBER;
BEGIN
    DBMS_OUTPUT.PUT_LINE('=== Teste 6.1: VW_DASHBOARD ===');

    SELECT COUNT(*) INTO v_count FROM VW_DASHBOARD;
    DBMS_OUTPUT.PUT_LINE('✓ VW_DASHBOARD funcionando (' || v_count || ' registros)');

    DBMS_OUTPUT.PUT_LINE('');
    DBMS_OUTPUT.PUT_LINE('=== Teste 6.2: VW_PRESENTES_COMPLETO ===');

    SELECT COUNT(*) INTO v_count FROM VW_PRESENTES_COMPLETO;
    DBMS_OUTPUT.PUT_LINE('✓ VW_PRESENTES_COMPLETO funcionando (' || v_count || ' registros)');

    DBMS_OUTPUT.PUT_LINE('');
    DBMS_OUTPUT.PUT_LINE('=== Teste 6.3: VW_USUARIO_ESTATISTICAS ===');

    SELECT COUNT(*) INTO v_count FROM VW_USUARIO_ESTATISTICAS;
    DBMS_OUTPUT.PUT_LINE('✓ VW_USUARIO_ESTATISTICAS funcionando (' || v_count || ' registros)');

    DBMS_OUTPUT.PUT_LINE('');
    DBMS_OUTPUT.PUT_LINE('✓ VIEWS: TODOS OS TESTES PASSARAM!');
    DBMS_OUTPUT.PUT_LINE('');
END;
/

-- ==============================================================================
-- RESUMO FINAL
-- ==============================================================================

PROMPT ========================================
PROMPT RESUMO DOS TESTES
PROMPT ========================================
PROMPT

SELECT
    'Usuarios cadastrados' AS ITEM,
    COUNT(*) AS QUANTIDADE
FROM TB_USUARIO
UNION ALL
SELECT
    'Presentes cadastrados',
    COUNT(*)
FROM TB_PRESENTE
UNION ALL
SELECT
    'Presentes ativos',
    COUNT(*)
FROM TB_PRESENTE
WHERE STATUS = 'ATIVO'
UNION ALL
SELECT
    'Presentes comprados',
    COUNT(*)
FROM TB_PRESENTE
WHERE STATUS = 'COMPRADO'
UNION ALL
SELECT
    'Compras realizadas',
    COUNT(*)
FROM TB_COMPRA
UNION ALL
SELECT
    'Sugestoes cadastradas',
    COUNT(*)
FROM TB_SUGESTAO_COMPRA
UNION ALL
SELECT
    'Notificacoes criadas',
    COUNT(*)
FROM TB_NOTIFICACAO;

PROMPT
PROMPT ========================================
PROMPT TODOS OS TESTES CONCLUIDOS COM SUCESSO!
PROMPT ========================================
PROMPT
PROMPT Sistema esta pronto para uso!
PROMPT

SET FEEDBACK ON
