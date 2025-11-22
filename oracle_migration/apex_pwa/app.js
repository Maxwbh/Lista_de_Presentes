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
// Carregadas dinamicamente do servidor para maior seguranca
// ============================================================================
let LP_CONFIG = {
    appId: 'LISTA_PRESENTES',
    swPath: '/pwa/service-worker.js',
    vapidPublicKey: null,
    apiEndpoint: '/ords/api/v1/',
    loaded: false
};

/**
 * Carrega configuracoes do servidor
 * VAPID key e outras configs sensiveis vem do backend
 */
async function loadConfig() {
    if (LP_CONFIG.loaded) return LP_CONFIG;

    try {
        // Tentar carregar via APEX process
        if (typeof apex !== 'undefined' && apex.server) {
            const response = await apex.server.process('GET_PWA_CONFIG', {});
            if (response && response.vapidPublicKey) {
                LP_CONFIG.vapidPublicKey = response.vapidPublicKey;
                LP_CONFIG.loaded = true;
                console.log('[LP] Configuracoes carregadas do servidor');
            }
        }

        // Fallback: tentar carregar de meta tag (configurada no APEX)
        if (!LP_CONFIG.vapidPublicKey) {
            const metaVapid = document.querySelector('meta[name="vapid-public-key"]');
            if (metaVapid && metaVapid.content) {
                LP_CONFIG.vapidPublicKey = metaVapid.content;
                LP_CONFIG.loaded = true;
                console.log('[LP] VAPID key carregada de meta tag');
            }
        }

    } catch (error) {
        console.warn('[LP] Erro ao carregar config:', error);
    }

    return LP_CONFIG;
}

// ============================================================================
// INICIALIZACAO
// ============================================================================
document.addEventListener('DOMContentLoaded', async function() {
    console.log('[LP] Aplicacao iniciada');

    // Carregar configuracoes do servidor primeiro
    await loadConfig();

    // Inicializar tema (dark mode)
    initTheme();

    // Registrar Service Worker
    registerServiceWorker();

    // Verificar instalacao PWA
    checkPWAInstall();

    // Inicializar notificacoes (apenas se config carregada)
    if (LP_CONFIG.vapidPublicKey) {
        initPushNotifications();
    } else {
        console.warn('[LP] Push notifications desabilitadas - VAPID key nao configurada');
    }

    // Inicializar componentes de UI
    initFAB();
    initBottomNav();

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
        // Verificar se VAPID key esta disponivel
        if (!LP_CONFIG.vapidPublicKey) {
            console.warn('[LP] VAPID key nao disponivel, tentando carregar...');
            await loadConfig();
            if (!LP_CONFIG.vapidPublicKey) {
                console.error('[LP] Nao foi possivel obter VAPID key');
                return;
            }
        }

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
// DARK MODE / THEME
// ============================================================================
function initTheme() {
    // Verificar preferencia salva ou do sistema
    const savedTheme = localStorage.getItem('lp-theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

    if (savedTheme) {
        setTheme(savedTheme);
    } else if (prefersDark) {
        setTheme('dark');
    }

    // Escutar mudancas de preferencia do sistema
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        if (!localStorage.getItem('lp-theme')) {
            setTheme(e.matches ? 'dark' : 'light');
        }
    });
}

function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('lp-theme', theme);

    // Atualizar botao de toggle se existir
    const toggleBtn = document.querySelector('.lp-theme-toggle');
    if (toggleBtn) {
        toggleBtn.classList.toggle('dark', theme === 'dark');
    }

    console.log('[LP] Tema alterado para:', theme);
}

function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme') || 'light';
    setTheme(current === 'dark' ? 'light' : 'dark');
}

// ============================================================================
// FLOATING ACTION BUTTON (FAB)
// ============================================================================
function initFAB() {
    const fab = document.querySelector('.lp-fab');
    const fabMenu = document.querySelector('.lp-fab-menu');

    if (fab && fabMenu) {
        fab.addEventListener('click', () => {
            fab.classList.toggle('open');
            fabMenu.classList.toggle('show');
        });

        // Fechar ao clicar fora
        document.addEventListener('click', (e) => {
            if (!fab.contains(e.target) && !fabMenu.contains(e.target)) {
                fab.classList.remove('open');
                fabMenu.classList.remove('show');
            }
        });
    }
}

// ============================================================================
// BOTTOM NAVIGATION
// ============================================================================
function initBottomNav() {
    const navItems = document.querySelectorAll('.lp-bottom-nav-item');
    const currentPage = window.location.pathname;

    navItems.forEach(item => {
        const href = item.getAttribute('href') || '';
        if (href && currentPage.includes(href.split(':')[1])) {
            item.classList.add('active');
        }
    });
}

// ============================================================================
// TOAST NOTIFICATIONS (melhorado)
// ============================================================================
function createToast(message, type = 'info', duration = 5000) {
    // Criar container se nao existir
    let container = document.querySelector('.lp-toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'lp-toast-container';
        container.setAttribute('role', 'alert');
        container.setAttribute('aria-live', 'polite');
        document.body.appendChild(container);
    }

    // Criar toast
    const toast = document.createElement('div');
    toast.className = `lp-toast ${type}`;
    toast.innerHTML = `
        <span class="lp-toast-message">${message}</span>
        <button class="lp-toast-close" aria-label="Fechar">
            <span class="fa fa-times"></span>
        </button>
    `;

    // Evento de fechar
    toast.querySelector('.lp-toast-close').addEventListener('click', () => {
        removeToast(toast);
    });

    container.appendChild(toast);

    // Auto-remover apos duracao
    if (duration > 0) {
        setTimeout(() => removeToast(toast), duration);
    }

    return toast;
}

function removeToast(toast) {
    toast.style.animation = 'slideInRight 0.3s ease reverse';
    setTimeout(() => toast.remove(), 300);
}

// ============================================================================
// SKELETON LOADING
// ============================================================================
function showSkeleton(container, count = 3) {
    const skeletonHTML = `
        <div class="lp-skeleton-card">
            <div class="lp-skeleton lp-skeleton-image"></div>
            <div class="lp-card-body">
                <div class="lp-skeleton lp-skeleton-title"></div>
                <div class="lp-skeleton lp-skeleton-text"></div>
                <div class="lp-skeleton lp-skeleton-text-sm"></div>
            </div>
        </div>
    `;

    container.innerHTML = Array(count).fill(skeletonHTML).join('');
}

function hideSkeleton(container) {
    const skeletons = container.querySelectorAll('.lp-skeleton-card');
    skeletons.forEach(s => s.remove());
}

// ============================================================================
// CONFETTI EFFECT
// ============================================================================
function showConfetti() {
    const container = document.createElement('div');
    container.className = 'lp-confetti';
    document.body.appendChild(container);

    const colors = ['#0572ce', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

    for (let i = 0; i < 50; i++) {
        const piece = document.createElement('div');
        piece.className = 'lp-confetti-piece';
        piece.style.left = Math.random() * 100 + 'vw';
        piece.style.background = colors[Math.floor(Math.random() * colors.length)];
        piece.style.animationDelay = Math.random() * 2 + 's';
        piece.style.transform = `rotate(${Math.random() * 360}deg)`;
        container.appendChild(piece);
    }

    // Remover apos animacao
    setTimeout(() => container.remove(), 4000);
}

// ============================================================================
// ACESSIBILIDADE
// ============================================================================
function announceToScreenReader(message) {
    const announcement = document.createElement('div');
    announcement.setAttribute('role', 'status');
    announcement.setAttribute('aria-live', 'polite');
    announcement.className = 'lp-sr-only';
    announcement.textContent = message;
    document.body.appendChild(announcement);

    setTimeout(() => announcement.remove(), 1000);
}

// ============================================================================
// PULL TO REFRESH (Mobile)
// ============================================================================
let touchStartY = 0;
let touchEndY = 0;

function initPullToRefresh() {
    document.addEventListener('touchstart', (e) => {
        touchStartY = e.touches[0].clientY;
    }, { passive: true });

    document.addEventListener('touchend', (e) => {
        touchEndY = e.changedTouches[0].clientY;
        handlePullToRefresh();
    }, { passive: true });
}

function handlePullToRefresh() {
    const scrollTop = window.scrollY || document.documentElement.scrollTop;
    const pullDistance = touchEndY - touchStartY;

    if (scrollTop === 0 && pullDistance > 100) {
        const indicator = document.querySelector('.lp-pull-to-refresh');
        if (indicator) {
            indicator.classList.add('show');
            setTimeout(() => {
                window.location.reload();
            }, 500);
        } else {
            window.location.reload();
        }
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
    showToast,
    // Novas funcoes
    toggleTheme,
    setTheme,
    createToast,
    showSkeleton,
    hideSkeleton,
    showConfetti,
    announceToScreenReader
};

console.log('[LP] JavaScript carregado - v2.0');
