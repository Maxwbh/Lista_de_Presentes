import os
from pathlib import Path
import dj_database_url
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-CHANGE-THIS-IN-PRODUCTION')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

CSRF_TRUSTED_ORIGINS = [
    'https://lista-presentes-0hbp.onrender.com',
    'https://*.onrender.com',
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',  # Required by allauth
    'presentes',
    'rest_framework',
    'pwa',
    'corsheaders',
    # Django-allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    # Social providers
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.facebook',
    'allauth.socialaccount.providers.linkedin_oauth2',
    'allauth.socialaccount.providers.apple',
]

# Required by django-allauth
SITE_ID = 1

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Servir arquivos estáticos em produção
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',  # Django-allauth middleware
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'lista_presentes.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'presentes.context_processors.grupos_usuario',
                'presentes.context_processors.app_version',
            ],
        },
    },
]

WSGI_APPLICATION = 'lista_presentes.wsgi.application'

# ==============================================================================
# Banco de Dados - Configuração com Schema Isolado
# ==============================================================================
# Suporta múltiplas opções de banco de dados:
#
# 1. PRODUÇÃO - Supabase PostgreSQL com Schema Isolado (Configuração Atual):
#    DATABASE_URL=postgresql://postgres.PROJECT:PASS@aws-1-us-east-2.pooler.supabase.com:6543/postgres
#    Schema: lista_presentes (isolado para evitar conflitos com outras apps Django)
#
# 2. DESENVOLVIMENTO - SQLite:
#    Sem DATABASE_URL ou com USE_SQLITE=True
#
# IMPORTANTE: Usa search_path=lista_presentes exclusivamente
# ==============================================================================

DATABASE_URL = os.getenv('DATABASE_URL')
USE_SQLITE = os.getenv('USE_SQLITE', 'False') == 'True'

# Supabase - Variáveis adicionais (opcionais, para uso futuro com Supabase SDK)
SUPABASE_URL = os.getenv('SUPABASE_URL', '')
SUPABASE_KEY = os.getenv('SUPABASE_KEY', '')

if DATABASE_URL and not USE_SQLITE:
    # Produção: PostgreSQL via DATABASE_URL (Render, Supabase, Heroku, etc.)
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,  # Pool de conexões: mantém conexões por 10 minutos
            conn_health_checks=True,  # Verifica saúde da conexão antes de usar
        )
    }

    # Usar schema separado para esta aplicação (compartilhamento de banco Supabase)
    # IMPORTANTE: Usar APENAS lista_presentes (sem public) para evitar
    # conflito com django_migrations de outras aplicações Django

    # Preservar OPTIONS existentes do dj_database_url e adicionar search_path
    if 'OPTIONS' not in DATABASES['default']:
        DATABASES['default']['OPTIONS'] = {}

    DATABASES['default']['OPTIONS']['options'] = '-c search_path=lista_presentes'

    # Signal para garantir search_path em cada conexão
    from django.db.backends.signals import connection_created
    def set_search_path(sender, connection, **kwargs):
        if connection.vendor == 'postgresql':
            cursor = connection.cursor()
            cursor.execute("SET search_path TO lista_presentes")
    connection_created.connect(set_search_path)
else:
    # Desenvolvimento: SQLite
    # Use para ambientes com recursos mínimos (512MB-1GB RAM)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'data' / 'db.sqlite3' if USE_SQLITE else BASE_DIR / 'db.sqlite3',
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Autenticação
AUTH_USER_MODEL = 'presentes.Usuario'
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/login/'

# Internacionalização
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# Arquivos estáticos
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Diretórios de arquivos estáticos adicionais
STATICFILES_DIRS = [
    BASE_DIR / 'static',
] if (BASE_DIR / 'static').exists() else []

# WhiteNoise para servir arquivos estáticos em produção
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Arquivos de mídia (uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# IMPORTANTE: Criar diretório media se não existir
import os
os.makedirs(MEDIA_ROOT, exist_ok=True)

# WhiteNoise também pode servir arquivos de mídia (não é ideal, mas funciona para free tier)
# Nota: Em produção real, use S3, Cloudinary ou similar
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = True if DEBUG else False

# PWA Settings
PWA_APP_NAME = 'Lista de Presentes'
PWA_APP_DESCRIPTION = "Sistema de Lista de Presentes"
PWA_APP_THEME_COLOR = '#0A4C95'
PWA_APP_BACKGROUND_COLOR = '#ffffff'
PWA_APP_DISPLAY = 'standalone'
PWA_APP_SCOPE = '/'
PWA_APP_ORIENTATION = 'any'
PWA_APP_START_URL = '/dashboard/'
PWA_APP_ICONS = [
    {
        'src': '/static/icons/icon-72x72.svg',
        'sizes': '72x72',
        'type': 'image/svg+xml'
    },
    {
        'src': '/static/icons/icon-96x96.svg',
        'sizes': '96x96',
        'type': 'image/svg+xml'
    },
    {
        'src': '/static/icons/icon-128x128.svg',
        'sizes': '128x128',
        'type': 'image/svg+xml'
    },
    {
        'src': '/static/icons/icon-144x144.svg',
        'sizes': '144x144',
        'type': 'image/svg+xml'
    },
    {
        'src': '/static/icons/icon-152x152.svg',
        'sizes': '152x152',
        'type': 'image/svg+xml'
    },
    {
        'src': '/static/icons/icon-192x192.svg',
        'sizes': '192x192',
        'type': 'image/svg+xml'
    },
    {
        'src': '/static/icons/icon-384x384.svg',
        'sizes': '384x384',
        'type': 'image/svg+xml'
    },
    {
        'src': '/static/icons/icon-512x512.svg',
        'sizes': '512x512',
        'type': 'image/svg+xml'
    }
]

# APIs de IA
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', 'sua-chave-anthropic')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', 'sua-chave-openai')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'sua-chave-gemini')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Logging em produção
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}

# Configurações de segurança para produção
if not DEBUG:
    # Render.com fornece proxy SSL, não redirecionar no app
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = False  # Render.com já faz o redirect
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'

    # HSTS (HTTP Strict Transport Security)
    SECURE_HSTS_SECONDS = 31536000  # 1 ano
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# ==============================================================================
# GitHub Integration - Auto-create issues for failed image downloads
# ==============================================================================
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')  # Token de acesso pessoal do GitHub
GITHUB_REPO_OWNER = os.getenv('GITHUB_REPO_OWNER', 'Maxwbh')  # Dono do repositório
GITHUB_REPO_NAME = os.getenv('GITHUB_REPO_NAME', 'Lista_de_Presentes')  # Nome do repositório
GITHUB_AUTO_CREATE_ISSUES = os.getenv('GITHUB_AUTO_CREATE_ISSUES', 'True') == 'True'  # Habilitar/desabilitar

# URL base da API do GitHub
GITHUB_API_BASE_URL = 'https://api.github.com'

# Site URL para links em issues
SITE_URL = os.getenv('SITE_URL', 'http://localhost:8000')

# ==============================================================================
# Django-allauth Configuration - Social Authentication
# ==============================================================================

# Authentication backends
AUTHENTICATION_BACKENDS = [
    # Django default backend
    'django.contrib.auth.backends.ModelBackend',
    # Allauth backend
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Allauth settings
ACCOUNT_AUTHENTICATION_METHOD = 'email'  # Use email instead of username
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_EMAIL_VERIFICATION = 'optional'  # Can be 'mandatory', 'optional', or 'none'
ACCOUNT_SIGNUP_EMAIL_ENTER_TWICE = False
ACCOUNT_SESSION_REMEMBER = True
ACCOUNT_LOGOUT_ON_GET = False

# Social account settings
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_VERIFICATION = 'optional'
SOCIALACCOUNT_QUERY_EMAIL = True
SOCIALACCOUNT_STORE_TOKENS = True

# Provider specific settings
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'APP': {
            'client_id': os.getenv('GOOGLE_CLIENT_ID', ''),
            'secret': os.getenv('GOOGLE_CLIENT_SECRET', ''),
            'key': ''
        }
    },
    'facebook': {
        'METHOD': 'oauth2',
        'SCOPE': ['email', 'public_profile'],
        'AUTH_PARAMS': {'auth_type': 'reauthenticate'},
        'FIELDS': [
            'id',
            'email',
            'name',
            'first_name',
            'last_name',
            'verified',
        ],
        'EXCHANGE_TOKEN': True,
        'VERIFIED_EMAIL': False,
        'VERSION': 'v18.0',
        'APP': {
            'client_id': os.getenv('FACEBOOK_APP_ID', ''),
            'secret': os.getenv('FACEBOOK_APP_SECRET', ''),
            'key': ''
        }
    },
    'linkedin_oauth2': {
        'SCOPE': [
            'r_basicprofile',
            'r_emailaddress'
        ],
        'PROFILE_FIELDS': [
            'id',
            'first-name',
            'last-name',
            'email-address',
        ],
        'APP': {
            'client_id': os.getenv('LINKEDIN_CLIENT_ID', ''),
            'secret': os.getenv('LINKEDIN_CLIENT_SECRET', ''),
            'key': ''
        }
    },
    'apple': {
        'APP': {
            'client_id': os.getenv('APPLE_CLIENT_ID', ''),
            'secret': os.getenv('APPLE_CLIENT_SECRET', ''),
            'key': os.getenv('APPLE_KEY_ID', ''),
            'certificate_key': os.getenv('APPLE_PRIVATE_KEY', ''),
        },
        'SCOPE': ['name', 'email'],
    }
}

# Login/Logout redirect URLs
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'
ACCOUNT_LOGOUT_REDIRECT_URL = '/'
