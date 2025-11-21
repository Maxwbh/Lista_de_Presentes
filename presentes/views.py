from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Usuario, Presente, Compra, Notificacao, SugestaoCompra
from .forms import UsuarioRegistroForm, PresenteForm, LoginForm
from .services import IAService
import base64
import logging

logger = logging.getLogger(__name__)

def converter_imagem_para_base64(imagem_file):
    """Converte um arquivo de imagem para base64"""
    try:
        # Ler o conteúdo do arquivo
        imagem_data = imagem_file.read()

        # Converter para base64
        imagem_base64 = base64.b64encode(imagem_data).decode('utf-8')

        # Obter o tipo MIME
        content_type = imagem_file.content_type

        # Obter o nome do arquivo
        nome_arquivo = imagem_file.name

        return imagem_base64, nome_arquivo, content_type
    except Exception as e:
        logger.error(f"Erro ao converter imagem para base64: {str(e)}")
        return None, None, None

def health_check(request):
    """Health check endpoint para Render.com e outros serviços"""
    return HttpResponse("OK", status=200)

def registro_view(request):
    if request.method == 'POST':
        form = UsuarioRegistroForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            login(request, usuario)
            messages.success(request, 'Cadastro realizado com sucesso!')
            return redirect('dashboard')
    else:
        form = UsuarioRegistroForm()
    return render(request, 'presentes/registro.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            usuario = authenticate(request, username=email, password=password)
            if usuario:
                login(request, usuario)
                return redirect('dashboard')
            else:
                messages.error(request, 'Email ou senha inválidos')
    else:
        form = LoginForm()
    return render(request, 'presentes/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard_view(request):
    # Total de usuários
    total_usuarios = Usuario.objects.filter(ativo=True).count()
    
    # Meus presentes ativos
    meus_presentes_ativos = Presente.objects.filter(
        usuario=request.user,
        status='ATIVO'
    ).count()
    
    # Total de presentes não comprados (todos os usuários)
    presentes_nao_comprados = Presente.objects.filter(status='ATIVO').count()
    
    # Notificações não lidas
    notificacoes_nao_lidas = Notificacao.objects.filter(
        usuario=request.user,
        lida=False
    ).count()
    
    context = {
        'total_usuarios': total_usuarios,
        'meus_presentes_ativos': meus_presentes_ativos,
        'presentes_nao_comprados': presentes_nao_comprados,
        'notificacoes_nao_lidas': notificacoes_nao_lidas,
    }
    return render(request, 'presentes/dashboard.html', context)

@login_required
def meus_presentes_view(request):
    # Otimizar query com select_related para evitar N+1
    presentes_list = Presente.objects.filter(usuario=request.user).select_related('usuario').prefetch_related('sugestoes')

    # Estatísticas
    total_presentes = presentes_list.count()
    presentes_ativos = presentes_list.filter(status='ATIVO').count()
    presentes_comprados = presentes_list.filter(status='COMPRADO').count()

    # Paginação (20 presentes por página)
    paginator = Paginator(presentes_list, 20)
    page = request.GET.get('page', 1)

    try:
        presentes = paginator.page(page)
    except PageNotAnInteger:
        presentes = paginator.page(1)
    except EmptyPage:
        presentes = paginator.page(paginator.num_pages)

    context = {
        'presentes': presentes,
        'total_presentes': total_presentes,
        'presentes_ativos': presentes_ativos,
        'presentes_comprados': presentes_comprados,
    }

    return render(request, 'presentes/meus_presentes.html', context)

@login_required
def adicionar_presente_view(request):
    if request.method == 'POST':
        form = PresenteForm(request.POST, request.FILES)
        if form.is_valid():
            presente = form.save(commit=False)
            presente.usuario = request.user

            # Converter imagem para base64 se foi enviada
            if 'imagem' in request.FILES:
                imagem_file = request.FILES['imagem']
                imagem_base64, nome_arquivo, content_type = converter_imagem_para_base64(imagem_file)

                if imagem_base64:
                    presente.imagem_base64 = imagem_base64
                    presente.imagem_nome = nome_arquivo
                    presente.imagem_tipo = content_type
                    # Limpar o campo antigo para economizar espaço
                    presente.imagem = None
                    logger.info(f"Imagem convertida para base64: {nome_arquivo}")

            presente.save()

            # Buscar preços REAIS automaticamente (Zoom + Buscapé)
            try:
                logger.info(f"Buscando preços reais para presente {presente.id}")

                # Buscar preços reais no Zoom e Buscapé
                sucesso, mensagem = IAService.buscar_sugestoes_reais(presente)

                if sucesso:
                    messages.success(request, f'Presente adicionado! {mensagem}')
                else:
                    messages.success(request, 'Presente adicionado com sucesso!')
                    messages.info(request, f'Preços: {mensagem}')

            except Exception as e:
                logger.error(f"Erro ao buscar preços reais: {str(e)}")
                messages.success(request, 'Presente adicionado com sucesso!')
                messages.warning(request, 'Não foi possível buscar preços automaticamente.')

            return redirect('meus_presentes')
    else:
        form = PresenteForm()
    return render(request, 'presentes/adicionar_presente.html', {'form': form})

@login_required
def editar_presente_view(request, pk):
    presente = get_object_or_404(Presente, pk=pk, usuario=request.user)
    if request.method == 'POST':
        form = PresenteForm(request.POST, request.FILES, instance=presente)
        if form.is_valid():
            presente = form.save(commit=False)

            # Converter imagem para base64 se foi enviada uma nova
            if 'imagem' in request.FILES:
                imagem_file = request.FILES['imagem']
                imagem_base64, nome_arquivo, content_type = converter_imagem_para_base64(imagem_file)

                if imagem_base64:
                    presente.imagem_base64 = imagem_base64
                    presente.imagem_nome = nome_arquivo
                    presente.imagem_tipo = content_type
                    # Limpar o campo antigo para economizar espaço
                    presente.imagem = None
                    logger.info(f"Imagem atualizada e convertida para base64: {nome_arquivo}")

            presente.save()
            messages.success(request, 'Presente atualizado com sucesso!')
            return redirect('meus_presentes')
    else:
        form = PresenteForm(instance=presente)
    return render(request, 'presentes/editar_presente.html', {'form': form, 'presente': presente})

@login_required
def deletar_presente_view(request, pk):
    presente = get_object_or_404(Presente, pk=pk, usuario=request.user)
    if request.method == 'POST':
        presente.delete()
        messages.success(request, 'Presente excluído com sucesso!')
        return redirect('meus_presentes')
    return render(request, 'presentes/deletar_presente.html', {'presente': presente})

def servir_imagem_view(request, pk):
    """Serve imagem armazenada em base64 no banco de dados"""
    presente = get_object_or_404(Presente, pk=pk)

    if not presente.imagem_base64:
        # Se não há imagem base64, retornar 404
        return HttpResponse('Imagem não encontrada', status=404)

    try:
        # Decodificar base64
        imagem_data = base64.b64decode(presente.imagem_base64)

        # Determinar content type (padrão image/jpeg se não especificado)
        content_type = presente.imagem_tipo or 'image/jpeg'

        # Retornar a imagem
        return HttpResponse(imagem_data, content_type=content_type)
    except Exception as e:
        logger.error(f"Erro ao servir imagem do presente {pk}: {str(e)}")
        return HttpResponse('Erro ao carregar imagem', status=500)

@login_required
def buscar_sugestoes_ia_view(request, pk):
    presente = get_object_or_404(Presente, pk=pk, usuario=request.user)

    # Escolher qual IA usar (pode ser configurável)
    ia_escolhida = request.GET.get('ia', 'claude')  # claude, chatgpt, gemini

    try:
        if ia_escolhida == 'claude':
            sucesso, mensagem = IAService.buscar_sugestoes_claude(presente)
        elif ia_escolhida == 'chatgpt':
            sucesso, mensagem = IAService.buscar_sugestoes_chatgpt(presente)
        elif ia_escolhida == 'gemini':
            sucesso, mensagem = IAService.buscar_sugestoes_gemini(presente)
        else:
            sucesso, mensagem = False, "IA não reconhecida"

        if sucesso:
            messages.success(request, mensagem)
        else:
            messages.warning(request, f"Não foi possível buscar sugestões: {mensagem}")

    except Exception as e:
        # Capturar qualquer erro da IA para não quebrar a aplicação
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erro ao buscar sugestões com {ia_escolhida}: {str(e)}")
        messages.warning(request, f"Não foi possível buscar sugestões com {ia_escolhida}. Tente novamente mais tarde ou use outra IA.")

    return redirect('ver_sugestoes', pk=pk)

@login_required
def ver_sugestoes_view(request, pk):
    # Otimizar query com select_related
    presente = get_object_or_404(Presente.objects.select_related('usuario'), pk=pk, usuario=request.user)

    # Sugestões já vem ordenadas por preço (definido no model)
    sugestoes = SugestaoCompra.objects.filter(presente=presente).select_related('presente')

    # Debug: Log das sugestões carregadas
    logger.info(f"Ver sugestões para presente {pk}: {sugestoes.count()} sugestões encontradas")
    for sug in sugestoes:
        loja = sug.local_compra or '(vazio)'
        preco = sug.preco_sugerido if sug.preco_sugerido else '(sem preço)'
        url = sug.url_compra or '(vazio)'
        logger.info(f"  - Loja: '{loja}', Preço: {preco}, URL: '{url}'")

    return render(request, 'presentes/ver_sugestoes.html', {
        'presente': presente,
        'sugestoes': sugestoes
    })

def _atualizar_precos_background():
    """Função para atualizar preços em background"""
    try:
        # Buscar TODOS os presentes ativos de TODOS os usuários
        presentes = Presente.objects.filter(status='ATIVO').select_related('usuario')

        total_presentes = presentes.count()
        sucesso_count = 0
        erro_count = 0

        logger.info(f"[BACKGROUND] Iniciando atualização de preços para {total_presentes} presentes ativos do sistema")

        for presente in presentes:
            try:
                sucesso, mensagem = IAService.buscar_sugestoes_reais(presente)
                if sucesso:
                    sucesso_count += 1
                    logger.info(f"[BACKGROUND] Presente {presente.id} ({presente.usuario.first_name}): {mensagem}")
                else:
                    erro_count += 1
                    logger.warning(f"[BACKGROUND] Presente {presente.id}: {mensagem}")
            except Exception as e:
                erro_count += 1
                logger.error(f"[BACKGROUND] Erro ao atualizar presente {presente.id}: {str(e)}")

        logger.info(f"[BACKGROUND] Atualização concluída: {sucesso_count} sucessos, {erro_count} erros de {total_presentes} presentes")

    except Exception as e:
        logger.error(f"[BACKGROUND] Erro fatal na atualização de preços: {str(e)}")
        import traceback
        logger.error(f"[BACKGROUND] Traceback: {traceback.format_exc()}")

@login_required
def atualizar_todos_precos_view(request):
    """Inicia atualização de preços de TODOS os presentes ativos em background"""
    if request.method == 'POST':
        # Verificar se usuário é admin (apenas admins podem atualizar todos)
        if not request.user.is_superuser:
            messages.error(request, 'Apenas administradores podem atualizar todos os preços do sistema.')
            return redirect('meus_presentes')

        # Contar quantos presentes serão atualizados
        total_presentes = Presente.objects.filter(status='ATIVO').count()

        if total_presentes == 0:
            messages.warning(request, 'Não há presentes ativos para atualizar.')
            return redirect('meus_presentes')

        logger.info(f"Usuário {request.user.email} iniciou atualização em background de {total_presentes} presentes")

        # Iniciar thread em background
        import threading
        thread = threading.Thread(target=_atualizar_precos_background, daemon=True)
        thread.start()

        # Mensagem de feedback imediato
        messages.success(
            request,
            f'✓ Atualização de preços iniciada em background para {total_presentes} presentes! '
            f'O processo continuará executando e você pode acompanhar o progresso nos logs. '
            f'As sugestões serão atualizadas automaticamente.'
        )
        messages.info(
            request,
            '💡 Dica: Aguarde alguns minutos e recarregue a página para ver as atualizações.'
        )

        return redirect('meus_presentes')

    # Se não for POST, redirecionar para meus presentes
    return redirect('meus_presentes')

@login_required
def lista_usuarios_view(request):
    # Otimizar query com prefetch_related para pegar presentes e sugestões
    usuarios_list = Usuario.objects.filter(ativo=True).exclude(id=request.user.id).prefetch_related(
        'presentes',
        'presentes__sugestoes'
    )

    # Adicionar estatísticas para cada usuário
    usuarios_com_stats = []
    for usuario in usuarios_list:
        usuario.total_presentes = usuario.presentes.count()
        usuario.presentes_ativos = usuario.presentes.filter(status='ATIVO').count()
        usuario.presentes_comprados = usuario.presentes.filter(status='COMPRADO').count()
        # Adicionar presentes com sugestões como atributo
        usuario.presentes_list = usuario.presentes.filter(status='ATIVO').order_by('-data_cadastro')[:6]
        usuarios_com_stats.append(usuario)

    # Buscar todos os presentes ativos de outros usuários (para visualização por produto)
    todos_presentes = Presente.objects.filter(
        usuario__ativo=True,
        status='ATIVO'
    ).exclude(
        usuario=request.user
    ).select_related('usuario').prefetch_related('sugestoes').order_by('-data_cadastro')

    # Paginação (20 usuários por página)
    paginator = Paginator(usuarios_com_stats, 20)
    page = request.GET.get('page', 1)

    try:
        usuarios = paginator.page(page)
    except PageNotAnInteger:
        usuarios = paginator.page(1)
    except EmptyPage:
        usuarios = paginator.page(paginator.num_pages)

    return render(request, 'presentes/lista_usuarios.html', {
        'usuarios': usuarios,
        'todos_presentes': todos_presentes,
    })

@login_required
def presentes_usuario_view(request, user_id):
    usuario = get_object_or_404(Usuario, pk=user_id)

    # Otimizar query com select_related e prefetch_related
    presentes_list = Presente.objects.filter(usuario=usuario).select_related('usuario').prefetch_related('sugestoes', 'compra')

    # Estatísticas
    total_presentes = presentes_list.count()
    presentes_ativos = presentes_list.filter(status='ATIVO').count()
    presentes_comprados = presentes_list.filter(status='COMPRADO').count()

    # Paginação (20 presentes por página)
    paginator = Paginator(presentes_list, 20)
    page = request.GET.get('page', 1)

    try:
        presentes = paginator.page(page)
    except PageNotAnInteger:
        presentes = paginator.page(1)
    except EmptyPage:
        presentes = paginator.page(paginator.num_pages)

    return render(request, 'presentes/presentes_usuario.html', {
        'usuario_presente': usuario,
        'presentes': presentes,
        'total_presentes': total_presentes,
        'presentes_ativos': presentes_ativos,
        'presentes_comprados': presentes_comprados,
    })

@login_required
@transaction.atomic
def marcar_comprado_view(request, pk):
    # Usar select_for_update para criar um lock no banco de dados
    # Isso previne race condition quando dois usuários tentam comprar o mesmo presente
    try:
        presente = Presente.objects.select_for_update().get(pk=pk)
    except Presente.DoesNotExist:
        messages.error(request, 'Presente não encontrado!')
        return redirect('lista_usuarios')

    # Não pode comprar seu próprio presente
    if presente.usuario == request.user:
        messages.error(request, 'Você não pode marcar seu próprio presente como comprado!')
        return redirect('presentes_usuario', user_id=presente.usuario.id)

    # Verificar se já foi comprado
    if presente.status == 'COMPRADO':
        messages.warning(request, 'Este presente já foi comprado por outra pessoa!')
        return redirect('presentes_usuario', user_id=presente.usuario.id)

    # Marcar como comprado
    presente.status = 'COMPRADO'
    presente.save()

    # Registrar compra
    Compra.objects.create(
        presente=presente,
        comprador=request.user
    )

    # Criar notificação
    Notificacao.objects.create(
        usuario=presente.usuario,
        mensagem=f'🎁 Um dos seus presentes foi comprado: {presente.descricao[:50]}!'
    )

    messages.success(request, 'Presente marcado como comprado!')
    return redirect('presentes_usuario', user_id=presente.usuario.id)

@login_required
def notificacoes_view(request):
    # Otimizar query com select_related
    notificacoes_list = Notificacao.objects.filter(usuario=request.user).select_related('usuario')

    # Marcar todas como lidas
    notificacoes_list.filter(lida=False).update(lida=True)

    # Paginação (30 notificações por página)
    paginator = Paginator(notificacoes_list, 30)
    page = request.GET.get('page', 1)

    try:
        notificacoes = paginator.page(page)
    except PageNotAnInteger:
        notificacoes = paginator.page(1)
    except EmptyPage:
        notificacoes = paginator.page(paginator.num_pages)

    return render(request, 'presentes/notificacoes.html', {'notificacoes': notificacoes})

@login_required
def notificacoes_nao_lidas_json(request):
    """API para buscar notificações não lidas"""
    count = Notificacao.objects.filter(usuario=request.user, lida=False).count()
    notificacoes = Notificacao.objects.filter(
        usuario=request.user, 
        lida=False
    ).values('id', 'mensagem', 'data_notificacao')[:5]
    
    return JsonResponse({
        'count': count,
        'notificacoes': list(notificacoes)
    })

@login_required
def extrair_info_produto_view(request):
    """
    Extrai informações de um produto a partir de uma URL.
    Retorna JSON com título, imagem e preço do produto.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)

    url = request.POST.get('url', '').strip()

    if not url:
        return JsonResponse({'error': 'URL não fornecida'}, status=400)

    # Validar URL
    if not url.startswith('http'):
        url = 'https://' + url

    try:
        import requests
        from bs4 import BeautifulSoup
        import re

        logger.info(f"Extraindo informações de: {url}")

        # Headers para simular navegador
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Extrair título
        titulo = None
        # Tentar og:title primeiro
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            titulo = og_title.get('content')
        # Tentar twitter:title
        if not titulo:
            twitter_title = soup.find('meta', attrs={'name': 'twitter:title'})
            if twitter_title and twitter_title.get('content'):
                titulo = twitter_title.get('content')
        # Tentar title tag
        if not titulo and soup.title:
            titulo = soup.title.string
        # Tentar h1
        if not titulo:
            h1 = soup.find('h1')
            if h1:
                titulo = h1.get_text(strip=True)

        # Limpar título
        if titulo:
            # Remover partes comuns do título
            titulo = re.sub(r'\s*[\|\-]\s*[A-Za-z0-9\s]+$', '', titulo)
            titulo = titulo.strip()[:200]  # Limitar a 200 caracteres

        # Extrair imagem
        imagem_url = None
        # Tentar og:image
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            imagem_url = og_image.get('content')
        # Tentar twitter:image
        if not imagem_url:
            twitter_image = soup.find('meta', attrs={'name': 'twitter:image'})
            if twitter_image and twitter_image.get('content'):
                imagem_url = twitter_image.get('content')
        # Tentar primeira imagem grande do produto
        if not imagem_url:
            product_images = soup.find_all('img', class_=re.compile(r'product|main|zoom|large', re.I))
            if product_images:
                for img in product_images:
                    src = img.get('src') or img.get('data-src')
                    if src and 'no-image' not in src.lower() and 'placeholder' not in src.lower():
                        imagem_url = src
                        break

        # Garantir URL absoluta para imagem
        if imagem_url and not imagem_url.startswith('http'):
            from urllib.parse import urljoin
            imagem_url = urljoin(url, imagem_url)

        # Extrair preço
        preco = None
        # Padrões comuns de preço em Real
        price_patterns = [
            r'R\$?\s*(\d+(?:[.,]\d{3})*(?:[.,]\d{2}))',  # R$ 1.234,56 ou R$1234.56
            r'(\d+(?:[.,]\d{3})*(?:[.,]\d{2}))\s*reais?',  # 1.234,56 reais
        ]

        # Procurar em meta tags primeiro
        price_meta = soup.find('meta', property='product:price:amount') or soup.find('meta', attrs={'itemprop': 'price'})
        if price_meta and price_meta.get('content'):
            try:
                preco_str = price_meta.get('content')
                preco = float(preco_str.replace(',', '.'))
            except:
                pass

        # Procurar no HTML
        if not preco:
            # Procurar em elementos comuns de preço
            price_elements = soup.find_all(['span', 'div', 'strong', 'p'], class_=re.compile(r'price|preco|valor|value', re.I))
            for elem in price_elements:
                text = elem.get_text(strip=True)
                for pattern in price_patterns:
                    match = re.search(pattern, text, re.I)
                    if match:
                        preco_str = match.group(1).replace('.', '').replace(',', '.')
                        try:
                            preco = float(preco_str)
                            break
                        except:
                            continue
                if preco:
                    break

        # Formatar resposta
        response_data = {
            'success': True,
            'titulo': titulo or '',
            'imagem_url': imagem_url or '',
            'preco': preco if preco else '',
        }

        logger.info(f"Informações extraídas: título={titulo}, imagem={bool(imagem_url)}, preco={preco}")

        return JsonResponse(response_data)

    except requests.RequestException as e:
        logger.error(f"Erro ao buscar URL {url}: {str(e)}")
        return JsonResponse({
            'error': 'Não foi possível acessar a URL. Verifique se o link está correto.',
            'details': str(e)
        }, status=400)

    except Exception as e:
        logger.error(f"Erro ao extrair informações de {url}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return JsonResponse({
            'error': 'Erro ao processar a página. Tente preencher os campos manualmente.',
            'details': str(e)
        }, status=500)

@login_required
def gerar_dados_teste_view(request):
    """
    View para gerar dados de teste.
    IMPORTANTE: Apenas superusuários podem acessar esta view.
    Acesso via: /gerar-dados-teste/
    """
    # Verificar se o usuário é superusuário
    if not request.user.is_superuser:
        messages.error(request, 'Acesso negado. Apenas administradores podem gerar dados de teste.')
        return redirect('index')

    if request.method == 'POST':
        try:
            from django.core.management import call_command
            from io import StringIO

            # Capturar a saída do comando
            output = StringIO()

            # Executar comando com 4 usuários e 4 presentes cada
            call_command('populate_test_data', users=4, gifts_per_user=4, stdout=output)

            # Pegar a saída
            result = output.getvalue()

            # Contar resultados
            usuarios_count = Usuario.objects.count()
            presentes_count = Presente.objects.count()
            presentes_ativos = Presente.objects.filter(status='ATIVO').count()

            messages.success(request, f'✓ Dados de teste gerados com sucesso!')
            messages.info(request, f'Total: {usuarios_count} usuários e {presentes_count} presentes ({presentes_ativos} ativos)')

            logger.info(f"Dados de teste gerados por {request.user.email}")
            logger.info(result)

            return redirect('gerar_dados_teste')

        except Exception as e:
            logger.error(f"Erro ao gerar dados de teste: {str(e)}")
            messages.error(request, f'Erro ao gerar dados: {str(e)}')
            return redirect('gerar_dados_teste')

    # GET - Mostrar página de confirmação
    usuarios_count = Usuario.objects.count()
    presentes_count = Presente.objects.count()
    presentes_ativos = Presente.objects.filter(status='ATIVO').count()
    presentes_comprados = Presente.objects.filter(status='COMPRADO').count()

    return render(request, 'presentes/gerar_dados_teste.html', {
        'usuarios_count': usuarios_count,
        'presentes_count': presentes_count,
        'presentes_ativos': presentes_ativos,
        'presentes_comprados': presentes_comprados,
    })
