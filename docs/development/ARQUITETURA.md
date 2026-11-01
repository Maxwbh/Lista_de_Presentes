# 🏗️ Arquitetura

Visão geral de como a **Lista de Presentes** está organizada. Para instalar e rodar, veja o [guia de instalação](INSTALACAO.md).

## Visão geral

```
Navegador / PWA (Tailwind + daisyUI, service worker, Web Push)
        │
        ▼
Render (gunicorn + WhiteNoise)  ◄──  GitHub Actions (keep-alive, pesquisa de preços, relatório de acessos)
        │
        ▼
Django 5.1 (app "presentes")
   ├─ PostgreSQL (Supabase, schema lista_presentes) ou SQLite em desenvolvimento
   ├─ Lojas: páginas dos produtos e API do Mercado Livre (leitura de título, preço e foto)
   ├─ Brevo (e-mail por HTTP)
   ├─ Web Push (VAPID)
   ├─ GitHub (issues automáticas de falha de leitura)
   └─ Serviços de IA (sugestões de onde comprar)
```

- **Um único app Django** (`presentes`) concentra modelos, telas e integrações. O projeto (`lista_presentes`) guarda configurações e rotas principais.
- **Sem fila de tarefas:** tarefas demoradas (pesquisa de preços, busca de imagens em lote, envio de e-mail) rodam em *threads* em segundo plano dentro do próprio processo web. Por isso o servidor precisa estar acordado; no Render Free ele dorme após 15 minutos sem acesso.
- **Imagens no banco:** fotos de presentes, grupos e usuários são guardadas em base64 no banco (o disco do Render Free é apagado a cada deploy) e servidas pelas próprias rotas do app.

## Módulos principais (`presentes/`)

| Arquivo | Responsabilidade |
|---|---|
| `models.py` | Modelos de dados (abaixo) |
| `views.py`, `urls.py`, `forms.py` | Telas, rotas e formulários |
| `scrapers.py` | Leitura de produtos por link: Amazon, Mercado Livre, Kabum, Decathlon e leitor genérico; log da extração e issues automáticas |
| `mercadolivre_api.py` | API oficial do Mercado Livre (token, anúncios, catálogo) |
| `precos.py` | Conversão de preços (`converter_preco`), com detecção do separador decimal |
| `services.py` | Sugestões de compra com IA, busca de preços (Zoom, Buscapé) e busca de imagem pelo link original |
| `pesquisa_precos.py` | Pesquisa semanal de preços (endpoint de cron e middleware de reserva) |
| `acessos.py` | Registro de despertares do servidor e acessos por hora; resumo para revisar o keep-alive |
| `github_helper.py` | Criação de issues automáticas, sem duplicar (comentário de nova ocorrência) |
| `emails.py`, `email_backend.py` | E-mails (boas-vindas, senha, presente comprado) e envio pela API da Brevo |
| `push.py` | Notificações Web Push |
| `senha.py` | Links de redefinição de senha |
| `admin.py` | Admin do Django, incluindo a busca de imagens que faltam |
| `management/commands/` | Comandos de manutenção (abaixo) |

## Modelos de dados

| Modelo | O que guarda |
|---|---|
| `Usuario` | Usuário (e-mail como login), grupo ativo e foto |
| `Grupo`, `GrupoMembro` | Grupos, código de convite, membros e mantenedores |
| `Presente` | Item da lista: descrição, link, preço, status (ativo/comprado), imagem e resultado da última busca de imagem |
| `Compra` | Quem comprou qual presente (não é mostrado ao dono da lista) |
| `SugestaoCompra` | Lojas e preços sugeridos para um presente |
| `PrecoHistorico`, `PesquisaPrecoLog` | Histórico de preços (gráfico e temperatura) e execuções da pesquisa semanal |
| `Notificacao`, `PushSubscription` | Notificações no site e inscrições de Web Push |
| `MercadoLivreToken` | Token OAuth da API do Mercado Livre |
| `DespertarServidor`, `AcessoHora` | Quando o servidor acordou e quantos acessos houve por hora |

Todos os dados de presentes, compras, sugestões e notificações são filtrados pelo **grupo ativo** do usuário.

## Endpoints internos (API)

Usados pelo próprio front-end e pelos workflows. Não há API pública versionada.

| Método | Rota | Uso | Acesso |
|---|---|---|---|
| POST | `/api/extrair-info-produto/` | Lê título, preço e foto de um link de produto | Usuário logado |
| GET | `/api/notificacoes/` | Notificações não lidas (sino do topo) | Usuário logado |
| GET | `/api/compras/` | Compras do grupo ativo (`?tipo=minhas` para as suas) | Usuário logado |
| GET | `/api/push/vapid-key/` | Chave pública VAPID | Público |
| POST | `/api/push/subscribe/`, `/api/push/unsubscribe/` | Inscrição de Web Push | Usuário logado |
| POST | `/api/cron/pesquisar-precos/` | Dispara a pesquisa semanal de preços | Header `X-Cron-Token` |
| GET | `/api/acessos/resumo/` | Resumo de acessos por hora e despertares (`?dias=`, `?limite=`) | Superusuário ou header `X-Cron-Token` |
| GET | `/health/` | Verificação de saúde (keep-alive e Render) | Público |

O `CRON_TOKEN` precisa ter o mesmo valor no Render e no secret do GitHub. Detalhes em [KEEP_ALIVE.md](../features/KEEP_ALIVE.md).

## Tarefas agendadas (GitHub Actions)

| Workflow | Quando | O que faz |
|---|---|---|
| `tests.yml` | Push e pull request | Testes (Python 3.11 e 3.12), lint e segurança |
| `keep-alive.yml` | Nas horas de uso, a cada 14 min | Ping em `/health/` para o servidor não dormir |
| `pesquisa-precos.yml` | Segunda-feira, 08:00 UTC | Chama `/api/cron/pesquisar-precos/` |
| `relatorio-acessos.yml` | Sob demanda | Busca o resumo de acessos para revisar as horas do keep-alive |

## Comandos de manutenção

| Comando | Uso |
|---|---|
| `populate_test_data` | Cria dados de exemplo (usuários com senha `senha123`) |
| `pesquisar_precos` | Roda a pesquisa de preços manualmente |
| `analisar_acessos` | Mostra o resumo de acessos no terminal |
| `limpar_historico_precos` | Limpa o histórico de preços |
| `gerar_chaves_vapid`, `testar_push` | Gera as chaves de Web Push e envia um push de teste |
| `validar_social` | Confere a configuração do login social |
| `fix_admin` | Cria ou atualiza o superusuário a partir das variáveis de ambiente |
| `criar_grupo_padrao`, `migrar_dados_para_grupo` | Legado: grupo padrão e migração de dados antigos para grupos |
| `migrate_images_to_base64`, `fix_migration_history`, `force_migrate` | Manutenção de imagens e migrações |

## Front-end

- Templates Django em `templates/`, com o layout base em `templates/base.html`.
- CSS com Tailwind 3 e daisyUI 4, compilado de `theme/static_src/` para `theme/static/css/dist/styles.css`. Tema padrão: `emerald_light`.
- PWA: `static/manifest.json` (inclui *share target* para compartilhar do celular para a lista) e `static/sw.js` (service worker, rede primeiro e cache de reserva).
- Arquivos estáticos servidos pelo WhiteNoise com nomes versionados (hash) a cada deploy.
