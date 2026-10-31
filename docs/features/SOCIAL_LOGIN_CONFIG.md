# 🔐 Login Social (django-allauth)

O login por redes sociais usa **django-allauth 65.4.1**. Provedores habilitados em `INSTALLED_APPS` (`lista_presentes/settings.py`):

| Provedor | ID no allauth | Variáveis de ambiente |
|----------|---------------|-----------------------|
| Google | `google` | `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` |
| Facebook | `facebook` | `FACEBOOK_APP_ID`, `FACEBOOK_APP_SECRET` |
| LinkedIn | `linkedin_oauth2` | `LINKEDIN_CLIENT_ID`, `LINKEDIN_CLIENT_SECRET` |
| Apple | `apple` | `APPLE_CLIENT_ID`, `APPLE_CLIENT_SECRET`, `APPLE_KEY_ID`, `APPLE_PRIVATE_KEY` |

As credenciais ficam em `SOCIALACCOUNT_PROVIDERS` (lidas do ambiente). **Não é preciso cadastrar "Social applications" no admin.**

---

## ⚙️ Como funciona

- **Botões só para provedores configurados:** o context processor (`presentes/context_processors.py`) valida o formato das credenciais (`presentes/social_validation.py`). Provedor vazio, com placeholder ou com formato errado não aparece na tela de login. Se nenhum for válido, a seção "Ou entre com" fica oculta.
- **Sem página intermediária:** `SOCIALACCOUNT_LOGIN_ON_GET = True` leva direto ao provedor.
- **Cadastro automático:** `SOCIALACCOUNT_AUTO_SIGNUP = True`; login por e-mail (`ACCOUNT_LOGIN_METHODS = {'email'}`), e-mail único e verificação opcional.
- **Conta já existente:** o `SocialAdapter` (`presentes/adapters.py`) conecta a conta social ao usuário local que tem o mesmo e-mail, sem cair em "conta já existe". Usuários criados pelo login social recebem o avatar padrão.
- Depois do login, o usuário vai para `/dashboard/`.

---

## 🔧 Configuração

### 1. Variáveis de ambiente

No Render (Environment) ou no `.env` local, defina as variáveis do(s) provedor(es) desejado(s).

**Google** ([Google Cloud Console](https://console.cloud.google.com/) → APIs & Services → Credentials → OAuth 2.0 Client ID)
- `GOOGLE_CLIENT_ID` precisa terminar em `.apps.googleusercontent.com`. Escopos usados: `profile`, `email`.

**Facebook** ([Meta for Developers](https://developers.facebook.com/) → app → Settings → Basic)
- `FACEBOOK_APP_ID` é numérico. Escopos: `email`, `public_profile` (Graph API v18.0).

**LinkedIn** ([LinkedIn Developers](https://www.linkedin.com/developers/apps))
- Ative o produto "Sign In with LinkedIn using OpenID Connect". Escopos: `openid`, `profile`, `email`.

**Apple** ([Apple Developer](https://developer.apple.com/account/) → Certificates, Identifiers & Profiles)
- Crie um *Services ID* com Sign in with Apple e uma chave privada (`.p8`).
- Pelo modo como o allauth monta o JWT da Apple, os campos são usados assim:

| Variável | Valor esperado |
|----------|----------------|
| `APPLE_CLIENT_ID` | Services ID (ex.: `br.com.exemplo.lista`) |
| `APPLE_CLIENT_SECRET` | **Key ID** da chave `.p8` (o allauth o usa como `kid`) |
| `APPLE_KEY_ID` | **Team ID** (o allauth o usa como `iss`) |
| `APPLE_PRIVATE_KEY` | Conteúdo do `.p8`, com `-----BEGIN PRIVATE KEY-----` |

> Os nomes `APPLE_CLIENT_SECRET` e `APPLE_KEY_ID` não correspondem ao conteúdo esperado; siga a tabela acima.

### 2. URLs de callback

Cadastre em cada provedor (as rotas do allauth ficam em `/accounts/`):

```
https://lista-presentes-im4b.onrender.com/accounts/google/login/callback/
https://lista-presentes-im4b.onrender.com/accounts/facebook/login/callback/
https://lista-presentes-im4b.onrender.com/accounts/linkedin_oauth2/login/callback/
https://lista-presentes-im4b.onrender.com/accounts/apple/login/callback/
```

Para desenvolvimento local, use os mesmos caminhos com `http://localhost:8000`.

### 3. Validar as credenciais

```bash
python manage.py validar_social             # valida contra a API de cada provedor
python manage.py validar_social --formato   # só o formato, sem rede
```

O comando mostra quais provedores estão válidos (botão visível) e quais estão ausentes ou inválidos (botão oculto).

### 4. Testar

Abra `/login/` (ou `/`), clique no botão do provedor, autorize e confira o redirecionamento para `/dashboard/`.

---

## 🆘 Troubleshooting

- **Botão não aparece:** a credencial está vazia ou com formato inválido. Rode `python manage.py validar_social`.
- **`redirect_uri_mismatch` / `invalid_redirect_uri`:** a URL de callback cadastrada no provedor difere da usada (domínio, `https` ou barra final).
- **`invalid_client`:** client ID/secret incorretos. Confira com `validar_social`.
- **`Site matching query does not exist`:** rode `python manage.py migrate` (o `SITE_ID = 1` vem da app `django.contrib.sites`).

Documentação: https://docs.allauth.org/
