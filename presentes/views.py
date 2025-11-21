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

    return render(request, 'presentes/ver_sugestoes.html', {
        'presente': presente,
        'sugestoes': sugestoes
    })

@login_required
def lista_usuarios_view(request):
    # Otimizar query com prefetch_related para pegar presentes
    usuarios_list = Usuario.objects.filter(ativo=True).exclude(id=request.user.id).prefetch_related('presentes')

    # Adicionar estatísticas para cada usuário
    usuarios_com_stats = []
    for usuario in usuarios_list:
        usuario.total_presentes = usuario.presentes.count()
        usuario.presentes_ativos = usuario.presentes.filter(status='ATIVO').count()
        usuario.presentes_comprados = usuario.presentes.filter(status='COMPRADO').count()
        usuarios_com_stats.append(usuario)

    # Paginação (20 usuários por página)
    paginator = Paginator(usuarios_com_stats, 20)
    page = request.GET.get('page', 1)

    try:
        usuarios = paginator.page(page)
    except PageNotAnInteger:
        usuarios = paginator.page(1)
    except EmptyPage:
        usuarios = paginator.page(paginator.num_pages)

    return render(request, 'presentes/lista_usuarios.html', {'usuarios': usuarios})

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
