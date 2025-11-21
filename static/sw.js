// Service Worker para Lista de Presentes
// Versão do cache - incrementar ao fazer mudanças
const CACHE_VERSION = 'v1.0.0';
const CACHE_NAME = `lista-presentes-${CACHE_VERSION}`;

// Arquivos essenciais para cache offline
const urlsToCache = [
  '/',
  '/static/manifest.json',
  '/static/icons/icon-192x192.svg',
  '/static/icons/icon-512x512.svg',
];

// Evento de instalação do Service Worker
self.addEventListener('install', (event) => {
  console.log('[ServiceWorker] Instalando...');

  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('[ServiceWorker] Armazenando arquivos em cache');
        return cache.addAll(urlsToCache);
      })
      .then(() => {
        console.log('[ServiceWorker] Instalação completa');
        return self.skipWaiting();
      })
      .catch((error) => {
        console.error('[ServiceWorker] Erro durante instalação:', error);
      })
  );
});

// Evento de ativação do Service Worker
self.addEventListener('activate', (event) => {
  console.log('[ServiceWorker] Ativando...');

  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            // Remover caches antigos
            if (cacheName !== CACHE_NAME) {
              console.log('[ServiceWorker] Removendo cache antigo:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        console.log('[ServiceWorker] Ativação completa');
        return self.clients.claim();
      })
  );
});

// Estratégia de cache: Network First, fallback para cache
self.addEventListener('fetch', (event) => {
  const { request } = event;

  // Ignorar requisições que não sejam HTTP/HTTPS
  if (!request.url.startsWith('http')) {
    return;
  }

  // Estratégia: tentar rede primeiro, fallback para cache
  event.respondWith(
    fetch(request)
      .then((response) => {
        // Clonar a resposta porque pode ser usada apenas uma vez
        const responseToCache = response.clone();

        // Armazenar no cache apenas GET requests bem-sucedidas
        if (request.method === 'GET' && response.status === 200) {
          caches.open(CACHE_NAME)
            .then((cache) => {
              cache.put(request, responseToCache);
            });
        }

        return response;
      })
      .catch(() => {
        // Se falhar (offline), tentar buscar do cache
        return caches.match(request)
          .then((cachedResponse) => {
            if (cachedResponse) {
              console.log('[ServiceWorker] Servindo do cache:', request.url);
              return cachedResponse;
            }

            // Se não houver no cache, retornar página offline
            return caches.match('/')
              .then((offlineResponse) => {
                return offlineResponse || new Response('Offline - Você está sem conexão.', {
                  status: 503,
                  statusText: 'Service Unavailable',
                  headers: new Headers({
                    'Content-Type': 'text/html'
                  })
                });
              });
          });
      })
  );
});

// Mensagens do Service Worker
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }

  if (event.data && event.data.type === 'CACHE_URLS') {
    event.waitUntil(
      caches.open(CACHE_NAME)
        .then((cache) => cache.addAll(event.data.payload))
    );
  }
});

// Log de erros
self.addEventListener('error', (event) => {
  console.error('[ServiceWorker] Erro:', event.error);
});

// Log de rejeição de promises
self.addEventListener('unhandledrejection', (event) => {
  console.error('[ServiceWorker] Promise rejeitada:', event.reason);
});

console.log('[ServiceWorker] Service Worker carregado');
