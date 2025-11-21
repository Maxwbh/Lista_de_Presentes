# 🔥 Keep Render Alive - Guia Completo

Este documento explica como manter seu app no Render.com ativo 24/7, evitando que ele entre em modo "sleep" após 15 minutos de inatividade.

---

## 📊 Status Atual

✅ **Endpoint de Health Check**: `/health/` já configurado
✅ **GitHub Action**: Ping automático a cada 10 minutos
✅ **URL do app**: https://lista-presentes-0hbp.onrender.com

---

## 🤖 Solução 1: GitHub Actions (Recomendada) ✅ ATIVA

### ✅ Já está configurado!

O arquivo `.github/workflows/keep-alive.yml` já está criado e faz:
- 🏓 Ping no `/health/` a cada 10 minutos
- 📊 Mede latência do servidor
- ✅ Verifica se resposta é 200 OK
- 📈 Logs detalhados de cada execução

### Como verificar se está funcionando:

1. Acesse: https://github.com/Maxwbh/Lista_de_Presentes/actions
2. Veja a aba "Keep Render Alive"
3. Cada execução aparecerá com timestamp

### Testar manualmente:

1. Vá em: https://github.com/Maxwbh/Lista_de_Presentes/actions
2. Clique em "Keep Render Alive"
3. Clique em "Run workflow" → "Run workflow"
4. Aguarde ~30 segundos e veja o resultado

### Vantagens:
- ✅ **Totalmente grátis** - GitHub Actions tem 2.000 minutos/mês grátis
- ✅ **Automático** - não precisa manutenção
- ✅ **Confiável** - infraestrutura do GitHub
- ✅ **Logs detalhados** - veja cada ping
- ✅ **Sem cadastro adicional** - usa seu GitHub

### Desvantagens:
- ⚠️ Se o repositório ficar 60 dias sem commits, o cron para (basta fazer 1 commit)

---

## 🌐 Solução 2: UptimeRobot (Backup Recomendado)

**Website**: https://uptimerobot.com
**Plano Grátis**: 50 monitores, check a cada 5 minutos

### Como configurar:

1. **Criar conta**: https://uptimerobot.com/signUp
2. **Adicionar monitor**:
   - Clique em "+ Add New Monitor"
   - Monitor Type: `HTTP(s)`
   - Friendly Name: `Lista de Presentes`
   - URL: `https://lista-presentes-0hbp.onrender.com/health/`
   - Monitoring Interval: `5 minutes` (plano grátis)
   - Monitor Timeout: `30 seconds`
   - HTTP Method: `GET`
   - Expected Status Code: `200`
3. **Salvar** e pronto!

### Vantagens:
- ✅ **Check a cada 5 minutos** (mais frequente que GitHub)
- ✅ **Dashboard visual** com uptime history
- ✅ **Alertas por email** se o site cair
- ✅ **Status page pública** (opcional)
- ✅ **50 monitores grátis** (pode monitorar outros sites)

### Configuração de alertas:
1. Settings → Alert Contacts
2. Adicione seu email
3. Receba notificação se o site ficar offline > 5 min

---

## 🕐 Solução 3: Cron-job.org

**Website**: https://cron-job.org
**Plano Grátis**: Ilimitado, check a cada 1 minuto (!)

### Como configurar:

1. **Criar conta**: https://console.cron-job.org/signup
2. **Verificar email** e fazer login
3. **Criar cron job**:
   - Menu → Cronjobs → Create cronjob
   - Title: `Keep Render Alive - Lista Presentes`
   - Address: `https://lista-presentes-0hbp.onrender.com/health/`
   - Schedule:
     - Every: `10 minutes` (recomendado)
     - ou Every: `5 minutes` (mais agressivo)
   - Request method: `GET`
   - Save cronjob

### Vantagens:
- ✅ **Checks muito frequentes** (até 1 minuto!)
- ✅ **Logs de execução** (últimas 100 execuções)
- ✅ **Notificações por email** em caso de falha
- ✅ **Interface simples** e fácil de usar

### Desvantagens:
- ⚠️ Requer criar conta separada
- ⚠️ Logs expiram após 100 execuções

---

## 🔧 Solução 4: Script Python Local (Avançado)

Se você tem um servidor próprio ou Raspberry Pi sempre ligado:

```python
#!/usr/bin/env python3
"""
keep_alive.py - Mantém o Render acordado
Uso: python3 keep_alive.py
"""

import requests
import time
from datetime import datetime

URL = "https://lista-presentes-0hbp.onrender.com/health/"
INTERVAL = 600  # 10 minutos em segundos

def ping():
    try:
        start = time.time()
        response = requests.get(URL, timeout=30)
        latency = int((time.time() - start) * 1000)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if response.status_code == 200:
            print(f"✅ [{timestamp}] OK - {latency}ms")
        else:
            print(f"⚠️ [{timestamp}] Status {response.status_code} - {latency}ms")

    except Exception as e:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"❌ [{timestamp}] Erro: {e}")

if __name__ == "__main__":
    print(f"🚀 Iniciando keep-alive para {URL}")
    print(f"⏰ Intervalo: {INTERVAL}s ({INTERVAL//60} minutos)")
    print("-" * 60)

    while True:
        ping()
        time.sleep(INTERVAL)
```

### Executar em background (Linux/Mac):

```bash
# Instalar requests
pip3 install requests

# Executar em background
nohup python3 keep_alive.py &

# Ver logs
tail -f nohup.out

# Parar
pkill -f keep_alive.py
```

---

## 📊 Comparação de Soluções

| Solução | Custo | Frequência | Confiabilidade | Setup |
|---------|-------|------------|----------------|-------|
| **GitHub Actions** | Grátis | 10 min | ⭐⭐⭐⭐⭐ | ✅ Feito |
| **UptimeRobot** | Grátis | 5 min | ⭐⭐⭐⭐⭐ | 5 min |
| **Cron-job.org** | Grátis | 1-10 min | ⭐⭐⭐⭐ | 5 min |
| **Script Python** | Grátis* | Customizável | ⭐⭐⭐ | 15 min |

\* Requer servidor próprio 24/7

---

## 🎯 Recomendação Final

### Setup Ideal (Redundância):

1. **GitHub Actions** (principal) - ✅ **Já configurado**
2. **UptimeRobot** (backup) - Configure em 5 minutos
3. **Cron-job.org** (redundância extra) - Opcional

Com essa configuração tripla, seu app **nunca** vai dormir!

### Setup Mínimo (Suficiente):

- **GitHub Actions apenas** - ✅ **Já está ativo**

---

## 🔍 Como Testar

### 1. Testar Health Check Manualmente:

```bash
curl -i https://lista-presentes-0hbp.onrender.com/health/
```

Resposta esperada:
```
HTTP/2 200
content-type: text/html; charset=utf-8
...

OK
```

### 2. Verificar GitHub Action:

```bash
# Acesse
https://github.com/Maxwbh/Lista_de_Presentes/actions

# Ou via CLI (se tiver gh instalado)
gh workflow list
gh run list --workflow="Keep Render Alive"
```

### 3. Verificar Logs do Render:

```bash
# Dashboard do Render
https://dashboard.render.com/

# Veja "Events" e "Logs" - deverá ver:
# [GET] /health/ 200 - ... ms
```

---

## ⚠️ Troubleshooting

### GitHub Action não está rodando?

**Motivo 1**: Repositório sem atividade por 60 dias
- **Solução**: Faça 1 commit qualquer

**Motivo 2**: Actions desabilitadas
- **Solução**: Settings → Actions → "Allow all actions"

**Motivo 3**: Falta de permissões
- **Solução**: Settings → Actions → Workflow permissions → "Read and write"

### Render ainda está dormindo?

**Sintoma**: Primeiro request demora 30-60s
- **Diagnóstico**: Render está iniciando (cold start)
- **Solução**:
  - Verifique se o ping está funcionando
  - Reduza intervalo (GitHub: 5min, UptimeRobot: 5min, Cron-job: 5min)
  - Configure múltiplos serviços (redundância)

### Health check retorna 500?

- Verifique se há erro no Django
- Rode: `python manage.py check`
- Veja logs no Render Dashboard

---

## 💡 Dicas Extras

### 1. Adicionar Logs Detalhados

Edite `presentes/views.py` se quiser ver quem está pingando:

```python
def health_check(request):
    """Health check endpoint para Render.com e outros serviços"""
    user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
    logger.info(f"Health check recebido de: {user_agent}")
    return HttpResponse("OK", status=200)
```

### 2. Criar Status Page Pública

Use UptimeRobot para criar uma página pública de status:
1. UptimeRobot → Add Status Page
2. URL pública: `https://stats.uptimerobot.com/XXXXX`
3. Adicione ao README.md

### 3. Monitorar Múltiplos Endpoints

Além de `/health/`, monitore:
- `/` (home)
- `/login/` (autenticação)
- `/api/notificacoes/` (API)

---

## 📈 Monitoramento Avançado (Opcional)

Se quiser estatísticas detalhadas, use **Better Stack** (ex-Logtail):

1. **Website**: https://betterstack.com/uptime
2. **Plano grátis**: 10 monitores, 3 min interval
3. **Features**:
   - Status page automática
   - SSL monitoring
   - Alertas via Slack, Discord, Telegram
   - Grafana dashboard integrado

---

## 🚀 Status: TUDO CONFIGURADO!

✅ Health check endpoint: `https://lista-presentes-0hbp.onrender.com/health/`
✅ GitHub Action: Ping a cada 10 minutos
✅ Logs: https://github.com/Maxwbh/Lista_de_Presentes/actions

**Próximo passo**: Configure UptimeRobot como backup (leva 5 minutos)

---

## 📞 Suporte

- **GitHub Actions Docs**: https://docs.github.com/en/actions
- **Render Docs**: https://render.com/docs/free#free-web-services
- **UptimeRobot Docs**: https://blog.uptimerobot.com/what-is-monitoring-interval/

---

**Última atualização**: 2025-11-21
