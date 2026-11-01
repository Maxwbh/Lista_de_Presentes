# 👥 Grupos: Primeiros Passos e Funcionalidades

Os presentes, compras, notificações e sugestões pertencem a um **grupo**. Cada usuário pode participar de vários grupos e trabalha sempre no seu **grupo ativo**.

---

## 🧭 Funcionalidades

Todas as telas abaixo exigem login.

| URL | O que faz | Quem pode |
|-----|-----------|-----------|
| `/grupos/` | Lista os grupos ativos do usuário e permite trocar o grupo ativo (sem grupos, redireciona para criar um) | Membro |
| `/grupos/criar/` | Cria um grupo; o criador vira mantenedor e o grupo vira o ativo | Qualquer usuário |
| `/grupos/editar/<id>/` | Edita o grupo | Mantenedor |
| `/grupos/ativar/<id>/` | Define o grupo ativo (aceita `?next=` para voltar à página atual) | Membro |
| `/grupos/<id>/membros/` | Gerencia membros e mostra o link de convite | Mantenedor |
| `/grupos/<id>/membros/adicionar/` | Adiciona por e-mail um usuário já cadastrado (ele recebe uma notificação) | Mantenedor |
| `/grupos/<id>/membros/remover/<user_id>/` | Remove um membro (não remove a si mesmo) | Mantenedor |
| `/grupos/<id>/membros/toggle-mantenedor/<user_id>/` | Promove ou rebaixa mantenedor | Mantenedor |
| `/grupos/<id>/toggle-ativo/` | Ativa ou desativa o grupo | Mantenedor |
| `/grupos/<id>/sair/` | Sai do grupo (o último mantenedor precisa promover outro antes) | Membro |
| `/grupos/entrar/` | Entra informando o código de convite (aceita também o link completo) | Qualquer usuário |
| `/grupos/convite/<codigo>/` | Aceita o convite: entra no grupo e o define como ativo | Qualquer usuário |

O seletor de grupo ativo também fica no menu superior (context processor `presentes/context_processors.py`).

### 🔗 Convite

- O link de convite exibido na tela de membros é montado com o domínio da requisição atual.
- Quem abre o link sem conta é levado ao login e pode se cadastrar; o `?next=` é preservado, e ao concluir o cadastro a pessoa volta ao convite e entra no grupo.
- Grupos desativados não aceitam convite nem podem ser ativados.

---

## 🚀 Primeiro grupo e convites

1. **Cadastre-se** em `/registro/` (ou entre pelo login social) e faça login.
2. Sem nenhum grupo, o sistema leva a **`/grupos/criar/`**. Informe o nome (e, se quiser, a descrição e a URL de uma imagem) e salve: você vira **mantenedor** e o grupo passa a ser o ativo.
3. Em **`/grupos/<id>/membros/`** copie o **link de convite** (ou o código) e envie para as pessoas.
4. Quem recebe o link:
   - já com conta: abre o link e entra no grupo;
   - sem conta: abre o link, cadastra-se e volta automaticamente ao convite;
   - ou informa o código em `/grupos/` (formulário "entrar com código", que chama `/grupos/entrar/`).
5. Quem já tem conta também pode ser adicionado pelo e-mail na tela de membros.
6. Promova outros membros a mantenedor se quiser dividir a administração.

---

## 🔧 Dados antigos sem grupo (legado)

Bancos criados antes da existência de grupos podem ter presentes, compras, notificações e sugestões sem grupo. Para esses casos existem dois comandos:

```bash
python manage.py criar_grupo_padrao
python manage.py migrar_dados_para_grupo [--grupo-nome "Nome do Grupo"]
```

- **`criar_grupo_padrao`** cria um grupo com nome fixo definido no próprio comando (pode ser repetido sem duplicar), adiciona todos os usuários (superusuários como **mantenedores**), define o grupo como ativo para quem não tem um e mostra o código e o link de convite (o link usa `SITE_URL`).
- **`migrar_dados_para_grupo`** vincula ao grupo os **Presentes**, **Compras**, **Notificações** e **Sugestões de Compra** sem grupo. Sem `--grupo-nome`, usa o grupo criado por `criar_grupo_padrao`.

Com Docker: `docker compose exec web python manage.py <comando>`.

### Interface web: `/setup/`

Para plataformas sem shell (ex.: Render Free), a rota `/setup/` (`setup_grupos_view`) mostra o status (usuários, grupos, presentes, presentes sem grupo e se o grupo padrão existe) e tem botões para:

- **Setup completo**: `makemigrations`, `migrate`, `criar_grupo_padrao` e `migrar_dados_para_grupo`;
- cada etapa separada: **Migrations**, **Criar Grupo** e **Migrar Dados**.

O resultado aparece em mensagens no topo da página.

> 🔒 **Acesso:** somente **superusuários** (sem login, vai para a tela de login; outros usuários recebem 403). A rota `/gerar-dados-teste/`, que cria usuários de teste com senha conhecida, tem a mesma restrição.

---

## ✅ Verificação

- **Admin:** `/admin/presentes/grupo/` e `/admin/presentes/grupomembro/` (mantenedores com `e_mantenedor = True`).
- **App:** `/grupos/` mostra o grupo como ativo e `/dashboard/` abre sem pedir grupo.
- **Shell:**

```python
from presentes.models import Presente
Presente.objects.filter(grupo__isnull=True).count()  # deve ser 0 depois de migrar_dados_para_grupo
```
