/**
 * Service Worker - Lista de Presentes PWA
 * Oracle APEX 24
 *
 * Desenvolvedor: Maxwell da Silva Oliveira (@maxwbh)
 * Email: maxwbh@gmail.com
 * Empresa: M&S do Brasil LTDA - msbrasil.inf.br
 */

const CACHE_NAME = 'lista-presentes-v1';
const OFFLINE_URL = '/ords/f?p=LISTA_PRESENTES:OFFLINE';

// Recursos para cache inicial
const PRECACHE_URLS = [
    '/',
    '/ords/f?p=LISTA_PRESENTES:1',
    '/i/apex_ui/css/Core.min.css',
    '/i/apex_ui/js/minified/apex_core.min.js',
    '/i/app_icons/gift-192.png',
    '/i/app_icons/gift-512.png'
];

// ============================================================================
// INSTALACAO DO SERVICE WORKER
// ============================================================================
self.addEventListener('install', event => {
    console.log('[SW] Instalando Service Worker...');

    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('[SW] Cache aberto, adicionando recursos...');
                return cache.addAll(PRECACHE_URLS);
            })
            .then(() => {
                console.log('[SW] Recursos em cache!');
                return self.skipWaiting();
            })
            .catch(error => {
                console.error('[SW] Erro ao fazer cache:', error);
            })
    );
});

// ============================================================================
// ATIVACAO DO SERVICE WORKER
// ============================================================================
self.addEventListener('activate', event => {
    console.log('[SW] Ativando Service Worker...');

    event.waitUntil(
        caches.keys()
            .then(cacheNames => {
                return Promise.all(
                    cacheNames.map(cacheName => {
                        if (cacheName !== CACHE_NAME) {
                            console.log('[SW] Removendo cache antigo:', cacheName);
                            return caches.delete(cacheName);
                        }
                    })
                );
            })
            .then(() => {
                console.log('[SW] Service Worker ativado!');
                return self.clients.claim();
            })
    );
});

// ============================================================================
// INTERCEPTACAO DE REQUISICOES (FETCH)
// ============================================================================
self.addEventListener('fetch', event => {
    const request = event.request;

    // Ignorar requisicoes que nao sao GET
    if (request.method !== 'GET') {
        return;
    }

    // Ignorar requisicoes de APIs (deixar passar direto)
    if (request.url.includes('/apex_util.') ||
        request.url.includes('wwv_flow.ajax')) {
        return;
    }

    event.respondWith(
        caches.match(request)
            .then(cachedResponse => {
                if (cachedResponse) {
                    // Retornar do cache
                    return cachedResponse;
                }

                // Buscar da rede
                return fetch(request)
                    .then(response => {
                        // Verificar se resposta e valida
                        if (!response || response.status !== 200 || response.type !== 'basic') {
                            return response;
                        }

                        // Clonar resposta (stream so pode ser lido uma vez)
                        const responseToCache = response.clone();

                        // Adicionar ao cache (apenas recursos estaticos)
                        if (shouldCache(request.url)) {
                            caches.open(CACHE_NAME)
                                .then(cache => {
                                    cache.put(request, responseToCache);
                                });
                        }

                        return response;
                    })
                    .catch(() => {
                        // Offline - retornar pagina offline para navegacao
                        if (request.mode === 'navigate') {
                            return caches.match(OFFLINE_URL);
                        }
                    });
            })
    );
});

// ============================================================================
// PUSH NOTIFICATIONS
// ============================================================================
self.addEventListener('push', event => {
    console.log('[SW] Push recebido:', event);

    let data = {
        title: 'Lista de Presentes',
        body: 'Voce tem uma nova notificacao!',
        icon: '/i/app_icons/gift-192.png',
        badge: '/i/app_icons/gift-72.png',
        tag: 'lista-presentes',
        requireInteraction: true,
        actions: [
            { action: 'ver', title: 'Ver' },
            { action: 'fechar', title: 'Fechar' }
        ]
    };

    if (event.data) {
        try {
            const pushData = event.data.json();
            data = { ...data, ...pushData };
        } catch (e) {
            data.body = event.data.text();
        }
    }

    event.waitUntil(
        self.registration.showNotification(data.title, {
            body: data.body,
            icon: data.icon,
            badge: data.badge,
            tag: data.tag,
            requireInteraction: data.requireInteraction,
            actions: data.actions,
            data: data.url || '/ords/f?p=LISTA_PRESENTES:30'
        })
    );
});

// ============================================================================
// CLICK NA NOTIFICACAO
// ============================================================================
self.addEventListener('notificationclick', event => {
    console.log('[SW] Notificacao clicada:', event);

    event.notification.close();

    const action = event.action;
    const url = event.notification.data || '/ords/f?p=LISTA_PRESENTES:30';

    if (action === 'fechar') {
        return;
    }

    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true })
            .then(clientList => {
                // Verificar se ja existe uma janela aberta
                for (const client of clientList) {
                    if (client.url.includes('LISTA_PRESENTES') && 'focus' in client) {
                        client.navigate(url);
                        return client.focus();
                    }
                }
                // Abrir nova janela
                if (clients.openWindow) {
                    return clients.openWindow(url);
                }
            })
    );
});

// ============================================================================
// SINCRONIZACAO EM BACKGROUND
// ============================================================================
self.addEventListener('sync', event => {
    console.log('[SW] Sync event:', event.tag);

    if (event.tag === 'sync-presentes') {
        event.waitUntil(syncPresentes());
    }
});

async function syncPresentes() {
    // Implementar logica de sincronizacao offline
    console.log('[SW] Sincronizando presentes...');
}

// ============================================================================
// FUNCOES AUXILIARES
// ============================================================================

/**
 * Verifica se URL deve ser cacheada
 */
function shouldCache(url) {
    const cacheableExtensions = ['.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.woff', '.woff2'];
    return cacheableExtensions.some(ext => url.includes(ext));
}

/**
 * Limpar caches antigos
 */
async function clearOldCaches() {
    const cacheNames = await caches.keys();
    return Promise.all(
        cacheNames
            .filter(name => name !== CACHE_NAME)
            .map(name => caches.delete(name))
    );
}

// ============================================================================
// LOG DE MENSAGENS
// ============================================================================
self.addEventListener('message', event => {
    console.log('[SW] Mensagem recebida:', event.data);

    if (event.data.action === 'skipWaiting') {
        self.skipWaiting();
    }
});

console.log('[SW] Service Worker carregado!');
