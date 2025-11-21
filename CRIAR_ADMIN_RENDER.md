# 👤 Como Criar Superusuário Admin no Render.com

## Credenciais do Admin

- **Username**: maxwbh
- **Email**: maxwbh@gmail.com
- **Senha**: a

---

## 🚀 Método 1: Script Automático (RECOMENDADO)

### Passo 1: Acessar Shell no Render.com

1. Vá para: https://dashboard.render.com
2. Clique no serviço: `lista-presentes`
3. Clique na aba: **"Shell"**
4. Aguarde o terminal carregar (pode demorar ~10 segundos)

### Passo 2: Executar Script

Copie e cole este comando no shell:

```bash
python create_admin.py
```

### Saída Esperada:

```
📝 Criando superusuário...
✅ Superusuário criado com sucesso!

👤 Username: maxwbh
📧 Email: maxwbh@gmail.com
🔑 Senha: a
👑 Superuser: True
👔 Staff: True

🌐 Acesse: https://lista-presentes-0hbp.onrender.com/admin/

✅ Concluído!
```

### Se o usuário já existir:

```
⚠️  Usuário com email maxwbh@gmail.com já existe!
✅ Usuário: maxwbh
✅ Email: maxwbh@gmail.com
✅ Superuser: True
✅ Staff: True
🔄 Senha atualizada!
```

---

## 🛠️ Método 2: Comando Django Interativo

### Passo 1: Acessar Shell no Render.com

(Mesmo do Método 1)

### Passo 2: Executar Comando

```bash
python manage.py createsuperuser
```

### Passo 3: Preencher Dados

```
E-mail: maxwbh@gmail.com
Username: maxwbh
Password: a
Password (again): a
```

### Aviso sobre senha curta:

```
This password is too short. It must contain at least 8 characters.
This password is too common.
Bypass password validation and create user anyway? [y/N]: y
```

**Digite**: `y` e pressione Enter

### Saída:

```
Superuser created successfully.
```

---

## 🐍 Método 3: Shell Python Direto

### Passo 1: Abrir Shell Django

No shell do Render, execute:

```bash
python manage.py shell
```

### Passo 2: Copiar e Colar Este Código

```python
from presentes.models import Usuario

# Criar superusuário
user = Usuario.objects.create_superuser(
    email='maxwbh@gmail.com',
    username='maxwbh',
    password='a',
    first_name='Max',
    last_name='WBH'
)

print(f"✅ Superusuário criado: {user.username}")
print(f"📧 Email: {user.email}")
print(f"👑 Superuser: {user.is_superuser}")
```

### Passo 3: Sair do Shell

```python
exit()
```

---

## ✅ Verificar Criação

### Teste 1: Login no Admin

1. Acesse: https://lista-presentes-0hbp.onrender.com/admin/
2. **Email**: maxwbh@gmail.com
3. **Senha**: a
4. Clique em **"Log in"**

Se funcionar, você verá a página de administração do Django!

### Teste 2: Login na Aplicação

1. Acesse: https://lista-presentes-0hbp.onrender.com/login/
2. **Email**: maxwbh@gmail.com
3. **Senha**: a
4. Clique em **"Entrar"**

Deve redirecionar para o dashboard!

---

## 🔧 Troubleshooting

### Erro: `OperationalError: FATAL: database not found`

**Causa**: Banco de dados não está conectado

**Solução**:
1. Dashboard → Seu serviço → **"Environment"**
2. Verificar `DATABASE_URL` está conectado ao banco
3. Verificar se o banco PostgreSQL está "Available" (verde)

---

### Erro: `ModuleNotFoundError: No module named 'presentes'`

**Causa**: DJANGO_SETTINGS_MODULE incorreto

**Solução**:
1. Dashboard → **"Environment"**
2. Verificar `DJANGO_SETTINGS_MODULE` = `lista_presentes.settings`
3. Fazer redeploy se necessário

---

### Erro: `IntegrityError: duplicate key value`

**Causa**: Usuário com esse email já existe

**Solução**:

**Opção A**: Usar script automático (Método 1) - ele atualiza a senha
**Opção B**: Deletar usuário existente e criar novo:

```python
python manage.py shell

# No shell Python:
from presentes.models import Usuario
Usuario.objects.filter(email='maxwbh@gmail.com').delete()
exit()

# Depois criar novamente
python create_admin.py
```

---

### Erro: `This password is too short`

**Causa**: Senha "a" é muito curta (mínimo 8 caracteres por padrão)

**Solução**:

**Opção A**: Aceitar bypass (digite `y`)

**Opção B**: Usar senha mais forte:

```python
# Editar create_admin.py localmente
PASSWORD = 'admin123'  # ou qualquer senha mais forte

# Ou no comando interativo, usar senha forte
```

---

## 📊 Verificar no Banco de Dados

Se quiser confirmar que o usuário foi criado:

```bash
python manage.py shell

# No shell Python:
from presentes.models import Usuario

# Listar todos os superusers
superusers = Usuario.objects.filter(is_superuser=True)
for user in superusers:
    print(f"👤 {user.username} - {user.email}")

# Verificar usuário específico
user = Usuario.objects.get(email='maxwbh@gmail.com')
print(f"Username: {user.username}")
print(f"Email: {user.email}")
print(f"Superuser: {user.is_superuser}")
print(f"Staff: {user.is_staff}")
print(f"Ativo: {user.ativo}")

exit()
```

---

## 🔐 Alterar Senha Depois

Se quiser alterar a senha depois:

```bash
python manage.py shell

# No shell Python:
from presentes.models import Usuario

user = Usuario.objects.get(email='maxwbh@gmail.com')
user.set_password('nova_senha_aqui')
user.save()

print("✅ Senha alterada!")
exit()
```

---

## 🎯 Resumo Rápido

**Comando mais rápido**:
```bash
python create_admin.py
```

**Acessar aplicação**:
- Admin: https://lista-presentes-0hbp.onrender.com/admin/
- Login: https://lista-presentes-0hbp.onrender.com/login/

**Credenciais**:
- Email: maxwbh@gmail.com
- Senha: a

---

## ⚠️ Segurança em Produção

**IMPORTANTE**: A senha "a" é muito fraca para produção!

Após testar, **altere para uma senha forte**:

```bash
python manage.py shell

from presentes.models import Usuario
user = Usuario.objects.get(email='maxwbh@gmail.com')
user.set_password('SenhaForteAqui123!')
user.save()
exit()
```

Ou crie nova variável de ambiente no Render:
```
DJANGO_ADMIN_PASSWORD = SenhaForte123!
```

E atualize o script para usar `os.getenv('DJANGO_ADMIN_PASSWORD', 'a')`.

---

**Última atualização**: Script create_admin.py criado
