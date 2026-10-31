# 🛠️ Instalação, configuração e operação

Guia técnico da **Lista de Presentes**: instalação local, Docker, deploy, testes, comandos de manutenção e solução de problemas. Para conhecer o projeto, veja o [README](../../README.md).

---

## 📋 Pré-requisitos

- Python 3.11 ou superior
- PostgreSQL 15 ou superior
- pip (gerenciador de pacotes Python)
- Git

---

## 🛠️ Instalação

### Método 1: Instalação via PIP (Recomendado)

Instale o pacote diretamente do GitHub:

```bash
# Instalação da versão mais recente
pip install git+https://github.com/Maxwbh/Lista_de_Presentes.git

# Instalação de uma versão específica
pip install git+https://github.com/Maxwbh/Lista_de_Presentes.git@v1.0.2

# Instalação com dependências de desenvolvimento
pip install git+https://github.com/Maxwbh/Lista_de_Presentes.git[dev]

# Instalação do repositório local
pip install -e /caminho/para/Lista_de_Presentes
```

Após a instalação via PIP, você ainda precisará configurar o banco de dados e executar as migrações conforme descrito nas seções abaixo.

### Método 2: Clone do Repositório

```bash
git clone https://github.com/Maxwbh/Lista_de_Presentes.git
cd Lista_de_Presentes
```

### 2. Crie um Ambiente Virtual

```bash
# Linux/Mac
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Instale as Dependências

```bash
pip install -r requirements.txt
```

### 4. Configure as Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto (use `.env.example` como base):

```bash
cp .env.example .env
```

Edite o arquivo `.env` com suas configurações:

```env
# Django
SECRET_KEY=sua-chave-secreta-aqui-muito-longa-e-aleatoria
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Banco de Dados
DATABASE_URL=postgresql://usuario:senha@localhost:5432/lista_presentes

# Opcional: Render.com (para deploy)
RENDER=False
```

#### Gerando uma SECRET_KEY

```python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 5. Configure o Banco de Dados

#### PostgreSQL Local

```bash
# Criar banco de dados
createdb lista_presentes

# Ou usando psql
psql -U postgres
CREATE DATABASE lista_presentes;
\q
```

#### SQLite (apenas desenvolvimento)

Se preferir usar SQLite para testes locais, edite `lista_presentes/settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

### 6. Execute as Migrações

```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Crie um Superusuário

```bash
python manage.py createsuperuser
```

### 8. (Opcional) Gere Dados de Teste

```bash
python manage.py populate_test_data --users 5 --gifts-per-user 5
```

Este comando criará:
- 5 usuários de teste
- 5 presentes para cada usuário
- Preços e descrições reais extraídos de URLs

**Credenciais dos usuários de teste:**
- **Senha**: `senha123` (para todos)

### 9. Colete Arquivos Estáticos

```bash
python manage.py collectstatic --no-input
```

### 10. Inicie o Servidor

```bash
python manage.py runserver
```

Acesse: [http://localhost:8000](http://localhost:8000)

---

## 🐳 Docker (Alternativa)

Se preferir usar Docker:

```bash
# Iniciar com auto-reload
docker compose up --watch

# Criar superusuário
docker compose exec web python manage.py createsuperuser

# Gerar dados de teste
docker compose exec web python manage.py populate_test_data
```

Ver documentação completa em [docs/deployment/DOCKER.md](../deployment/DOCKER.md).

---

## 📂 Estrutura do Projeto

```
Lista_de_Presentes/
├── lista_presentes/          # Configurações do Django
│   ├── settings.py           # Configurações principais
│   ├── urls.py               # URLs do projeto
│   └── wsgi.py               # WSGI para produção
├── presentes/                # App principal
│   ├── models.py             # Modelos (Usuario, Presente, Compra, etc)
│   ├── views.py              # Views e lógica de negócio
│   ├── forms.py              # Formulários Django
│   ├── urls.py               # URLs do app
│   ├── admin.py              # Interface administrativa
│   └── management/
│       └── commands/
│           └── populate_test_data.py  # Geração de dados de teste
├── templates/                # Templates HTML
│   ├── base.html             # Template base
│   └── presentes/            # Templates do app
│       ├── login.html
│       ├── registro.html
│       ├── lista_usuarios.html
│       ├── meus_presentes.html
│       └── ...
├── static/                   # Arquivos estáticos
│   ├── icons/                # Ícones PWA
│   ├── manifest.json         # PWA manifest
│   └── sw.js                 # Service Worker
├── media/                    # Upload de arquivos (gitignored)
├── requirements.txt          # Dependências Python
├── .env.example              # Exemplo de variáveis de ambiente
├── .gitignore                # Arquivos ignorados pelo Git
├── manage.py                 # CLI do Django
├── build.sh                  # Script de build para Render
└── README.md                 # Este arquivo
```

---

## ⚙️ Configuração

### Variáveis de Ambiente

| Variável | Descrição | Padrão | Obrigatório |
|----------|-----------|---------|-------------|
| `SECRET_KEY` | Chave secreta do Django | - | ✅ Sim |
| `DEBUG` | Modo debug | `False` | Não |
| `ALLOWED_HOSTS` | Hosts permitidos | `localhost` | Sim (produção) |
| `DATABASE_URL` | URL do banco PostgreSQL | SQLite | Recomendado |
| `RENDER` | Indica ambiente Render | `False` | Não |

### Configurações de Email (Opcional)

Para enviar emails de notificação:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=seu-email@gmail.com
EMAIL_HOST_PASSWORD=sua-senha-de-app
```

---

## 🚀 Deploy

### Render.com (Recomendado)

1. **Crie conta no [Render.com](https://render.com)**

2. **Conecte seu repositório GitHub**

3. **Crie um PostgreSQL Database**
   - Nome: `lista-presentes-db`
   - Copie a `DATABASE_URL`

4. **Crie um Web Service**
   - Build Command: `./build.sh`
   - Start Command: `gunicorn lista_presentes.wsgi:application`

5. **Configure Variáveis de Ambiente**
   ```
   SECRET_KEY=sua-chave-gerada
   DATABASE_URL=sua-url-do-postgres
   ALLOWED_HOSTS=seu-app.onrender.com
   RENDER=True
   ```

6. **Deploy Automático**
   - Cada push na branch `main` fará deploy automaticamente

Ver documentação completa em [RENDER.md](../deployment/RENDER.md).

### Heroku

```bash
heroku create nome-do-app
heroku addons:create heroku-postgresql:mini
heroku config:set SECRET_KEY=sua-chave
git push heroku main
heroku run python manage.py migrate
heroku run python manage.py createsuperuser
```

### VPS/Ubuntu Server

Siga os passos de instalação local acima com PostgreSQL, `DEBUG=False` e um servidor como gunicorn atrás de um proxy (nginx). A configuração usada em produção está em `Dockerfile` e `entrypoint.sh`.

---

## 🔥 Keep-Alive (Render Free Tier)

O plano gratuito do Render coloca o app em "sleep" após 15 minutos sem acesso e tem limite de 750 horas de instância por mês. O workflow `.github/workflows/keep-alive.yml` faz um ping a cada 14 minutos **só nas horas de uso** (definidas a partir do relatório de acessos), sem estourar o limite.

- Para revisar as horas: rode o workflow **Relatorio de Acessos** (`.github/workflows/relatorio-acessos.yml`), que mostra os acessos por hora e dia da semana.
- Execuções: [GitHub Actions](https://github.com/Maxwbh/Lista_de_Presentes/actions)
- Detalhes: [KEEP_ALIVE.md](../features/KEEP_ALIVE.md)

---

## 📱 PWA - Progressive Web App

O aplicativo pode ser instalado como um app nativo:

### Android
1. Abra no Chrome
2. Menu > "Instalar app"
3. Confirme a instalação

### iOS
1. Abra no Safari
2. Compartilhar > "Adicionar à Tela Inicial"
3. Confirme

### Desktop
1. Abra no Chrome/Edge
2. Ícone de instalação na barra de endereços
3. Clique em "Instalar"

---

## 🧪 Testes

### Executar Todos os Testes

```bash
python manage.py test
```

### Testes Específicos

```bash
# Testar apenas o app presentes
python manage.py test presentes

# Testar com cobertura
coverage run --source='.' manage.py test
coverage report
coverage html
```

### CI/CD - Testes Automatizados

O projeto possui workflows de GitHub Actions que executam automaticamente:

✅ **Testes em múltiplas versões do Python** (3.11, 3.12)
- Testes unitários completos
- Cobertura de código (coverage reports)
- Testes com PostgreSQL 15

✅ **Análise de Qualidade de Código**
- Formatação: black, isort
- Linting: flake8
- Complexidade: mccabe

✅ **Segurança**
- Scan de vulnerabilidades: safety
- Análise de código: bandit

✅ **Deploy Automático**
- Deploy no Render após merge no `master`
- Health checks automáticos

**Workflows**: [`.github/workflows/`](../../.github/workflows/)

---

## 🗄️ Comandos de Gerenciamento

### Criar Admin

```bash
python manage.py createsuperuser
```

### Gerar Dados de Teste

```bash
# 5 usuários, 5 presentes cada
python manage.py populate_test_data

# Customizado
python manage.py populate_test_data --users 10 --gifts-per-user 8
```

### Limpar Banco de Dados

```bash
python manage.py flush --no-input
```

### Backup do Banco

```bash
# PostgreSQL
pg_dump lista_presentes > backup.sql

# Restaurar
psql lista_presentes < backup.sql
```

---

## 🐛 Troubleshooting

### Erro: "SECRET_KEY not set"

```bash
# Gere uma nova SECRET_KEY
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Adicione ao .env
echo "SECRET_KEY=chave-gerada" >> .env
```

### Erro: "database does not exist"

```bash
# Crie o banco
createdb lista_presentes

# Ou no psql
psql -U postgres -c "CREATE DATABASE lista_presentes;"
```

### Erro 500 em Produção

Ver guia completo: [DEBUG_500_ERRORS.md](DEBUG_500_ERRORS.md)

### Problemas com Imagens

```bash
# Executar migração de imagens para base64
python manage.py migrate_images_to_base64
```

Ver: [MIGRACAO_IMAGENS_BASE64.md](../database/MIGRACAO_IMAGENS_BASE64.md)

### Mais Problemas

Ver: [RENDER.md](../deployment/RENDER.md)

---

## 📊 Admin Django

Acesse o painel administrativo em: `http://localhost:8000/admin`

**Funcionalidades:**
- Gerenciar usuários
- Gerenciar presentes
- Ver compras realizadas
- Gerenciar notificações
- Ver sugestões de preços

---

## 🔐 Segurança

### Boas Práticas Implementadas

- ✅ Senhas hasheadas com PBKDF2
- ✅ CSRF protection
- ✅ Validação de formulários
- ✅ SQL injection protection (Django ORM)
- ✅ XSS protection
- ✅ Secure cookies em produção
- ✅ HTTPS obrigatório em produção

### Recomendações

- 🔒 Sempre use HTTPS em produção
- 🔒 Mantenha `DEBUG=False` em produção
- 🔒 Use senhas fortes
- 🔒 Atualize dependências regularmente

```bash
# Verificar vulnerabilidades
pip-audit

# Atualizar dependências
pip install --upgrade -r requirements.txt
```

---

## 📈 Performance

### Otimizações Implementadas

- ✅ Índices no banco de dados
- ✅ `select_related` e `prefetch_related` para evitar N+1
- ✅ Paginação (20 itens por página)
- ✅ Compressão de arquivos estáticos
- ✅ Cache de Service Worker (PWA)
- ✅ Imagens em base64 (evita requisições extras)

### Melhorias Futuras

- [ ] Redis para cache
- [ ] CDN para arquivos estáticos
- [ ] Lazy loading de imagens
- [ ] Compressão de respostas HTTP

---
