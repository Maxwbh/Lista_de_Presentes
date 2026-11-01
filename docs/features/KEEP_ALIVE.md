# 🔥 Keep-Alive do Render

No plano gratuito do Render o serviço dorme depois de **15 minutos sem tráfego** e o primeiro acesso seguinte leva ~50 s para acordá-lo. O workflow `keep-alive.yml` faz um ping periódico para manter o servidor acordado **apenas nas horas em que o sistema é usado**.

> ⚠️ **Limite do Render Free:** 750 horas de instância por mês, somadas entre todos os serviços da conta. Acordado 24h, este serviço gastaria ~744h. Por isso o ping roda só nas horas de uso (~200h/mês).

---

## 🤖 Workflow `keep-alive.yml`

Arquivo: [`.github/workflows/keep-alive.yml`](../../.github/workflows/keep-alive.yml)

- Faz `GET /health/` (responde `OK`, HTTP 200) **a cada 14 minutos**, só nas horas listadas para cada dia da semana.
- A URL vem da variável de repositório `RENDER_URL` (Settings → Secrets and variables → Actions → Variables); sem ela, usa `https://lista-presentes-im4b.onrender.com`.
- Também pode ser executado manualmente (`workflow_dispatch`): Actions → **Keep Render Alive** → **Run workflow**.

### 🕐 Horas cobertas (Brasília)

Escolhidas a partir do relatório de acessos de 31/10/2026 (últimos 30 dias). Próxima revisão combinada: ~30/11/2026.

| Dia | Horas |
|-----|-------|
| Segunda | 09-11h, 14h, 17h, 23h |
| Terça | 09h, 11h |
| Quarta | 08-10h, 12-13h, 16-18h, 22h |
| Quinta | 00h, 07-08h, 15h, 18-20h, 23h |
| Sexta | 05h, 07h, 22h |
| Sábado | 00h, 08-09h, 13-14h, 16h, 19h, 21-23h |
| Domingo | 15h |

Fora dessas horas o servidor dorme e o primeiro acesso o acorda.

O GitHub Actions usa **UTC** (Brasília + 3h): as horas de Brasília a partir das 21h caem no dia seguinte em UTC. Por isso cada linha `cron` do arquivo traz um comentário com a conversão. Ao alterar as horas, mantenha essa correspondência.

---

## 📊 Registro de acessos

Os horários são escolhidos com base em dados reais coletados pelo próprio sistema ([`presentes/acessos.py`](../../presentes/acessos.py)):

- **`RegistroAcessoMiddleware`** (registrado em `settings.MIDDLEWARE`):
  - **`DespertarServidor`**: grava cada vez que o servidor sobe (ao acordar), com a primeira requisição, o caminho e a origem (`USUARIO` ou `MONITOR`).
  - **`AcessoHora`**: conta os acessos de pessoas por data e hora (horário local). Ignora pings de monitoramento (user agents como `github`, `curl/`, `uptimerobot`, bots) e caminhos como `/static/`, `/health/`, `/api/notificacoes/`, `/api/push/` e `/api/cron/`.
- Os dois modelos aparecem no Django Admin.

### Resumo: `/api/acessos/resumo/`

Retorna JSON com acessos por hora, por dia da semana, horas de pico, faixas sugeridas, uma sugestão de `cron` (`cron_keep_alive_utc`, uma linha única para todos os dias) e o total de despertares (por usuário e por monitor).

- **Acesso:** superusuário logado **ou** header `X-Cron-Token` com o valor de `CRON_TOKEN`.
- **Parâmetros:** `?dias=30` (1 a 365) e `?limite=5` (percentual mínimo de acessos para a hora ser pico).
- Pelo terminal: `python manage.py analisar_acessos [--dias 30] [--limite 5]`.

### Workflow `relatorio-acessos.yml`

Arquivo: [`.github/workflows/relatorio-acessos.yml`](../../.github/workflows/relatorio-acessos.yml)

- **Somente sob demanda** (`workflow_dispatch`): Actions → **Relatorio de Acessos** → **Run workflow** (entrada opcional `dias`, padrão 30).
- Acorda o servidor, chama `/api/acessos/resumo/` com o header `X-Cron-Token` e mostra o JSON no log e no resumo da execução; também guarda o arquivo `resumo-acessos.json` como artefato (90 dias).
- O resumo só tem contagens, nenhum dado pessoal.

### 🔑 `CRON_TOKEN`

Precisa ter **o mesmo valor** em dois lugares:

1. **Render** → Environment → `CRON_TOKEN`
2. **GitHub** → Settings → Secrets and variables → Actions → Secrets → `CRON_TOKEN`

O mesmo token protege `/api/cron/pesquisar-precos/` (workflow `pesquisa-precos.yml`).

### Como revisar as horas

1. Rode o workflow **Relatorio de Acessos**.
2. Veja `acessos_por_dia_semana` (listas de 24 posições, uma por hora, de `seg` a `dom`).
3. Atualize as linhas `cron` e os comentários de `keep-alive.yml`, convertendo para UTC.

---

## 🔍 Como testar

```bash
curl -i https://lista-presentes-im4b.onrender.com/health/   # esperado: HTTP 200, corpo "OK"
gh run list --workflow="Keep Render Alive"                 # últimas execuções
```

---

## ⚠️ Troubleshooting

### O agendamento parou de rodar

Em repositórios públicos, o GitHub **desativa os workflows agendados depois de 60 dias sem atividade no repositório**. Para reativar: Actions → **Keep Render Alive** → menu `...` → **Disable workflow** e depois **Enable workflow** (ou apenas **Enable workflow**, se já estiver desativado).

Lembre também que o GitHub não garante o horário exato: execuções agendadas podem atrasar ou ser puladas em horários de pico.

### Relatório de acessos falha

- `Secret CRON_TOKEN nao configurado`: crie o secret no GitHub.
- `resumo: HTTP 403`: o valor do secret é diferente do `CRON_TOKEN` do Render.

### Servidor ainda demora a responder

- Fora das horas listadas isso é esperado.
- Dentro delas, confira as execuções em Actions e os logs do Render.

### Health check retorna erro

Veja os logs no Render e rode `python manage.py check`.

---

## 💡 Alternativas externas

Serviços como [UptimeRobot](https://uptimerobot.com) ou [cron-job.org](https://cron-job.org) também podem pingar `/health/`. Eles não estão configurados no projeto. Se usar algum, restrinja os horários para não passar do limite de 750h/mês.

---

**Referências:** [Render Free](https://render.com/docs/free) · [GitHub Actions: desativar e ativar workflows](https://docs.github.com/pt/actions/managing-workflow-runs-and-deployments/managing-workflow-runs/disabling-and-enabling-a-workflow)
