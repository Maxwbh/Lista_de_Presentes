# GitHub Actions Workflows

Este diretório contém os workflows de CI/CD do projeto.

## 📋 Workflows Disponíveis

### 1. `tests.yml` - Testes Automatizados

**Trigger:**
- Push em branches `master` e `claude/*`
- Pull requests para `master`
- Manual via GitHub Actions UI

**O que faz:**
- ✅ Roda testes em Python 3.11 e 3.12
- ✅ Testa com PostgreSQL 15
- ✅ Gera relatório de cobertura (coverage)
- ✅ Verifica formatação de código (black, isort)
- ✅ Análise de qualidade (flake8)
- ✅ Scan de segurança (safety, bandit)
- ✅ Verifica migrations pendentes

**Artifacts gerados:**
- `coverage-report` - Relatório HTML de cobertura
- `security-reports` - Relatórios de segurança (bandit)

**Jobs:**
1. **test** - Testes unitários com coverage
2. **lint** - Análise de código (flake8, black, isort)
3. **security** - Verificações de segurança (safety, bandit)

---

### 2. `deploy.yml` - Deploy Automático

**Trigger:**
- Push no branch `master`
- Manual via GitHub Actions UI

**O que faz:**
- 📡 Notifica início do deploy
- ⏳ Aguarda Render detectar push
- 🔍 Verifica status da aplicação
- 📊 Gera resumo do deploy

**Observação:**
O Render faz deploy automático ao detectar push no `master`. Este workflow apenas monitora o processo.

---

### 3. `keep-alive.yml` - Manter Render Ativo

**Trigger:**
- Cron job: a cada 10 minutos
- Manual via GitHub Actions UI

**O que faz:**
- 🏓 Faz ping no endpoint `/health/`
- ⚡ Mede latência
- 📊 Monitora uptime

**Objetivo:**
Evitar que o Render Free tier coloque a aplicação em sleep após 15 minutos de inatividade.

---

## 🚀 Como Usar

### Executar Testes Localmente

```bash
# Instalar dependências de teste
pip install coverage pytest pytest-django flake8 black isort safety bandit

# Rodar testes
python manage.py test

# Rodar com coverage
coverage run --source='.' manage.py test
coverage report
coverage html

# Verificar formatação
black --check .
isort --check-only .
flake8 .

# Scan de segurança
safety check
bandit -r presentes/ lista_presentes/
```

### Executar Workflows Manualmente

1. Vá em **Actions** no GitHub
2. Selecione o workflow desejado
3. Clique em **Run workflow**
4. Escolha o branch
5. Clique em **Run workflow**

### Visualizar Resultados

1. Vá em **Actions** no GitHub
2. Clique no workflow executado
3. Veja os logs de cada job
4. Baixe artifacts (se disponível)

---

## 📊 Status Badges

Adicione ao README.md principal:

```markdown
![Tests](https://github.com/Maxwbh/Lista_de_Presentes/actions/workflows/tests.yml/badge.svg)
![Deploy](https://github.com/Maxwbh/Lista_de_Presentes/actions/workflows/deploy.yml/badge.svg)
![Keep Alive](https://github.com/Maxwbh/Lista_de_Presentes/actions/workflows/keep-alive.yml/badge.svg)
```

---

## 🔧 Configuração

### Secrets Necessários

Nenhum secret é necessário para os workflows atuais. Se adicionar integração com Slack, Discord, etc., configure em:

**Settings → Secrets and variables → Actions**

Exemplo:
- `SLACK_WEBHOOK_URL`
- `DISCORD_WEBHOOK_URL`
- `RENDER_API_KEY`

### Variáveis de Ambiente

Configuradas diretamente nos workflows ou em `.env` para execução local.

---

## 🐛 Troubleshooting

### Testes Falhando

1. Verifique os logs no GitHub Actions
2. Rode localmente: `python manage.py test`
3. Verifique se todas as dependências estão instaladas
4. Verifique se o PostgreSQL está rodando (para testes locais)

### Deploy Não Funciona

1. Verifique o Render Dashboard
2. Verifique se o branch `master` foi atualizado
3. Verifique logs de build no Render
4. Verifique se `build.sh` está configurado corretamente

### Keep-Alive Falhando

1. Verifique se a URL está correta
2. Verifique se o endpoint `/health/` existe
3. Verifique se o Render está online

---

## 📝 Melhorias Futuras

- [ ] Adicionar notificações no Slack/Discord
- [ ] Adicionar testes de integração end-to-end
- [ ] Adicionar deploy em staging antes de production
- [ ] Adicionar rollback automático em caso de erro
- [ ] Adicionar performance tests (load testing)
- [ ] Adicionar dependency update bot (Dependabot)

---

**Desenvolvido por**: Maxwell Oliveira (@maxwbh)
**Empresa**: M&S do Brasil LTDA
**Versão**: 1.1.9
