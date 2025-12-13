# Setup do Sistema de Grupos

Este guia explica como configurar o grupo padrão **"Natal Família Cruz e Credos 2025"** e migrar dados existentes.

## 🚀 Setup Rápido (Recomendado)

Execute o script automatizado que faz tudo:

```bash
./setup_grupo_padrao.sh
```

Este script irá:
1. ✅ Criar migrations
2. ✅ Aplicar migrations ao banco de dados
3. ✅ Criar o grupo padrão
4. ✅ Adicionar todos os usuários ao grupo
5. ✅ Tornar administradores em mantenedores
6. ✅ Migrar todos os dados existentes para o grupo

---

## 📋 Setup Manual (Passo a Passo)

Se preferir executar manualmente:

### 1. Criar e Aplicar Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 2. Criar Grupo Padrão e Adicionar Usuários

```bash
python manage.py criar_grupo_padrao
```

**O que este comando faz:**
- ✅ Cria o grupo "Natal Família Cruz e Credos 2025"
- ✅ Adiciona TODOS os usuários existentes ao grupo
- ✅ Torna usuários `is_superuser=True` em **mantenedores** do grupo
- ✅ Define o grupo como **grupo ativo** para usuários que não têm um
- ✅ Exibe o código e link de convite

**Saída esperada:**
```
✓ Grupo "Natal Família Cruz e Credos 2025" criado com sucesso!
  Código de convite: abc123xyz...

📊 Encontrados 5 usuários
  ✓ admin@example.com adicionado como MANTENEDOR
  + user1@example.com adicionado como membro
  + user2@example.com adicionado como membro
  ...

✅ OPERAÇÃO CONCLUÍDA COM SUCESSO!

📋 Resumo:
  • Grupo: Natal Família Cruz e Credos 2025
  • Total de usuários: 5
  • Novos membros adicionados: 5
  • Mantenedores (admins): 1
```

### 3. Migrar Dados Existentes para o Grupo

```bash
python manage.py migrar_dados_para_grupo
```

**O que este comando faz:**
- ✅ Migra todos os **Presentes** sem grupo para o grupo padrão
- ✅ Migra todas as **Compras** sem grupo
- ✅ Migra todas as **Notificações** sem grupo
- ✅ Migra todas as **Sugestões de Compra** sem grupo

**Saída esperada:**
```
✓ Grupo encontrado: Natal Família Cruz e Credos 2025
✓ 15 presentes migrados para o grupo
✓ 3 compras migradas para o grupo
✓ 8 notificações migradas para o grupo
✓ 12 sugestões migradas para o grupo

✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!

📋 Resumo:
  • Presentes migrados: 15
  • Compras migradas: 3
  • Notificações migradas: 8
  • Sugestões migradas: 12
  • TOTAL: 38 registros
```

---

## 🔧 Opções Avançadas

### Criar Grupo com Nome Personalizado

Edite o comando `criar_grupo_padrao.py` e altere a linha:

```python
nome='Natal Família Cruz e Credos 2025',
```

### Migrar para Grupo Específico

```bash
python manage.py migrar_dados_para_grupo --grupo-nome "Meu Grupo Customizado"
```

---

## 📝 Comandos de Gerenciamento Disponíveis

| Comando | Descrição |
|---------|-----------|
| `criar_grupo_padrao` | Cria grupo padrão e adiciona todos os usuários |
| `migrar_dados_para_grupo` | Migra dados existentes para um grupo |
| `populate_test_data` | Gera dados de teste (já existia) |

---

## 🐳 Docker

Se estiver usando Docker:

```bash
docker compose exec web python manage.py criar_grupo_padrao
docker compose exec web python manage.py migrar_dados_para_grupo
```

Ou execute o script dentro do container:

```bash
docker compose exec web ./setup_grupo_padrao.sh
```

---

## ✅ Verificação

Após executar os comandos, verifique:

1. **Django Admin**: http://localhost:8000/admin/presentes/grupo/
   - Deve mostrar o grupo "Natal Família Cruz e Credos 2025"
   - Clique no grupo para ver todos os membros

2. **Django Admin - Membros**: http://localhost:8000/admin/presentes/grupomembro/
   - Deve mostrar todos os usuários como membros
   - Administradores devem ter `e_mantenedor = True`

3. **Interface de Grupos**: http://localhost:8000/grupos/
   - Usuários verão o grupo na lista
   - Grupo deve estar marcado como ativo

4. **Dashboard**: http://localhost:8000/dashboard/
   - Deve funcionar normalmente (sem erro de grupo ativo)
   - Estatísticas devem refletir dados do grupo

---

## 🔗 Link de Convite

Para adicionar novos usuários ao grupo, compartilhe o link de convite gerado:

```
http://localhost:8000/grupos/convite/{CODIGO_DO_CONVITE}/
```

O código é exibido ao executar `criar_grupo_padrao`.

---

## 🆘 Troubleshooting

### Erro: "Grupo já existia"

Se o comando `criar_grupo_padrao` for executado novamente, ele não duplicará o grupo. Apenas adicionará novos usuários que ainda não são membros.

### Erro: "No module named 'django'"

Ative o ambiente virtual antes:

```bash
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### Dados não aparecem após migração

Verifique se o grupo foi definido corretamente:

```bash
python manage.py shell
>>> from presentes.models import Presente, Grupo
>>> grupo = Grupo.objects.get(nome='Natal Família Cruz e Credos 2025')
>>> Presente.objects.filter(grupo=grupo).count()
```

---

**Desenvolvido por**: Maxwell da Silva Oliveira (@maxwbh)  
**Empresa**: M&S do Brasil LTDA  
**Email**: maxwbh@gmail.com
