/**
 * JavaScript - Lista de Presentes PWA
 * Oracle APEX 24
 *
 * Desenvolvedor: Maxwell da Silva Oliveira (@maxwbh)
 * Email: maxwbh@gmail.com
 * Empresa: M&S do Brasil LTDA - msbrasil.inf.br
 */

// ============================================================================
// CONFIGURACOES
// ============================================================================
const LP_CONFIG = {
    appId: 'LISTA_PRESENTES',
    swPath: '/pwa/service-worker.js',
    vapidPublicKey: 'YOUR_VAPID_PUBLIC_KEY_HERE', // Substituir pela chave real
    apiEndpoint: '/ords/api/v1/'
};

// ============================================================================
// INICIALIZACAO
// ============================================================================
document.addEventListener('DOMContentLoaded', function() {
    console.log('[LP] Aplicacao iniciada');

    // Registrar Service Worker
    registerServiceWorker();

    // Verificar instalacao PWA
    checkPWAInstall();

    // Inicializar notificacoes
    initPushNotifications();

    // Listeners globais
    initGlobalListeners();
});

// ============================================================================
// SERVICE WORKER
// ============================================================================
async function registerServiceWorker() {
    if ('serviceWorker' in navigator) {
        try {
            const registration = await navigator.serviceWorker.register(LP_CONFIG.swPath, {
                scope: '/ords/'
            });

            console.log('[LP] ServiceWorker registrado:', registration.scope);

            // Verificar atualizacoes
            registration.addEventListener('updatefound', () => {
                const newWorker = registration.installing;
                console.log('[LP] Nova versao do ServiceWorker encontrada');

                newWorker.addEventListener('statechange', () => {
                    if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                        showUpdateNotification();
                    }
                });
            });

        } catch (error) {
            console.error('[LP] Erro ao registrar ServiceWorker:', error);
        }
    }
}

function showUpdateNotification() {
    if (confirm('Nova versao disponivel! Deseja atualizar?')) {
        window.location.reload();
    }
}

// ============================================================================
// PWA INSTALL
// ============================================================================
let deferredPrompt = null;

function checkPWAInstall() {
    window.addEventListener('beforeinstallprompt', (e) => {
        e.preventDefault();
        deferredPrompt = e;
        showInstallBanner();
    });

    window.addEventListener('appinstalled', () => {
        console.log('[LP] App instalado!');
        hideInstallBanner();
        deferredPrompt = null;
    });
}

function showInstallBanner() {
    const banner = document.querySelector('.lp-install-banner');
    if (banner) {
        banner.classList.add('show');
    }
}

function hideInstallBanner() {
    const banner = document.querySelector('.lp-install-banner');
    if (banner) {
        banner.classList.remove('show');
    }
}

async function installPWA() {
    if (!deferredPrompt) {
        console.log('[LP] Prompt de instalacao nao disponivel');
        return;
    }

    deferredPrompt.prompt();

    const { outcome } = await deferredPrompt.userChoice;
    console.log('[LP] Escolha do usuario:', outcome);

    deferredPrompt = null;
    hideInstallBanner();
}

// ============================================================================
// PUSH NOTIFICATIONS
// ============================================================================
async function initPushNotifications() {
    if (!('Notification' in window)) {
        console.log('[LP] Navegador nao suporta notificacoes');
        return;
    }

    if (!('PushManager' in window)) {
        console.log('[LP] Navegador nao suporta Push');
        return;
    }

    // Verificar permissao atual
    if (Notification.permission === 'granted') {
        await subscribeToPush();
    } else if (Notification.permission === 'default') {
        // Mostrar botao para solicitar permissao
        showNotificationPermissionButton();
    }
}

async function requestNotificationPermission() {
    const permission = await Notification.requestPermission();

    if (permission === 'granted') {
        console.log('[LP] Permissao para notificacoes concedida');
        await subscribeToPush();
        hideNotificationPermissionButton();
    } else {
        console.log('[LP] Permissao para notificacoes negada');
    }
}

async function subscribeToPush() {
    try {
        const registration = await navigator.serviceWorker.ready;

        // Verificar subscription existente
        let subscription = await registration.pushManager.getSubscription();

        if (!subscription) {
            // Criar nova subscription
            subscription = await registration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: urlBase64ToUint8Array(LP_CONFIG.vapidPublicKey)
            });
        }

        console.log('[LP] Push subscription:', subscription);

        // Enviar para o servidor
        await sendSubscriptionToServer(subscription);

    } catch (error) {
        console.error('[LP] Erro ao subscrever push:', error);
    }
}

async function sendSubscriptionToServer(subscription) {
    try {
        await apex.server.process('REGISTRAR_PUSH', {
            x01: JSON.stringify(subscription)
        });
        console.log('[LP] Subscription registrada no servidor');
    } catch (error) {
        console.error('[LP] Erro ao registrar subscription:', error);
    }
}

function showNotificationPermissionButton() {
    const btn = document.getElementById('btn-enable-notifications');
    if (btn) {
        btn.style.display = 'inline-flex';
    }
}

function hideNotificationPermissionButton() {
    const btn = document.getElementById('btn-enable-notifications');
    if (btn) {
        btn.style.display = 'none';
    }
}

// ============================================================================
// FUNCOES UTILITARIAS
// ============================================================================

/**
 * Converter VAPID key de base64 para Uint8Array
 */
function urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding)
        .replace(/-/g, '+')
        .replace(/_/g, '/');

    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);

    for (let i = 0; i < rawData.length; ++i) {
        outputArray[i] = rawData.charCodeAt(i);
    }

    return outputArray;
}

/**
 * Formatar valor monetario
 */
function formatCurrency(value) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(value);
}

/**
 * Formatar data relativa
 */
function formatRelativeTime(date) {
    const now = new Date();
    const diff = now - new Date(date);
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 7) {
        return new Date(date).toLocaleDateString('pt-BR');
    } else if (days > 1) {
        return `${days} dias atras`;
    } else if (days === 1) {
        return 'Ontem';
    } else if (hours > 1) {
        return `${hours} horas atras`;
    } else if (hours === 1) {
        return '1 hora atras';
    } else if (minutes > 1) {
        return `${minutes} minutos atras`;
    } else {
        return 'Agora mesmo';
    }
}

/**
 * Debounce function
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// ============================================================================
// LISTENERS GLOBAIS
// ============================================================================
function initGlobalListeners() {
    // Botao instalar PWA
    document.addEventListener('click', function(e) {
        if (e.target.matches('#btn-install-pwa, #btn-install-pwa *')) {
            installPWA();
        }

        if (e.target.matches('#btn-close-install, #btn-close-install *')) {
            hideInstallBanner();
        }

        if (e.target.matches('#btn-enable-notifications, #btn-enable-notifications *')) {
            requestNotificationPermission();
        }
    });

    // Filtro de busca com debounce
    const searchInput = document.querySelector('.lp-search-input');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(function(e) {
            apex.submit({ request: 'SEARCH' });
        }, 500));
    }

    // Online/Offline status
    window.addEventListener('online', () => {
        showToast('Conexao restaurada!', 'success');
    });

    window.addEventListener('offline', () => {
        showToast('Voce esta offline. Algumas funcoes podem nao estar disponiveis.', 'warning');
    });
}

// ============================================================================
// TOAST NOTIFICATIONS
// ============================================================================
function showToast(message, type = 'info') {
    // Usar APEX message se disponivel
    if (typeof apex !== 'undefined' && apex.message) {
        apex.message.showPageSuccess(message);
    } else {
        // Fallback simples
        alert(message);
    }
}

// ============================================================================
// COMPARTILHAR LISTA
// ============================================================================
async function shareList() {
    if (!navigator.share) {
        // Fallback para copiar link
        const url = window.location.href;
        await navigator.clipboard.writeText(url);
        showToast('Link copiado para a area de transferencia!', 'success');
        return;
    }

    try {
        await navigator.share({
            title: 'Minha Lista de Presentes',
            text: 'Confira minha lista de presentes!',
            url: window.location.href
        });
    } catch (error) {
        if (error.name !== 'AbortError') {
            console.error('[LP] Erro ao compartilhar:', error);
        }
    }
}

// ============================================================================
// PREVIEW DE IMAGEM
// ============================================================================
function previewImage(input, previewId) {
    const preview = document.getElementById(previewId);
    if (!preview) return;

    if (input.files && input.files[0]) {
        const reader = new FileReader();

        reader.onload = function(e) {
            preview.src = e.target.result;
            preview.style.display = 'block';
        };

        reader.readAsDataURL(input.files[0]);
    }
}

// ============================================================================
// CONFIRMACAO DE ACAO
// ============================================================================
function confirmAction(message, callback) {
    if (typeof apex !== 'undefined' && apex.message && apex.message.confirm) {
        apex.message.confirm(message, function(okPressed) {
            if (okPressed) {
                callback();
            }
        });
    } else if (confirm(message)) {
        callback();
    }
}

// ============================================================================
// EXPORTAR FUNCOES GLOBAIS
// ============================================================================
window.LP = {
    installPWA,
    requestNotificationPermission,
    formatCurrency,
    formatRelativeTime,
    shareList,
    previewImage,
    confirmAction,
    showToast
};

console.log('[LP] JavaScript carregado!');
