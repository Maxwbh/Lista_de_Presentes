# Configuração de Login Social - Django Allauth

Este projeto suporta login via redes sociais usando django-allauth.

## Redes Sociais Suportadas

- **Google** - Login com conta Google
- **Facebook** - Login com Facebook
- **LinkedIn** - Login com perfil do LinkedIn
- **Apple** - Login com Apple ID (iCloud)

## Configuração Necessária

### 1. Executar Migrações

```bash
python manage.py migrate
```

### 2. Configurar Variáveis de Ambiente

No painel do Render.com (ou arquivo `.env` local), adicione:

#### Google OAuth
```
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
```

**Como obter:**
1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um projeto ou selecione um existente
3. Vá em "APIs & Services" > "Credentials"
4. Clique em "Create Credentials" > "OAuth 2.0 Client ID"
5. Configure as URLs de redirect:
   - Authorized redirect URIs: `https://lista-presentes-1iwb.onrender.com/accounts/google/login/callback/`

#### Facebook OAuth
```
FACEBOOK_APP_ID=your_facebook_app_id_here
FACEBOOK_APP_SECRET=your_facebook_app_secret_here
```

**Como obter:**
1. Acesse [Facebook Developers](https://developers.facebook.com/)
2. Crie um aplicativo ou selecione um existente
3. Vá em "Settings" > "Basic"
4. Copie o App ID e App Secret
5. Em "Facebook Login" > "Settings", adicione:
   - Valid OAuth Redirect URIs: `https://lista-presentes-1iwb.onrender.com/accounts/facebook/login/callback/`

#### LinkedIn OAuth
```
LINKEDIN_CLIENT_ID=your_linkedin_client_id_here
LINKEDIN_CLIENT_SECRET=your_linkedin_client_secret_here
```

**Como obter:**
1. Acesse [LinkedIn Developers](https://www.linkedin.com/developers/apps)
2. Crie um aplicativo
3. Copie o Client ID e Client Secret
4. Em "Auth", adicione:
   - Redirect URLs: `https://lista-presentes-1iwb.onrender.com/accounts/linkedin_oauth2/login/callback/`

#### Apple Sign In
```
APPLE_CLIENT_ID=your_apple_service_id
APPLE_CLIENT_SECRET=your_apple_client_secret
APPLE_KEY_ID=your_apple_key_id
APPLE_PRIVATE_KEY=your_apple_private_key_content
```

**Como obter:**
1. Acesse [Apple Developer](https://developer.apple.com/account/)
2. Vá em "Certificates, Identifiers & Profiles"
3. Crie um Services ID
4. Configure Sign in with Apple
5. Gere uma chave privada e baixe o arquivo `.p8`

### 3. Configurar Site no Django Admin

1. Acesse o admin: `/admin/`
2. Vá em "Sites"
3. Edite o site existente (ID=1) para:
   - Domain name: `lista-presentes-1iwb.onrender.com`
   - Display name: `Lista de Presentes`

### 4. Testar Login Social

1. Acesse a página de login: `/login/`
2. Clique em um dos botões de rede social
3. Autorize o aplicativo
4. Você será redirecionado de volta autenticado

## URLs de Callback (Para Configurar nas Plataformas)

- **Google**: `https://lista-presentes-1iwb.onrender.com/accounts/google/login/callback/`
- **Facebook**: `https://lista-presentes-1iwb.onrender.com/accounts/facebook/login/callback/`
- **LinkedIn**: `https://lista-presentes-1iwb.onrender.com/accounts/linkedin_oauth2/login/callback/`
- **Apple**: `https://lista-presentes-1iwb.onrender.com/accounts/apple/login/callback/`

## Desenvolvimento Local

Para testar localmente, use URLs de callback com `http://localhost:8000`:

```
http://localhost:8000/accounts/google/login/callback/
http://localhost:8000/accounts/facebook/login/callback/
http://localhost:8000/accounts/linkedin_oauth2/login/callback/
http://localhost:8000/accounts/apple/login/callback/
```

## Troubleshooting

### Erro: "Site matching query does not exist"
- Execute: `python manage.py migrate`
- Configure o Site no admin conforme passo 3

### Erro: "invalid_client" ou "invalid_redirect_uri"
- Verifique se as URLs de callback estão corretas nas plataformas
- Certifique-se de que o domínio no Site (admin) está correto

### Erro: "Social account not found"
- O email do usuário pode já existir com login tradicional
- Faça login tradicional primeiro e depois conecte a conta social

## Documentação Django-allauth

Para mais informações: https://django-allauth.readthedocs.io/
