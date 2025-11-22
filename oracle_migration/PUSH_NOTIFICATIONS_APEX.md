

# Push Notifications para Oracle APEX 24

> **Desenvolvedor:** Maxwell da Silva Oliveira (@maxwbh) | **Empresa:** M&S do Brasil LTDA | **Site:** [msbrasil.inf.br](http://msbrasil.inf.br)

## 📱 Visão Geral

Este documento descreve a implementação completa de **Push Notifications** para o sistema de Lista de Presentes usando Oracle APEX 24 e Progressive Web App (PWA).

## 🎯 Funcionalidades

✅ **Registro de Subscriptions**
- Suporte a múltiplos dispositivos por usuário
- Armazenamento seguro de chaves de criptografia (P256DH, Auth)
- Tracking de User Agent e IP

✅ **Envio de Notificações**
- Push individual para usuário
- Push para subscription específica
- Broadcast para todos usuários
- Integração automática com sistema de notificações

✅ **Gerenciamento**
- Ativar/Desativar subscriptions
- Limpeza automática de subscriptions inativas
- Log completo de envios e erros
- Estatísticas detalhadas

✅ **Trigger Automático**
- Push notification enviado automaticamente quando criar notificação
- Integrado com PKG_COMPRA, PKG_PRESENTE, etc.

---

## 📦 Estrutura Criada

### Tabelas

**TB_PUSH_SUBSCRIPTION**
- Armazena subscriptions dos usuários
- Campos: endpoint, keys, user_agent, estatísticas

**TB_PUSH_LOG**
- Log de todos envios de push
- Campos: status, erro, data, vinculação com notificação

### Package

**PKG_PUSH_NOTIFICATION**
- `REGISTRAR_SUBSCRIPTION` - Registra nova subscription
- `ENVIAR_PUSH_USUARIO` - Envia push para um usuário
- `ENVIAR_PUSH_BROADCAST` - Envia para todos
- `LISTAR_SUBSCRIPTIONS_USUARIO` - Lista subscriptions
- `TEM_SUBSCRIPTION_ATIVA` - Verifica se usuário tem push ativo
- `LIMPAR_SUBSCRIPTIONS_INATIVAS` - Remove subscriptions antigas

### Views

**VW_PUSH_ESTATISTICAS**
- Estatísticas por usuário
- Taxa de sucesso, total enviados, total erros

### Triggers

**TRG_NOTIFICACAO_PUSH**
- Dispara automaticamente quando criar notificação
- Envia push notification se usuário tiver subscription ativa

### Procedures APEX

**APEX_REGISTRAR_PUSH_SUBSCRIPTION** - Endpoint para registro
**APEX_REMOVER_PUSH_SUBSCRIPTION** - Endpoint para remoção
**APEX_PROCESSAR_PUSH_PENDENTES** - Processa fila de envios

### Jobs Agendados

**JOB_PROCESSAR_PUSH_PENDENTES** - A cada 1 minuto
**JOB_LIMPAR_PUSH_INATIVAS** - Diariamente às 3h

---

## 🚀 Instalação

### 1. Executar Scripts SQL

```sql
-- 1. Criar estrutura de push notifications
@07_PKG_PUSH_NOTIFICATION.sql

-- 2. Criar integração com APEX
@08_INTEGRACAO_PUSH_APEX.sql
```

### 2. Habilitar Jobs (Opcional)

```sql
BEGIN
    DBMS_SCHEDULER.ENABLE('JOB_PROCESSAR_PUSH_PENDENTES');
    DBMS_SCHEDULER.ENABLE('JOB_LIMPAR_PUSH_INATIVAS');
END;
/
```

---

## 📱 Configuração do APEX PWA

### Passo 1: Habilitar PWA no APEX

1. Acesse sua aplicação no APEX
2. Vá em **Shared Components** > **Progressive Web App**
3. Habilite **Enable Progressive Web App**
4. Configure:
   - **Application Name:** Lista de Presentes
   - **Short Name:** Presentes
   - **Start URL:** f?p=&APP_ID.:1
   - **Display:** standalone
   - **Theme Color:** #007bff

### Passo 2: Configurar Push Notifications no APEX

1. Em **Progressive Web App** > **Push Notifications**
2. Habilite **Enable Push Notifications**
3. Configure:
   - **VAPID Public Key:** (Gerar usando web-push library)
   - **VAPID Private Key:** (Guardar de forma segura)
   - **VAPID Subject:** mailto:maxwbh@gmail.com

### Passo 3: Gerar VAPID Keys

```javascript
// Usar biblioteca web-push em Node.js
const webpush = require('web-push');
const vapidKeys = webpush.generateVAPIDKeys();

console.log('Public Key:', vapidKeys.publicKey);
console.log('Private Key:', vapidKeys.privateKey);
```

---

## 🔧 Service Worker (JavaScript)

### service-worker.js

```javascript
// Service Worker para Push Notifications
// Este arquivo é gerado automaticamente pelo APEX, mas você pode customizar

self.addEventListener('push', function(event) {
    console.log('Push notification received:', event);

    const data = event.data ? event.data.json() : {
        title: 'Nova Notificação',
        body: 'Você tem uma nova notificação',
        icon: '/i/app-icon.png',
        badge: '/i/badge-icon.png'
    };

    const options = {
        body: data.body || data.mensagem,
        icon: data.icon || '/i/app-icon.png',
        badge: data.badge || '/i/badge-icon.png',
        tag: data.tag || 'notification-' + Date.now(),
        data: {
            url: data.url || '/notificacoes',
            notificationId: data.id
        },
        requireInteraction: data.requireInteraction || false,
        vibrate: [200, 100, 200]
    };

    event.waitUntil(
        self.registration.showNotification(data.title || 'Lista de Presentes', options)
    );
});

self.addEventListener('notificationclick', function(event) {
    console.log('Notification clicked:', event);

    event.notification.close();

    const urlToOpen = event.notification.data.url || '/';

    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true })
            .then(function(windowClients) {
                // Verificar se já existe uma janela aberta
                for (let i = 0; i < windowClients.length; i++) {
                    const client = windowClients[i];
                    if (client.url.indexOf(urlToOpen) !== -1 && 'focus' in client) {
                        return client.focus();
                    }
                }
                // Se não existe, abrir nova janela
                if (clients.openWindow) {
                    return clients.openWindow(urlToOpen);
                }
            })
    );
});
```

---

## 💻 Código JavaScript no APEX

### Página: Dashboard ou Notificações

Adicione este código na **Page Properties** > **JavaScript** > **Execute when Page Loads**:

```javascript
// Função para registrar push notification subscription
async function registrarPushNotification() {
    // Verificar se o browser suporta
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
        console.log('Push notifications não suportadas neste browser');
        return false;
    }

    try {
        // Registrar service worker
        const registration = await navigator.serviceWorker.ready;

        // Solicitar permissão
        const permission = await Notification.requestPermission();

        if (permission !== 'granted') {
            console.log('Permissão de notificação negada');
            return false;
        }

        // Obter VAPID public key do APEX
        // IMPORTANTE: Substituir pela sua chave pública
        const vapidPublicKey = 'SEU_VAPID_PUBLIC_KEY_AQUI';

        // Converter chave para Uint8Array
        const convertedVapidKey = urlBase64ToUint8Array(vapidPublicKey);

        // Criar subscription
        const subscription = await registration.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: convertedVapidKey
        });

        console.log('Subscription criada:', subscription);

        // Enviar subscription para o servidor Oracle
        await salvarSubscriptionNoOracle(subscription);

        return true;

    } catch (error) {
        console.error('Erro ao registrar push notification:', error);
        return false;
    }
}

// Função para converter VAPID key
function urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding)
        .replace(/\-/g, '+')
        .replace(/_/g, '/');

    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);

    for (let i = 0; i < rawData.length; ++i) {
        outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
}

// Função para salvar subscription no Oracle
async function salvarSubscriptionNoOracle(subscription) {
    const subscriptionJson = JSON.parse(JSON.stringify(subscription));

    // Extrair dados da subscription
    const endpoint = subscriptionJson.endpoint;
    const p256dh = subscriptionJson.keys.p256dh;
    const auth = subscriptionJson.keys.auth;

    // Chamar procedure do Oracle via APEX
    apex.server.process(
        'REGISTRAR_PUSH_SUBSCRIPTION',
        {
            x01: endpoint,      // p_endpoint
            x02: p256dh,        // p_p256dh_key
            x03: auth           // p_auth_key
        },
        {
            success: function(data) {
                console.log('Subscription registrada no Oracle:', data);
                apex.message.showPageSuccess('Push notifications ativadas!');
            },
            error: function(jqXHR, textStatus, errorThrown) {
                console.error('Erro ao registrar subscription:', errorThrown);
                apex.message.alert('Erro ao ativar push notifications');
            }
        }
    );
}

// Função para desregistrar push notifications
async function desregistrarPushNotification() {
    try {
        const registration = await navigator.serviceWorker.ready;
        const subscription = await registration.pushManager.getSubscription();

        if (subscription) {
            await subscription.unsubscribe();

            // Remover do Oracle
            apex.server.process(
                'REMOVER_PUSH_SUBSCRIPTION',
                {
                    x01: subscription.endpoint
                },
                {
                    success: function() {
                        apex.message.showPageSuccess('Push notifications desativadas!');
                    }
                }
            );
        }
    } catch (error) {
        console.error('Erro ao desregistrar:', error);
    }
}

// Auto-registrar quando página carregar (opcional)
$(document).ready(function() {
    // Verificar se usuário já tem permissão
    if (Notification.permission === 'granted') {
        // Já tem permissão - registrar silenciosamente
        registrarPushNotification();
    }
});
```

---

## 🎨 Interface no APEX

### Botão para Ativar/Desativar Push

**Página de Configurações ou Dashboard:**

```sql
-- Region: Configurações de Notificações
-- Type: Static Content

-- Botão: Ativar Push Notifications
-- Button Name: BTN_ATIVAR_PUSH
-- Action: Defined by Dynamic Action

-- Dynamic Action: Ativar Push
-- Event: Click
-- Selection Type: Button
-- Button: BTN_ATIVAR_PUSH

-- True Action 1: Execute JavaScript Code
-- Code:
registrarPushNotification();
```

**HTML personalizado:**

```html
<div class="notification-settings">
    <h3>🔔 Push Notifications</h3>
    <p>Receba notificações instantâneas quando alguém comprar seus presentes!</p>

    <button id="btn-toggle-push" class="btn btn-primary">
        <i class="fa fa-bell"></i> Ativar Notificações Push
    </button>

    <div id="push-status" class="mt-3">
        <span class="badge badge-secondary">Status: Desativado</span>
    </div>
</div>

<script>
document.getElementById('btn-toggle-push').addEventListener('click', async function() {
    const permission = Notification.permission;

    if (permission === 'default') {
        // Primeiro acesso - solicitar permissão
        const resultado = await registrarPushNotification();
        if (resultado) {
            this.innerHTML = '<i class="fa fa-bell-slash"></i> Desativar Notificações Push';
            document.getElementById('push-status').innerHTML =
                '<span class="badge badge-success">Status: Ativado ✓</span>';
        }
    } else if (permission === 'granted') {
        // Já tem permissão - desativar
        await desregistrarPushNotification();
        this.innerHTML = '<i class="fa fa-bell"></i> Ativar Notificações Push';
        document.getElementById('push-status').innerHTML =
            '<span class="badge badge-secondary">Status: Desativado</span>';
    } else {
        // Permissão negada
        apex.message.alert('Você bloqueou as notificações. Altere nas configurações do browser.');
    }
});
</script>
```

---

## 🔌 APEX Processes

### Process: REGISTRAR_PUSH_SUBSCRIPTION

**Process Point:** Ajax Callback
**Name:** REGISTRAR_PUSH_SUBSCRIPTION
**Type:** PL/SQL Code

```sql
DECLARE
    v_endpoint      VARCHAR2(1000);
    v_p256dh_key    VARCHAR2(500);
    v_auth_key      VARCHAR2(500);
    v_user_id       NUMBER;
BEGIN
    -- Obter parâmetros
    v_endpoint := APEX_APPLICATION.G_X01;
    v_p256dh_key := APEX_APPLICATION.G_X02;
    v_auth_key := APEX_APPLICATION.G_X03;
    v_user_id := :APP_USER_ID; -- Ou V('APP_USER_ID')

    -- Chamar procedure
    APEX_REGISTRAR_PUSH_SUBSCRIPTION(
        p_user_id => v_user_id,
        p_endpoint => v_endpoint,
        p_p256dh_key => v_p256dh_key,
        p_auth_key => v_auth_key
    );
END;
```

### Process: REMOVER_PUSH_SUBSCRIPTION

**Process Point:** Ajax Callback
**Name:** REMOVER_PUSH_SUBSCRIPTION
**Type:** PL/SQL Code

```sql
DECLARE
    v_endpoint VARCHAR2(1000);
BEGIN
    v_endpoint := APEX_APPLICATION.G_X01;

    APEX_REMOVER_PUSH_SUBSCRIPTION(
        p_endpoint => v_endpoint
    );
END;
```

---

## 📊 Relatórios e Monitoramento

### Interactive Report: Subscriptions Ativas

```sql
SELECT
    ID_SUBSCRIPTION,
    ID_USUARIO,
    SUBSTR(ENDPOINT, 1, 50) || '...' AS ENDPOINT,
    USER_AGENT,
    IP_ADDRESS,
    DATA_SUBSCRIPTION,
    DATA_ULTIMO_ENVIO,
    TOTAL_ENVIADOS,
    TOTAL_ERROS,
    CASE WHEN ATIVO = 'S' THEN 'Ativa' ELSE 'Inativa' END AS STATUS
FROM TB_PUSH_SUBSCRIPTION
WHERE ID_USUARIO = :APP_USER_ID
ORDER BY DATA_SUBSCRIPTION DESC;
```

### Dashboard: Estatísticas Push

```sql
SELECT * FROM VW_PUSH_ESTATISTICAS
WHERE ID_USUARIO = :APP_USER_ID;
```

### Log de Envios

```sql
SELECT
    l.ID_LOG,
    l.TITULO,
    SUBSTR(l.MENSAGEM, 1, 100) AS MENSAGEM,
    l.STATUS,
    l.DATA_ENVIO,
    CASE
        WHEN l.STATUS = 'ENVIADO' THEN '<span class="badge badge-success">Enviado</span>'
        WHEN l.STATUS = 'ERRO' THEN '<span class="badge badge-danger">Erro</span>'
        ELSE '<span class="badge badge-warning">Pendente</span>'
    END AS STATUS_HTML
FROM TB_PUSH_LOG l
INNER JOIN TB_PUSH_SUBSCRIPTION s ON l.ID_SUBSCRIPTION = s.ID_SUBSCRIPTION
WHERE s.ID_USUARIO = :APP_USER_ID
ORDER BY l.DATA_ENVIO DESC
FETCH FIRST 50 ROWS ONLY;
```

---

## 🧪 Testando Push Notifications

### Teste 1: Registro de Subscription

```sql
-- Simular registro de subscription
DECLARE
    v_id NUMBER;
BEGIN
    v_id := PKG_PUSH_NOTIFICATION.REGISTRAR_SUBSCRIPTION(
        p_id_usuario => 1,
        p_endpoint => 'https://fcm.googleapis.com/fcm/send/teste123',
        p_p256dh_key => 'TEST_P256DH_KEY',
        p_auth_key => 'TEST_AUTH_KEY',
        p_user_agent => 'Mozilla/5.0 (Test Browser)',
        p_ip_address => '127.0.0.1'
    );

    DBMS_OUTPUT.PUT_LINE('Subscription ID: ' || v_id);
END;
/
```

### Teste 2: Enviar Push

```sql
-- Enviar push para usuário
DECLARE
    v_count NUMBER;
BEGIN
    v_count := PKG_PUSH_NOTIFICATION.ENVIAR_PUSH_USUARIO(
        p_id_usuario => 1,
        p_titulo => '🎁 Teste de Push',
        p_mensagem => 'Esta é uma notificação de teste!'
    );

    DBMS_OUTPUT.PUT_LINE('Push enviado para ' || v_count || ' subscriptions');
END;
/
```

### Teste 3: Verificar Estatísticas

```sql
SELECT * FROM TABLE(PKG_PUSH_NOTIFICATION.OBTER_ESTATISTICAS);
```

---

## 🔐 Segurança

### Boas Práticas

1. **VAPID Keys Seguras**
   - Nunca commitar as chaves private no git
   - Armazenar em variáveis de ambiente ou APEX Application Items (protegidos)

2. **Validação de Origem**
   - Verificar User-Agent suspeitos
   - Limitar taxa de registro por IP

3. **Limpeza de Dados**
   - Remover subscriptions inativas periodicamente
   - Limpar logs antigos (> 90 dias)

4. **Permissões Oracle**
```sql
-- Grant apenas para schema da aplicação
GRANT EXECUTE ON PKG_PUSH_NOTIFICATION TO APEX_APP_USER;
GRANT EXECUTE ON APEX_REGISTRAR_PUSH_SUBSCRIPTION TO APEX_APP_USER;
GRANT EXECUTE ON APEX_REMOVER_PUSH_SUBSCRIPTION TO APEX_APP_USER;
```

---

## 🚀 Deploy em Produção

### Checklist

- [ ] Gerar VAPID Keys (produção)
- [ ] Configurar VAPID Keys no APEX
- [ ] Executar scripts de criação
- [ ] Habilitar jobs agendados
- [ ] Testar em diferentes browsers (Chrome, Firefox, Safari)
- [ ] Testar em diferentes dispositivos (Desktop, Mobile, Tablet)
- [ ] Configurar ícones PWA
- [ ] Adicionar botão de ativar/desativar push
- [ ] Documentar processo para usuários
- [ ] Monitorar logs de erro

---

## 📱 Compatibilidade de Browsers

| Browser | Desktop | Mobile | Notas |
|---------|---------|--------|-------|
| Chrome | ✅ | ✅ | Suporte completo |
| Firefox | ✅ | ✅ | Suporte completo |
| Safari | ⚠️ | ⚠️ | iOS 16.4+ apenas |
| Edge | ✅ | ✅ | Suporte completo |
| Opera | ✅ | ✅ | Suporte completo |

---

## 🐛 Troubleshooting

### Erro: "Push not supported"

**Causa:** Browser não suporta ou HTTPS não configurado
**Solução:** Push notifications requerem HTTPS (ou localhost para testes)

### Erro: "Permission denied"

**Causa:** Usuário negou permissão
**Solução:** Solicitar ao usuário alterar nas configurações do browser

### Erro: "Invalid VAPID key"

**Causa:** Chave VAPID incorreta ou não configurada
**Solução:** Verificar configuração no APEX PWA

### Push não recebido

**Causas possíveis:**
1. Subscription inativa - Verificar TB_PUSH_SUBSCRIPTION
2. Job não habilitado - Habilitar JOB_PROCESSAR_PUSH_PENDENTES
3. Erro de rede - Verificar TB_PUSH_LOG

---

## 📞 Suporte

Para dúvidas:
- Consultar logs: `SELECT * FROM TB_PUSH_LOG WHERE STATUS = 'ERRO'`
- Verificar subscriptions: `SELECT * FROM VW_PUSH_ESTATISTICAS`
- Documentação APEX PWA: https://docs.oracle.com/en/database/oracle/apex/

---

**Sistema de Push Notifications pronto para produção!** 🚀
