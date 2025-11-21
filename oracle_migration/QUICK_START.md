# Guia Rápido de Início - Lista de Presentes Oracle

> **Desenvolvedor:** Maxwell da Silva Oliveira (@maxwbh) | **Empresa:** M&S do Brasil LTDA | **Site:** [msbrasil.inf.br](http://msbrasil.inf.br)

## 🚀 Instalação em 5 Minutos

### 1. Conectar ao Banco Oracle

```bash
sqlplus username/password@database
```

### 2. Executar Script de Instalação

```sql
@00_INSTALL_ALL.sql
```

Este script executará automaticamente todos os passos de instalação na ordem correta.

### 3. Criar Usuário Administrador

```sql
DECLARE
    v_id NUMBER;
BEGIN
    v_id := PKG_USUARIO.REGISTRAR_USUARIO(
        p_username => 'admin',
        p_email => 'admin@listapresentes.com',
        p_senha => 'Admin@123',
        p_primeiro_nome => 'Administrador',
        p_ultimo_nome => 'Sistema'
    );

    -- Tornar superusuário
    UPDATE TB_USUARIO
    SET IS_SUPERUSER = 'S', IS_STAFF = 'S'
    WHERE ID_USUARIO = v_id;

    COMMIT;

    DBMS_OUTPUT.PUT_LINE('Admin criado com ID: ' || v_id);
END;
/
```

### 4. Executar Testes (Opcional)

```sql
@99_TESTES_COMPLETOS.sql
```

### 5. Pronto! 🎉

O sistema está instalado e pronto para uso.

---

## 📱 Configuração do Oracle APEX

### Criar Nova Aplicação

1. Acesse o Oracle APEX Workspace
2. Crie nova aplicação: **Lista de Presentes**
3. Configure autenticação customizada:

```sql
-- Authentication Function
FUNCTION apex_authenticate(
    p_username IN VARCHAR2,
    p_password IN VARCHAR2
) RETURN BOOLEAN
IS
    v_id NUMBER;
BEGIN
    v_id := PKG_USUARIO.AUTENTICAR_USUARIO(
        p_email => p_username,
        p_senha => p_password
    );
    APEX_UTIL.SET_SESSION_STATE('APP_USER_ID', v_id);
    RETURN TRUE;
EXCEPTION
    WHEN OTHERS THEN
        RETURN FALSE;
END;
```

### Páginas Recomendadas

**1. Login (Página 101)**
- 2 campos: Email e Senha
- Botão: Entrar
- Link: Criar Conta → Página 102

**2. Dashboard (Página 1)**
```sql
-- Fonte da Região
SELECT * FROM VW_DASHBOARD;
```

**3. Meus Presentes (Página 10)**
```sql
-- Interactive Report
DECLARE
    v_cursor PKG_PRESENTE.t_cursor;
BEGIN
    v_cursor := PKG_PRESENTE.LISTAR_MEUS_PRESENTES(
        p_id_usuario => :APP_USER_ID,
        p_status => :P10_FILTRO_STATUS
    );
    RETURN v_cursor;
END;
```

---

## 🔧 Comandos Úteis

### Gerenciar Usuários

```sql
-- Criar usuário
DECLARE
    v_id NUMBER;
BEGIN
    v_id := PKG_USUARIO.REGISTRAR_USUARIO(
        p_username => 'joao.silva',
        p_email => 'joao@email.com',
        p_senha => 'Senha@123',
        p_primeiro_nome => 'João',
        p_ultimo_nome => 'Silva'
    );
END;
/

-- Autenticar
DECLARE
    v_id NUMBER;
BEGIN
    v_id := PKG_USUARIO.AUTENTICAR_USUARIO(
        p_email => 'joao@email.com',
        p_senha => 'Senha@123'
    );
    DBMS_OUTPUT.PUT_LINE('ID: ' || v_id);
END;
/

-- Listar usuários ativos
DECLARE
    v_cursor PKG_USUARIO.t_cursor;
BEGIN
    v_cursor := PKG_USUARIO.LISTAR_USUARIOS_ATIVOS;
    -- Processar cursor
END;
/
```

### Gerenciar Presentes

```sql
-- Adicionar presente
DECLARE
    v_id NUMBER;
BEGIN
    v_id := PKG_PRESENTE.ADICIONAR_PRESENTE(
        p_id_usuario => 1,
        p_descricao => 'Notebook Dell Inspiron 15',
        p_url => 'https://www.dell.com.br/...',
        p_preco => 3500.00
    );
    DBMS_OUTPUT.PUT_LINE('Presente ID: ' || v_id);
END;
/

-- Listar meus presentes
SELECT * FROM TABLE(
    PKG_PRESENTE.LISTAR_MEUS_PRESENTES(
        p_id_usuario => 1,
        p_status => 'ATIVO'
    )
);

-- Contar presentes
SELECT PKG_PRESENTE.CONTAR_PRESENTES(
    p_id_usuario => 1,
    p_status => 'ATIVO'
) AS TOTAL
FROM DUAL;
```

### Gerenciar Compras

```sql
-- Marcar como comprado
DECLARE
    v_id_compra NUMBER;
BEGIN
    v_id_compra := PKG_COMPRA.MARCAR_COMPRADO(
        p_id_presente => 10,
        p_id_comprador => 2
    );
    -- Cria notificação automaticamente
END;
/

-- Listar minhas compras
SELECT * FROM TABLE(
    PKG_COMPRA.LISTAR_MINHAS_COMPRAS(
        p_id_comprador => 2
    )
);
```

### Gerenciar Sugestões

```sql
-- Adicionar sugestão
DECLARE
    v_id NUMBER;
BEGIN
    v_id := PKG_SUGESTAO.ADICIONAR_SUGESTAO(
        p_id_presente => 10,
        p_local_compra => 'Amazon',
        p_url_compra => 'https://amazon.com.br/...',
        p_preco_sugerido => 3299.90
    );
END;
/

-- Obter melhor preço
SELECT PKG_SUGESTAO.OBTER_MELHOR_PRECO(10) AS MELHOR_PRECO
FROM DUAL;

-- Listar sugestões
SELECT * FROM TABLE(
    PKG_SUGESTAO.LISTAR_SUGESTOES(
        p_id_presente => 10,
        p_ordenar_por => 'PRECO'
    )
);
```

### Gerenciar Notificações

```sql
-- Criar notificação
DECLARE
    v_id NUMBER;
BEGIN
    v_id := PKG_NOTIFICACAO.CRIAR_NOTIFICACAO(
        p_id_usuario => 1,
        p_mensagem => '🎁 Você tem uma nova notificação!'
    );
END;
/

-- Contar não lidas
SELECT PKG_NOTIFICACAO.CONTAR_NAO_LIDAS(1) AS NAO_LIDAS
FROM DUAL;

-- Marcar todas como lidas
DECLARE
    v_count NUMBER;
BEGIN
    v_count := PKG_NOTIFICACAO.MARCAR_TODAS_LIDAS(1);
    DBMS_OUTPUT.PUT_LINE('Marcadas: ' || v_count);
END;
/
```

---

## 📊 Consultas Úteis

### Dashboard Completo

```sql
SELECT * FROM VW_DASHBOARD;
```

### Estatísticas por Usuário

```sql
SELECT * FROM VW_USUARIO_ESTATISTICAS
ORDER BY TOTAL_PRESENTES DESC;
```

### Presentes com Melhor Preço

```sql
SELECT
    p.DESCRICAO,
    p.PRECO AS PRECO_ESTIMADO,
    PKG_SUGESTAO.OBTER_MELHOR_PRECO(p.ID_PRESENTE) AS MELHOR_PRECO,
    PKG_SUGESTAO.CONTAR_SUGESTOES(p.ID_PRESENTE) AS TOTAL_SUGESTOES
FROM TB_PRESENTE p
WHERE p.STATUS = 'ATIVO'
ORDER BY MELHOR_PRECO;
```

### Presentes Mais Desejados

```sql
SELECT
    u.PRIMEIRO_NOME || ' ' || u.ULTIMO_NOME AS USUARIO,
    p.DESCRICAO,
    p.PRECO,
    PKG_SUGESTAO.CONTAR_SUGESTOES(p.ID_PRESENTE) AS SUGESTOES
FROM TB_PRESENTE p
INNER JOIN TB_USUARIO u ON p.ID_USUARIO = u.ID_USUARIO
WHERE p.STATUS = 'ATIVO'
ORDER BY SUGESTOES DESC
FETCH FIRST 10 ROWS ONLY;
```

---

## 🔍 Troubleshooting

### Erro: Package inválido

```sql
-- Recompilar package
ALTER PACKAGE PKG_USUARIO COMPILE;
ALTER PACKAGE PKG_USUARIO COMPILE BODY;

-- Ver erros
SELECT * FROM USER_ERRORS
WHERE NAME = 'PKG_USUARIO'
ORDER BY SEQUENCE;
```

### Erro: Senha inválida

As senhas são hasheadas com SHA-256. Certifique-se de:
- Usar a função `PKG_USUARIO.AUTENTICAR_USUARIO`
- Nunca comparar hash diretamente

### Erro: Presente já comprado

O sistema valida automaticamente o status do presente. Se ocorrer:
- Verifique se presente já está COMPRADO
- Use `PKG_COMPRA.IS_COMPRADO(id_presente)` para verificar antes
- Constraints do banco garantem integridade (UK_COMPRA_PRESENTE)

---

## 📚 Documentação Completa

Para documentação detalhada, consulte:
- `README.md` - Documentação completa
- Scripts SQL - Comentários inline

---

## 🆘 Suporte

Consulte os comentários nos arquivos SQL para detalhes sobre cada função/procedure.

---

## ✅ Checklist de Instalação

- [ ] Executar `00_INSTALL_ALL.sql`
- [ ] Verificar objetos inválidos (não deve haver nenhum)
- [ ] Criar usuário administrador
- [ ] Executar testes (`99_TESTES_COMPLETOS.sql`)
- [ ] Configurar Oracle APEX
- [ ] Testar login e funcionalidades básicas
- [ ] Fazer backup do schema

---

**Sistema pronto para produção!** 🚀
