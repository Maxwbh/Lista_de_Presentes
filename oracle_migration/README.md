# Migração Lista de Presentes - Oracle 26 / Apex 24

## 👨‍💻 Desenvolvedor

**Nome:** Maxwell da Silva Oliveira
**Email:** maxwbh@gmail.com
**LinkedIn:** [linkedin.com/in/maxwbh](https://www.linkedin.com/in/maxwbh/)
**GitHub:** [@maxwbh](https://github.com/Maxwbh/)
**Empresa:** M&S do Brasil LTDA
**Site:** [msbrasil.inf.br](http://msbrasil.inf.br)

---

## 📋 Visão Geral

Este documento descreve a migração completa do sistema de Lista de Presentes de Python/Django para Oracle Database 26 com Oracle APEX 24. Toda a lógica de negócio foi implementada no banco de dados através de Packages, Procedures e Functions.

## 🗂️ Estrutura dos Arquivos

```
oracle_migration/
├── 01_DDL_TABELAS.sql          # Criação de todas as tabelas, índices e views
├── 02_PKG_USUARIO.sql          # Package de gerenciamento de usuários
├── 03_PKG_PRESENTE.sql         # Package de gerenciamento de presentes
├── 04_PKG_COMPRA.sql           # Package de gerenciamento de compras
├── 05_PKG_NOTIFICACAO.sql      # Package de gerenciamento de notificações
├── 06_PKG_SUGESTAO.sql         # Package de gerenciamento de sugestões
└── README.md                   # Esta documentação
```

## 🎯 Ordem de Execução

Execute os scripts na seguinte ordem:

1. **01_DDL_TABELAS.sql** - Cria toda a estrutura de dados
2. **02_PKG_USUARIO.sql** - Cria package de usuários (usado por outros packages)
3. **05_PKG_NOTIFICACAO.sql** - Cria package de notificações (usado por PKG_COMPRA)
4. **03_PKG_PRESENTE.sql** - Cria package de presentes
5. **06_PKG_SUGESTAO.sql** - Cria package de sugestões
6. **04_PKG_COMPRA.sql** - Cria package de compras (depende de notificações)

```sql
-- Conectar como usuário com privilégios adequados
@01_DDL_TABELAS.sql
@02_PKG_USUARIO.sql
@05_PKG_NOTIFICACAO.sql
@03_PKG_PRESENTE.sql
@06_PKG_SUGESTAO.sql
@04_PKG_COMPRA.sql
```

## 📊 Estrutura do Banco de Dados

### Tabelas Principais

#### TB_USUARIO
Armazena os usuários do sistema (herda funcionalidade do Django AbstractUser)
- **Chave Primária:** ID_USUARIO
- **Unique Keys:** EMAIL, USERNAME
- **Campos Principais:** EMAIL, SENHA_HASH, PRIMEIRO_NOME, ULTIMO_NOME, ATIVO, IS_SUPERUSER
- **Sequences:** SEQ_USUARIO

#### TB_PRESENTE
Armazena os presentes cadastrados
- **Chave Primária:** ID_PRESENTE
- **Foreign Keys:** ID_USUARIO → TB_USUARIO
- **Campos Principais:** DESCRICAO, URL, PRECO, STATUS (ATIVO/COMPRADO)
- **Campos de Imagem:** IMAGEM_BASE64 (CLOB), IMAGEM_NOME, IMAGEM_TIPO
- **Sequences:** SEQ_PRESENTE

#### TB_COMPRA
Registra as compras de presentes (relacionamento 1:1 com TB_PRESENTE)
- **Chave Primária:** ID_COMPRA
- **Foreign Keys:** ID_PRESENTE → TB_PRESENTE, ID_COMPRADOR → TB_USUARIO
- **Unique Key:** ID_PRESENTE (um presente só pode ser comprado uma vez)
- **Sequences:** SEQ_COMPRA

#### TB_SUGESTAO_COMPRA
Armazena sugestões de onde comprar (integração com Zoom, Buscapé, IA)
- **Chave Primária:** ID_SUGESTAO
- **Foreign Keys:** ID_PRESENTE → TB_PRESENTE
- **Campos Principais:** LOCAL_COMPRA, URL_COMPRA, PRECO_SUGERIDO
- **Sequences:** SEQ_SUGESTAO_COMPRA

#### TB_NOTIFICACAO
Sistema de notificações para usuários
- **Chave Primária:** ID_NOTIFICACAO
- **Foreign Keys:** ID_USUARIO → TB_USUARIO
- **Campos Principais:** MENSAGEM, LIDA (S/N), DATA_NOTIFICACAO
- **Sequences:** SEQ_NOTIFICACAO

#### TB_LOG_AUDITORIA
Tabela para auditoria de operações (opcional)
- **Chave Primária:** ID_LOG
- **Campos Principais:** TABELA, OPERACAO, USUARIO_BD, DADOS_ANTES, DADOS_DEPOIS
- **Sequences:** SEQ_LOG_AUDITORIA

### Views

#### VW_PRESENTES_COMPLETO
View consolidada com todas informações de presentes, usuários, compras e estatísticas

#### VW_DASHBOARD
View com estatísticas gerais do sistema

#### VW_USUARIO_ESTATISTICAS
View com estatísticas por usuário

## 📦 Packages PL/SQL

### PKG_USUARIO
Gerenciamento completo de usuários

**Principais Functions:**
- `REGISTRAR_USUARIO` - Cadastro de novo usuário com validações
- `AUTENTICAR_USUARIO` - Autenticação com email/senha
- `VALIDAR_SENHA` - Valida senha do usuário
- `BUSCAR_POR_ID` - Busca usuário por ID
- `BUSCAR_POR_EMAIL` - Busca usuário por email
- `IS_SUPERUSER` - Verifica se é administrador
- `LISTAR_USUARIOS_ATIVOS` - Lista todos usuários ativos
- `LISTAR_OUTROS_USUARIOS` - Lista usuários exceto o especificado

**Principais Procedures:**
- `ATUALIZAR_USUARIO` - Atualiza dados do usuário
- `ALTERAR_SENHA` - Troca senha com validação
- `ALTERAR_STATUS` - Ativa/Desativa usuário
- `REGISTRAR_LOGIN` - Registra data/hora de login
- `EXCLUIR_USUARIO` - Soft delete (marca como inativo)

**Segurança:**
- Hash de senha usando SHA-256 (DBMS_CRYPTO)
- Validação de email com REGEXP
- Controle de duplicidade de email/username

**Exemplo de Uso:**
```sql
-- Registrar novo usuário
DECLARE
    v_id_usuario NUMBER;
BEGIN
    v_id_usuario := PKG_USUARIO.REGISTRAR_USUARIO(
        p_username => 'joao.silva',
        p_email => 'joao.silva@email.com',
        p_senha => 'senha123',
        p_primeiro_nome => 'João',
        p_ultimo_nome => 'Silva',
        p_telefone => '11999999999'
    );
    DBMS_OUTPUT.PUT_LINE('Usuário criado: ' || v_id_usuario);
END;
/

-- Autenticar usuário
DECLARE
    v_id_usuario NUMBER;
BEGIN
    v_id_usuario := PKG_USUARIO.AUTENTICAR_USUARIO(
        p_email => 'joao.silva@email.com',
        p_senha => 'senha123'
    );
    DBMS_OUTPUT.PUT_LINE('Usuário autenticado: ' || v_id_usuario);
EXCEPTION
    WHEN OTHERS THEN
        DBMS_OUTPUT.PUT_LINE('Erro: ' || SQLERRM);
END;
/
```

### PKG_PRESENTE
Gerenciamento de presentes

**Principais Functions:**
- `ADICIONAR_PRESENTE` - Adiciona novo presente (com suporte a imagem base64)
- `BUSCAR_POR_ID` - Busca presente completo por ID
- `LISTAR_MEUS_PRESENTES` - Lista presentes do usuário
- `LISTAR_PRESENTES_OUTROS` - Lista presentes de outros usuários (com filtros)
- `LISTAR_PRESENTES_USUARIO` - Lista presentes de um usuário específico
- `OBTER_IMAGEM_BASE64` - Retorna imagem em base64
- `CONTAR_PRESENTES` - Conta presentes por status
- `IS_DONO_PRESENTE` - Verifica propriedade
- `OBTER_ESTATISTICAS` - Estatísticas do presente

**Principais Procedures:**
- `ATUALIZAR_PRESENTE` - Atualiza dados do presente (com validação de propriedade)
- `EXCLUIR_PRESENTE` - Exclui presente (CASCADE para sugestões e compras)

**Recursos:**
- Armazenamento de imagens em Base64 (CLOB)
- Validação de propriedade em todas operações
- Filtros por preço e status
- Integração com sugestões (contagem, melhor preço)

**Exemplo de Uso:**
```sql
-- Adicionar presente
DECLARE
    v_id_presente NUMBER;
BEGIN
    v_id_presente := PKG_PRESENTE.ADICIONAR_PRESENTE(
        p_id_usuario => 1,
        p_descricao => 'Notebook Dell Inspiron 15',
        p_url => 'https://www.dell.com.br/...',
        p_preco => 3500.00,
        p_imagem_base64 => NULL, -- Pode ser passado aqui
        p_imagem_nome => NULL,
        p_imagem_tipo => NULL
    );
    DBMS_OUTPUT.PUT_LINE('Presente criado: ' || v_id_presente);
END;
/

-- Listar meus presentes
DECLARE
    v_cursor PKG_PRESENTE.t_cursor;
    v_id NUMBER;
    v_desc CLOB;
    v_preco NUMBER;
BEGIN
    v_cursor := PKG_PRESENTE.LISTAR_MEUS_PRESENTES(
        p_id_usuario => 1,
        p_status => 'ATIVO'
    );

    LOOP
        FETCH v_cursor INTO v_id, v_desc, v_preco; -- etc
        EXIT WHEN v_cursor%NOTFOUND;
        DBMS_OUTPUT.PUT_LINE(v_id || ' - ' || v_desc);
    END LOOP;
    CLOSE v_cursor;
END;
/
```

### PKG_COMPRA
Gerenciamento de compras de presentes

**Principais Functions:**
- `MARCAR_COMPRADO` - Marca presente como comprado (com validações)
- `LISTAR_MINHAS_COMPRAS` - Lista compras realizadas pelo usuário
- `LISTAR_PRESENTES_COMPRADOS` - Lista presentes comprados do usuário
- `BUSCAR_COMPRA_POR_PRESENTE` - Busca dados da compra
- `IS_COMPRADO` - Verifica se presente foi comprado
- `IS_COMPRADOR` - Verifica se usuário comprou o presente
- `CONTAR_MINHAS_COMPRAS` - Total de compras do usuário

**Principais Procedures:**
- `CANCELAR_COMPRA` - Cancela compra e volta presente para ATIVO

**Validações e Regras de Negócio:**
- ✅ Não pode comprar próprio presente
- ✅ Presente deve estar ATIVO
- ✅ Lock de linha (FOR UPDATE) para evitar race condition
- ✅ Relacionamento 1:1 (presente só pode ser comprado uma vez)
- ✅ Criação automática de notificação para dono do presente
- ✅ Cancelamento com notificação

**Exemplo de Uso:**
```sql
-- Marcar presente como comprado
DECLARE
    v_id_compra NUMBER;
BEGIN
    v_id_compra := PKG_COMPRA.MARCAR_COMPRADO(
        p_id_presente => 10,
        p_id_comprador => 2  -- Usuário diferente do dono
    );
    DBMS_OUTPUT.PUT_LINE('Compra registrada: ' || v_id_compra);
    -- Automaticamente cria notificação para dono do presente
EXCEPTION
    WHEN OTHERS THEN
        DBMS_OUTPUT.PUT_LINE('Erro: ' || SQLERRM);
END;
/

-- Cancelar compra
BEGIN
    PKG_COMPRA.CANCELAR_COMPRA(
        p_id_presente => 10,
        p_id_usuario => 2  -- Pode ser comprador ou dono
    );
    DBMS_OUTPUT.PUT_LINE('Compra cancelada com sucesso');
END;
/
```

### PKG_NOTIFICACAO
Sistema de notificações

**Principais Functions:**
- `CRIAR_NOTIFICACAO` - Cria nova notificação
- `MARCAR_TODAS_LIDAS` - Marca todas notificações como lidas
- `LISTAR_NOTIFICACOES` - Lista notificações (com filtros)
- `CONTAR_NAO_LIDAS` - Conta notificações não lidas
- `LIMPAR_NOTIFICACOES_LIDAS` - Exclui notificações lidas
- `BUSCAR_POR_ID` - Busca notificação específica

**Principais Procedures:**
- `MARCAR_LIDA` - Marca notificação individual como lida
- `EXCLUIR_NOTIFICACAO` - Exclui notificação

**Recursos:**
- Filtragem por lida/não lida
- Limite de registros
- Validação de propriedade
- Data de leitura automática

**Exemplo de Uso:**
```sql
-- Criar notificação
DECLARE
    v_id_notif NUMBER;
BEGIN
    v_id_notif := PKG_NOTIFICACAO.CRIAR_NOTIFICACAO(
        p_id_usuario => 1,
        p_mensagem => '🎁 Um dos seus presentes foi comprado!'
    );
END;
/

-- Contar não lidas
DECLARE
    v_count NUMBER;
BEGIN
    v_count := PKG_NOTIFICACAO.CONTAR_NAO_LIDAS(p_id_usuario => 1);
    DBMS_OUTPUT.PUT_LINE('Notificações não lidas: ' || v_count);
END;
/

-- Marcar todas como lidas
DECLARE
    v_count NUMBER;
BEGIN
    v_count := PKG_NOTIFICACAO.MARCAR_TODAS_LIDAS(p_id_usuario => 1);
    DBMS_OUTPUT.PUT_LINE('Marcadas como lidas: ' || v_count);
END;
/
```

### PKG_SUGESTAO
Gerenciamento de sugestões de compra

**Principais Functions:**
- `ADICIONAR_SUGESTAO` - Adiciona sugestão de loja/preço
- `LISTAR_SUGESTOES` - Lista sugestões (ordenado por preço/data/loja)
- `OBTER_MELHOR_PRECO` - Retorna menor preço encontrado
- `OBTER_MELHOR_SUGESTAO` - Retorna sugestão com melhor preço
- `CONTAR_SUGESTOES` - Conta sugestões do presente
- `LIMPAR_SUGESTOES` - Exclui todas sugestões do presente
- `BUSCAR_POR_ID` - Busca sugestão específica

**Principais Procedures:**
- `ATUALIZAR_SUGESTAO` - Atualiza dados da sugestão
- `EXCLUIR_SUGESTAO` - Exclui sugestão
- `ADICIONAR_SUGESTOES_LOTE` - Placeholder para integração com APIs
- `ATUALIZAR_DATA_BUSCA` - Atualiza data de busca

**Integração com APIs Externas:**
O package está preparado para integração com:
- Zoom
- Buscapé
- APIs de IA (Claude, ChatGPT, Gemini)

**Exemplo de Uso:**
```sql
-- Adicionar sugestão
DECLARE
    v_id_sugestao NUMBER;
BEGIN
    v_id_sugestao := PKG_SUGESTAO.ADICIONAR_SUGESTAO(
        p_id_presente => 10,
        p_local_compra => 'Amazon (Zoom)',
        p_url_compra => 'https://www.zoom.com.br/...',
        p_preco_sugerido => 3299.90
    );
END;
/

-- Obter melhor preço
DECLARE
    v_melhor_preco NUMBER;
BEGIN
    v_melhor_preco := PKG_SUGESTAO.OBTER_MELHOR_PRECO(p_id_presente => 10);
    DBMS_OUTPUT.PUT_LINE('Melhor preço: R$ ' || v_melhor_preco);
END;
/

-- Limpar sugestões antigas
DECLARE
    v_count NUMBER;
BEGIN
    v_count := PKG_SUGESTAO.LIMPAR_SUGESTOES(p_id_presente => 10);
    DBMS_OUTPUT.PUT_LINE('Sugestões removidas: ' || v_count);
END;
/
```

## 🔐 Segurança

### Hash de Senhas
- Utiliza **SHA-256** através do `DBMS_CRYPTO`
- Senhas nunca são armazenadas em texto plano
- Função: `PKG_USUARIO.HASH_SENHA` (privada)

```sql
-- Exemplo interno do hash
v_hash := DBMS_CRYPTO.HASH(
    src => UTL_I18N.STRING_TO_RAW(p_senha, 'AL32UTF8'),
    typ => DBMS_CRYPTO.HASH_SH256
);
```

### Validações
- Email: Validação com REGEXP
- Propriedade: Todas operações validam se usuário é dono
- Duplicidade: Email e Username únicos
- Status: Apenas usuários ativos podem operar

### Controle de Concorrência
- **SELECT FOR UPDATE** em operações críticas (marcar comprado)
- Transações ACID completas
- Rollback automático em caso de erro

## 📱 Integração com Oracle APEX 24

### Configuração de Autenticação

1. **Criar Esquema de Autenticação Customizado**
```sql
-- Em Authentication Schemes do APEX
-- Tipo: Custom
-- Function Returning Boolean:

FUNCTION apex_authentication(
    p_username IN VARCHAR2,
    p_password IN VARCHAR2
) RETURN BOOLEAN
IS
    v_id_usuario NUMBER;
BEGIN
    v_id_usuario := PKG_USUARIO.AUTENTICAR_USUARIO(
        p_email => p_username,
        p_senha => p_password
    );

    -- Armazenar ID na sessão
    APEX_UTIL.SET_SESSION_STATE('P_USER_ID', v_id_usuario);

    RETURN TRUE;
EXCEPTION
    WHEN OTHERS THEN
        RETURN FALSE;
END;
```

### Páginas Sugeridas

#### 1. **Login (Página 101)**
- Item: P101_EMAIL
- Item: P101_SENHA
- Validação customizada chamando `PKG_USUARIO.AUTENTICAR_USUARIO`

#### 2. **Dashboard (Página 1)**
```sql
-- Region Source: SQL Query
SELECT * FROM VW_DASHBOARD;
```

#### 3. **Meus Presentes (Página 10)**
```sql
-- Interactive Report Source
SELECT *
FROM TABLE(PKG_PRESENTE.LISTAR_MEUS_PRESENTES(
    p_id_usuario => :APP_USER_ID,
    p_status => :P10_FILTRO_STATUS
));
```

#### 4. **Adicionar Presente (Página 11)**
```sql
-- Page Process: Criar Presente
DECLARE
    v_id_presente NUMBER;
BEGIN
    v_id_presente := PKG_PRESENTE.ADICIONAR_PRESENTE(
        p_id_usuario => :APP_USER_ID,
        p_descricao => :P11_DESCRICAO,
        p_url => :P11_URL,
        p_preco => :P11_PRECO,
        p_imagem_base64 => :P11_IMAGEM_BASE64,
        p_imagem_nome => :P11_IMAGEM_NOME,
        p_imagem_tipo => :P11_IMAGEM_TIPO
    );

    -- Redirecionar para página de presentes
    APEX_UTIL.REDIRECT_URL('f?p=&APP_ID.:10:&SESSION.');
END;
```

#### 5. **Lista de Usuários (Página 20)**
```sql
-- Cards Region Source
SELECT *
FROM TABLE(PKG_USUARIO.LISTAR_OUTROS_USUARIOS(
    p_id_usuario_excluir => :APP_USER_ID
));
```

#### 6. **Presentes do Usuário (Página 21)**
```sql
-- Interactive Report Source
SELECT *
FROM TABLE(PKG_PRESENTE.LISTAR_PRESENTES_USUARIO(
    p_id_usuario_dono => :P21_ID_USUARIO,
    p_id_usuario_visualizador => :APP_USER_ID
));
```

#### 7. **Sugestões de Compra (Página 30)**
```sql
-- Interactive Report Source
SELECT *
FROM TABLE(PKG_SUGESTAO.LISTAR_SUGESTOES(
    p_id_presente => :P30_ID_PRESENTE,
    p_ordenar_por => :P30_ORDENAR
));
```

#### 8. **Notificações (Página 40)**
```sql
-- Interactive Report Source
SELECT *
FROM TABLE(PKG_NOTIFICACAO.LISTAR_NOTIFICACOES(
    p_id_usuario => :APP_USER_ID,
    p_apenas_nao_lidas => FALSE
));

-- Badge de Notificações (Header)
SELECT PKG_NOTIFICACAO.CONTAR_NAO_LIDAS(:APP_USER_ID)
FROM DUAL;
```

### Processos APEX Comuns

**Marcar Presente como Comprado**
```sql
-- Page Process
DECLARE
    v_id_compra NUMBER;
BEGIN
    v_id_compra := PKG_COMPRA.MARCAR_COMPRADO(
        p_id_presente => :P21_ID_PRESENTE,
        p_id_comprador => :APP_USER_ID
    );

    -- Mensagem de sucesso
    APEX_APPLICATION.G_PRINT_SUCCESS_MESSAGE := 'Presente marcado como comprado!';
EXCEPTION
    WHEN OTHERS THEN
        APEX_ERROR.ADD_ERROR(
            p_message => 'Erro: ' || SQLERRM,
            p_display_location => APEX_ERROR.C_INLINE_IN_NOTIFICATION
        );
END;
```

**Upload de Imagem**
```sql
-- Page Process: Converter e Salvar Imagem
DECLARE
    v_blob BLOB;
    v_base64 CLOB;
BEGIN
    -- Obter BLOB do item de upload
    SELECT blob_content INTO v_blob
    FROM apex_application_temp_files
    WHERE name = :P11_IMAGEM;

    -- Converter para Base64
    v_base64 := APEX_WEB_SERVICE.BLOB2CLOBBASE64(v_blob);

    -- Armazenar na session
    :P11_IMAGEM_BASE64 := v_base64;
    :P11_IMAGEM_TIPO := :P11_IMAGEM_MIME_TYPE;
END;
```

## 🔄 Fluxos de Trabalho

### Fluxo: Adicionar Presente
1. Usuário preenche formulário (descrição, URL, preço, imagem)
2. Sistema converte imagem para Base64 (se houver)
3. Chama `PKG_PRESENTE.ADICIONAR_PRESENTE`
4. Sistema pode chamar automaticamente `PKG_SUGESTAO.ADICIONAR_SUGESTOES_LOTE` para buscar preços

### Fluxo: Comprar Presente
1. Usuário visualiza presente de outro usuário
2. Clica em "Marcar como Comprado"
3. Sistema chama `PKG_COMPRA.MARCAR_COMPRADO`
4. Package valida:
   - Não é o próprio presente
   - Presente está ATIVO
   - Não foi comprado ainda (lock na linha)
5. Atualiza status do presente
6. Cria registro de compra
7. Cria notificação para dono do presente
8. Commit

### Fluxo: Buscar Sugestões
1. Sistema busca em APIs externas (Zoom, Buscapé, IA)
2. Para cada resultado, chama `PKG_SUGESTAO.ADICIONAR_SUGESTAO`
3. Sugestões ordenadas por preço
4. Usuário visualiza melhor preço com `PKG_SUGESTAO.OBTER_MELHOR_PRECO`

## 📈 Índices e Performance

### Índices Criados

**TB_USUARIO:**
- `IDX_USUARIO_EMAIL` - Busca por email (login)
- `IDX_USUARIO_ATIVO` - Filtro de usuários ativos
- `IDX_USUARIO_DATA_CADASTRO` - Ordenação por data

**TB_PRESENTE:**
- `IDX_PRESENTE_USUARIO` - Presentes por usuário
- `IDX_PRESENTE_STATUS` - Filtro por status
- `IDX_PRESENTE_DATA_CAD` - Ordenação por data
- `IDX_PRESENTE_USR_STATUS` - Composto (usuário + status)

**TB_COMPRA:**
- `IDX_COMPRA_PRESENTE` - Busca por presente
- `IDX_COMPRA_COMPRADOR` - Compras por usuário
- `IDX_COMPRA_DATA` - Ordenação por data

**TB_SUGESTAO_COMPRA:**
- `IDX_SUGESTAO_PRESENTE` - Sugestões por presente
- `IDX_SUGESTAO_PRECO` - Ordenação por preço
- `IDX_SUGESTAO_DATA` - Ordenação por data

**TB_NOTIFICACAO:**
- `IDX_NOTIF_USUARIO` - Notificações por usuário
- `IDX_NOTIF_LIDA` - Filtro por lida
- `IDX_NOTIF_DATA` - Ordenação por data
- `IDX_NOTIF_USR_LIDA` - Composto (usuário + lida + data)

### Otimizações

1. **SELECT FOR UPDATE** em operações críticas
2. **BULK COLLECT** para operações em lote (futuro)
3. **Views materializadas** para dashboard (opcional)
4. **Particionamento** de tabelas grandes (opcional)

## 🧪 Testes

### Teste 1: Criar Usuário e Autenticar
```sql
-- Criar usuário
DECLARE
    v_id NUMBER;
BEGIN
    v_id := PKG_USUARIO.REGISTRAR_USUARIO(
        p_username => 'teste.usuario',
        p_email => 'teste@email.com',
        p_senha => 'senha123',
        p_primeiro_nome => 'Teste',
        p_ultimo_nome => 'Usuario'
    );
    DBMS_OUTPUT.PUT_LINE('ID: ' || v_id);
END;
/

-- Autenticar
DECLARE
    v_id NUMBER;
BEGIN
    v_id := PKG_USUARIO.AUTENTICAR_USUARIO(
        p_email => 'teste@email.com',
        p_senha => 'senha123'
    );
    DBMS_OUTPUT.PUT_LINE('Autenticado: ' || v_id);
END;
/
```

### Teste 2: Fluxo Completo de Presente
```sql
-- 1. Adicionar presente
DECLARE
    v_id_presente NUMBER;
    v_id_sugestao NUMBER;
BEGIN
    -- Criar presente
    v_id_presente := PKG_PRESENTE.ADICIONAR_PRESENTE(
        p_id_usuario => 1,
        p_descricao => 'Smartphone Samsung Galaxy S23',
        p_preco => 2500.00
    );
    DBMS_OUTPUT.PUT_LINE('Presente criado: ' || v_id_presente);

    -- Adicionar sugestões
    v_id_sugestao := PKG_SUGESTAO.ADICIONAR_SUGESTAO(
        p_id_presente => v_id_presente,
        p_local_compra => 'Amazon',
        p_url_compra => 'https://amazon.com.br/...',
        p_preco_sugerido => 2399.00
    );

    v_id_sugestao := PKG_SUGESTAO.ADICIONAR_SUGESTAO(
        p_id_presente => v_id_presente,
        p_local_compra => 'Magazine Luiza',
        p_url_compra => 'https://magazineluiza.com.br/...',
        p_preco_sugerido => 2450.00
    );

    DBMS_OUTPUT.PUT_LINE('Sugestões adicionadas');

    -- Ver melhor preço
    DBMS_OUTPUT.PUT_LINE('Melhor preço: ' ||
        PKG_SUGESTAO.OBTER_MELHOR_PRECO(v_id_presente));
END;
/
```

### Teste 3: Fluxo de Compra
```sql
-- Marcar como comprado (usuário 2 comprando presente do usuário 1)
DECLARE
    v_id_compra NUMBER;
BEGIN
    v_id_compra := PKG_COMPRA.MARCAR_COMPRADO(
        p_id_presente => 1,
        p_id_comprador => 2
    );
    DBMS_OUTPUT.PUT_LINE('Compra: ' || v_id_compra);

    -- Verificar notificação criada
    DBMS_OUTPUT.PUT_LINE('Notificações não lidas do usuário 1: ' ||
        PKG_NOTIFICACAO.CONTAR_NAO_LIDAS(1));
END;
/
```

## 🚀 Deploy em Produção

### Checklist de Deploy

- [ ] Backup completo do banco de dados
- [ ] Executar scripts na ordem correta
- [ ] Compilar todos os packages sem erros
- [ ] Executar testes de integração
- [ ] Validar índices criados
- [ ] Verificar privilégios dos usuários
- [ ] Documentar configurações do APEX
- [ ] Criar jobs de manutenção (limpeza de logs, etc)

### Permissões Necessárias

```sql
-- Para o schema da aplicação
GRANT EXECUTE ON DBMS_CRYPTO TO schema_app;
GRANT EXECUTE ON UTL_I18N TO schema_app;
GRANT CREATE SEQUENCE TO schema_app;
GRANT CREATE TABLE TO schema_app;
GRANT CREATE VIEW TO schema_app;
GRANT CREATE PROCEDURE TO schema_app;
```

### Backup e Restore

```sql
-- Export do schema
expdp username/password \
    schemas=LISTA_PRESENTES \
    directory=DATA_PUMP_DIR \
    dumpfile=lista_presentes_backup.dmp \
    logfile=lista_presentes_backup.log

-- Import do schema
impdp username/password \
    schemas=LISTA_PRESENTES \
    directory=DATA_PUMP_DIR \
    dumpfile=lista_presentes_backup.dmp \
    logfile=lista_presentes_restore.log
```

## 📝 Manutenção

### Rotinas Recomendadas

**Diária:**
- Verificar logs de erro do APEX
- Monitorar notificações não lidas antigas (> 30 dias)

**Semanal:**
- Analisar índices e estatísticas
- Verificar espaço em disco (CLOBs de imagem)

**Mensal:**
- Limpar logs de auditoria antigos
- Arquivar presentes muito antigos

### Scripts de Manutenção

```sql
-- Limpar notificações lidas antigas (> 90 dias)
DELETE FROM TB_NOTIFICACAO
WHERE LIDA = 'S'
  AND DATA_LEITURA < SYSDATE - 90;
COMMIT;

-- Limpar logs de auditoria antigos (> 180 dias)
DELETE FROM TB_LOG_AUDITORIA
WHERE DATA_OPERACAO < SYSDATE - 180;
COMMIT;

-- Atualizar estatísticas
BEGIN
    DBMS_STATS.GATHER_SCHEMA_STATS(
        ownname => USER,
        cascade => TRUE
    );
END;
/
```

## 🔗 Diferenças do Sistema Python

### Migração de Conceitos

| Python/Django | Oracle/APEX |
|---------------|-------------|
| `User.objects.create_user()` | `PKG_USUARIO.REGISTRAR_USUARIO()` |
| `authenticate(email, password)` | `PKG_USUARIO.AUTENTICAR_USUARIO()` |
| `Presente.objects.filter()` | `PKG_PRESENTE.LISTAR_MEUS_PRESENTES()` |
| `presente.save()` | `PKG_PRESENTE.ADICIONAR_PRESENTE()` |
| `@login_required` | Validação via `PKG_USUARIO.IS_SUPERUSER()` |
| `ImageField` | `IMAGEM_BASE64 CLOB` |
| `status='ATIVO'` | `STATUS VARCHAR2(20)` |
| Django Admin | Oracle APEX Admin Pages |

### Funcionalidades Mantidas

✅ Registro e autenticação de usuários
✅ CRUD completo de presentes
✅ Sistema de compras com validações
✅ Notificações automáticas
✅ Sugestões de compra
✅ Upload de imagens (Base64)
✅ Estatísticas e dashboard
✅ Filtros por preço e status

### Funcionalidades Adicionadas

➕ Views consolidadas para performance
➕ Auditoria de operações (TB_LOG_AUDITORIA)
➕ Lock de concorrência em compras
➕ Separação clara em packages (modularização)
➕ Documentação inline (comentários SQL)

## 📞 Suporte

Para dúvidas sobre implementação:
- Revisar comentários nos scripts SQL
- Consultar exemplos de uso neste README
- Verificar mensagens de erro das exceptions customizadas

## 📄 Licença

Este projeto segue a mesma licença do sistema original em Python.
