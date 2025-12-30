# 🛠️ Guia de Instalação

Este guia cobre todas as formas de instalar o Lista de Presentes de Natal.

## 📋 Métodos de Instalação

### 1. Instalação Local (Desenvolvimento)
Recomendado para desenvolvimento e testes locais.

**Requisitos:**
- Python 3.11+
- PostgreSQL 15+ ou SQLite
- pip

**Passos:**
```bash
# Clone o repositório
git clone https://github.com/Maxwbh/Lista_de_Presentes.git
cd Lista_de_Presentes

# Crie ambiente virtual
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou venv\Scripts\activate (Windows)

# Instale dependências
pip install -r requirements.txt

# Configure variáveis de ambiente
cp .env.example .env
# Edite o .env com suas configurações

# Execute migrações
python manage.py migrate

# Crie superusuário
python manage.py createsuperuser

# Rode o servidor
python manage.py runserver
```

Ver [Setup Local Completo](local-setup.md) para mais detalhes.

### 2. Instalação via PIP
Instale o pacote diretamente do repositório:

```bash
# Instalar do GitHub (branch main)
pip install git+https://github.com/Maxwbh/Lista_de_Presentes.git

# Instalar versão específica
pip install git+https://github.com/Maxwbh/Lista_de_Presentes.git@v1.0.2

# Instalar do repositório local
pip install -e /caminho/para/Lista_de_Presentes

# Com dependências de desenvolvimento
pip install git+https://github.com/Maxwbh/Lista_de_Presentes.git[dev]
```

**Uso após instalação:**
```python
# Em seu projeto Django
INSTALLED_APPS = [
    ...
    'presentes',
    'lista_presentes',
]
```

### 3. Instalação com Docker
Recomendado para ambientes isolados:

```bash
# Build da imagem
docker-compose build

# Iniciar serviços
docker-compose up -d

# Executar migrações
docker-compose exec web python manage.py migrate

# Criar superusuário
docker-compose exec web python manage.py createsuperuser
```

Ver [Guia Docker Completo](../deployment/docker.md)

### 4. Deploy em Produção

#### Render.com (Recomendado)
```bash
# 1. Crie conta no Render.com
# 2. Conecte seu repositório GitHub
# 3. Crie um PostgreSQL Database
# 4. Crie um Web Service com:
#    - Build Command: ./build.sh
#    - Start Command: gunicorn lista_presentes.wsgi:application
# 5. Configure variáveis de ambiente
```

Ver [Guia Render Completo](../deployment/render.md)

#### Heroku
```bash
heroku create nome-do-app
heroku addons:create heroku-postgresql:mini
heroku config:set SECRET_KEY=sua-chave
git push heroku main
heroku run python manage.py migrate
```

Ver [Guia Heroku Completo](../deployment/heroku.md)

## 📦 Dependências

### Produção
- Django 5.0
- PostgreSQL (psycopg2-binary)
- Gunicorn
- WhiteNoise
- Django REST Framework
- Django CORS Headers
- django-pwa
- Pillow
- BeautifulSoup4
- Anthropic AI SDK
- OpenAI SDK

### Desenvolvimento
- pytest
- pytest-django
- black
- flake8
- isort
- mypy

Ver [requirements.txt](../../requirements.txt) completo.

## 🔧 Configuração Inicial

### Variáveis de Ambiente

Crie um arquivo `.env`:

```env
# Django
SECRET_KEY=sua-chave-secreta-muito-longa
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Banco de Dados
DATABASE_URL=postgresql://usuario:senha@localhost:5432/lista_presentes

# APIs (Opcional)
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...

# Email (Opcional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=seu-email@gmail.com
EMAIL_HOST_PASSWORD=sua-senha-app
```

Ver [Guia de Configuração Completo](configuration.md)

### Gerar SECRET_KEY

```python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Banco de Dados

#### PostgreSQL (Recomendado)
```bash
# Criar banco
createdb lista_presentes

# Ou via psql
psql -U postgres
CREATE DATABASE lista_presentes;
CREATE USER lista_user WITH PASSWORD 'senha123';
GRANT ALL PRIVILEGES ON DATABASE lista_presentes TO lista_user;
\q
```

#### SQLite (Apenas Desenvolvimento)
```python
# Em settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

## 🧪 Verificar Instalação

```bash
# Verificar versão Python
python --version  # Deve ser 3.11+

# Verificar instalação Django
python manage.py --version  # Deve ser 5.0

# Executar testes
python manage.py test

# Verificar servidor
python manage.py runserver
# Acesse http://localhost:8000
```

## 📊 Dados de Teste

```bash
# Criar 5 usuários com 5 presentes cada
python manage.py populate_test_data

# Customizado
python manage.py populate_test_data --users 10 --gifts-per-user 8

# Senha dos usuários de teste: senha123
```

## 🐛 Problemas Comuns

### Erro: "SECRET_KEY not set"
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
# Adicione a saída ao .env
```

### Erro: "database does not exist"
```bash
createdb lista_presentes
```

### Erro: "Port 8000 already in use"
```bash
# Use outra porta
python manage.py runserver 8080
```

Ver [Troubleshooting Completo](../troubleshooting.md)

## 📚 Próximos Passos

- [Quick Start](quickstart.md) - Tutorial rápido
- [Configuração Avançada](configuration.md)
- [Guia do Usuário](../user-guide/introduction.md)
- [Deploy em Produção](../deployment/production.md)

## 📞 Ajuda

- **Issues**: [GitHub Issues](https://github.com/Maxwbh/Lista_de_Presentes/issues)
- **Email**: maxwbh@gmail.com

---

**Versão**: 1.0.2
**Autor**: Maxwell da Silva Oliveira - M&S do Brasil LTDA
