from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from .models import Usuario, Presente, Compra, Notificacao, SugestaoCompra, Grupo, GrupoMembro
from .forms import UsuarioRegistroForm, PresenteForm, LoginForm, GrupoForm
from .services import IAService
import base64
import logging
import secrets
import hashlib
from datetime import timedelta
from functools import wraps

logger = logging.getLogger(__name__)

# Dicionário para armazenar tokens de recuperação de senha (em produção, usar banco de dados)
password_reset_tokens = {}

def requer_grupo_ativo(view_func):
    """
    Decorator que verifica se o usuario tem um grupo ativo.
    Se nao tiver, redireciona para a pagina de selecao de grupo.
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.grupo_ativo:
            messages.warning(request, 'Selecione ou crie um grupo para continuar.')
            return redirect('grupos_lista')
        return view_func(request, *args, **kwargs)
    return wrapper

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

def baixar_imagem_da_url(url):
    """Baixa uma imagem de uma URL e converte para base64"""
    import requests
    from urllib.parse import urlparse

    try:
        if not url or not url.strip():
            return None, None, None

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
        }

        response = requests.get(url, headers=headers, timeout=15, stream=True)
        response.raise_for_status()

        # Verificar se é uma imagem
        content_type = response.headers.get('content-type', '')
        if not content_type.startswith('image/'):
            logger.warning(f"URL não é uma imagem válida: {content_type}")
            return None, None, None

        # Ler conteúdo
        imagem_data = response.content

        # Verificar tamanho (máximo 5MB)
        if len(imagem_data) > 5 * 1024 * 1024:
            logger.warning("Imagem muito grande (> 5MB)")
            return None, None, None

        # Converter para base64
        imagem_base64 = base64.b64encode(imagem_data).decode('utf-8')

        # Extrair nome do arquivo da URL
        parsed_url = urlparse(url)
        nome_arquivo = parsed_url.path.split('/')[-1] or 'imagem.jpg'
        # Limpar parâmetros do nome
        nome_arquivo = nome_arquivo.split('?')[0]
        if not nome_arquivo or '.' not in nome_arquivo:
            # Determinar extensão pelo content-type
            extensao = content_type.split('/')[-1].split(';')[0]
            if extensao == 'jpeg':
                extensao = 'jpg'
            nome_arquivo = f'imagem.{extensao}'

        logger.info(f"Imagem baixada da URL: {nome_arquivo} ({content_type})")
        return imagem_base64, nome_arquivo, content_type

    except requests.exceptions.RequestException as e:
        logger.error(f"Erro ao baixar imagem da URL {url}: {str(e)}")
        return None, None, None
    except Exception as e:
        logger.error(f"Erro inesperado ao baixar imagem: {str(e)}")
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

def esqueceu_senha_view(request):
    """View para solicitar recuperação de senha"""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()

        if not email:
            return render(request, 'presentes/esqueceu_senha.html', {
                'erro': 'Por favor, informe seu email.'
            })

        try:
            usuario = Usuario.objects.get(email=email)

            # Gerar token único
            token = secrets.token_urlsafe(32)
            token_hash = hashlib.sha256(token.encode()).hexdigest()

            # Armazenar token com expiração de 1 hora
            password_reset_tokens[token_hash] = {
                'user_id': usuario.id,
                'expires': timezone.now() + timedelta(hours=1)
            }

            # Construir URL de redefinição
            reset_url = request.build_absolute_uri(f'/redefinir-senha/{token}/')

            # Tentar enviar email
            try:
                send_mail(
                    subject='Redefinição de Senha - Lista de Presentes de Natal',
                    message=f'''Olá {usuario.first_name},

Você solicitou a redefinição de sua senha na Lista de Presentes de Natal.

Clique no link abaixo para criar uma nova senha:
{reset_url}

Este link expira em 1 hora.

Se você não solicitou esta redefinição, ignore este email.

Atenciosamente,
Equipe Lista de Presentes de Natal
''',
                    from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@listadepresentes.com',
                    recipient_list=[email],
                    fail_silently=False,
                )
                logger.info(f"Email de recuperação enviado para {email}")
            except Exception as e:
                logger.warning(f"Não foi possível enviar email para {email}: {str(e)}")
                # Mesmo sem enviar email, mostrar mensagem genérica para não revelar se o email existe

            return render(request, 'presentes/esqueceu_senha.html', {
                'mensagem_sucesso': f'Se o email {email} estiver cadastrado, você receberá as instruções de recuperação em breve. Verifique também sua caixa de spam.'
            })

        except Usuario.DoesNotExist:
            # Não revelar se o email existe ou não (segurança)
            logger.info(f"Tentativa de recuperação para email não cadastrado: {email}")
            return render(request, 'presentes/esqueceu_senha.html', {
                'mensagem_sucesso': f'Se o email {email} estiver cadastrado, você receberá as instruções de recuperação em breve. Verifique também sua caixa de spam.'
            })

    return render(request, 'presentes/esqueceu_senha.html')

def redefinir_senha_view(request, token):
    """View para redefinir senha com token"""
    # Calcular hash do token
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    # Verificar se token existe e não expirou
    token_data = password_reset_tokens.get(token_hash)

    if not token_data:
        return render(request, 'presentes/redefinir_senha.html', {
            'token_valido': False
        })

    # Verificar expiração
    if timezone.now() > token_data['expires']:
        # Remover token expirado
        del password_reset_tokens[token_hash]
        return render(request, 'presentes/redefinir_senha.html', {
            'token_valido': False
        })

    if request.method == 'POST':
        nova_senha = request.POST.get('nova_senha', '')
        confirmar_senha = request.POST.get('confirmar_senha', '')

        # Validações
        if not nova_senha or not confirmar_senha:
            return render(request, 'presentes/redefinir_senha.html', {
                'token_valido': True,
                'erro': 'Por favor, preencha todos os campos.'
            })

        if nova_senha != confirmar_senha:
            return render(request, 'presentes/redefinir_senha.html', {
                'token_valido': True,
                'erro': 'As senhas não conferem.'
            })

        if len(nova_senha) < 8:
            return render(request, 'presentes/redefinir_senha.html', {
                'token_valido': True,
                'erro': 'A senha deve ter pelo menos 8 caracteres.'
            })

        try:
            usuario = Usuario.objects.get(id=token_data['user_id'])
            usuario.password = make_password(nova_senha)
            usuario.save()

            # Remover token usado
            del password_reset_tokens[token_hash]

            messages.success(request, 'Senha redefinida com sucesso! Faça login com sua nova senha.')
            logger.info(f"Senha redefinida para usuário {usuario.email}")
            return redirect('login')

        except Usuario.DoesNotExist:
            return render(request, 'presentes/redefinir_senha.html', {
                'token_valido': False
            })

    return render(request, 'presentes/redefinir_senha.html', {
        'token_valido': True
    })

@requer_grupo_ativo
def dashboard_view(request):
    grupo_ativo = request.user.grupo_ativo

    # Total de usuários do grupo
    total_usuarios = GrupoMembro.objects.filter(grupo=grupo_ativo).count()

    # Meus presentes ativos no grupo
    meus_presentes_ativos = Presente.objects.filter(
        grupo=grupo_ativo,
        usuario=request.user,
        status='ATIVO'
    ).count()

    # Total de presentes não comprados no grupo (todos os usuários)
    presentes_nao_comprados = Presente.objects.filter(
        grupo=grupo_ativo,
        status='ATIVO'
    ).count()

    # Notificações não lidas do grupo
    notificacoes_nao_lidas = Notificacao.objects.filter(
        grupo=grupo_ativo,
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

@requer_grupo_ativo
def meus_presentes_view(request):
    grupo_ativo = request.user.grupo_ativo

    # Otimizar query com select_related para evitar N+1 - FILTRADO POR GRUPO
    presentes_list = Presente.objects.filter(
        grupo=grupo_ativo,
        usuario=request.user
    ).select_related('usuario').prefetch_related('sugestoes')

    # Estatísticas
    total_presentes = presentes_list.count()
    presentes_ativos = presentes_list.filter(status='ATIVO').count()
    presentes_comprados = presentes_list.filter(status='COMPRADO').count()

    # Paginação (40 presentes por página)
    paginator = Paginator(presentes_list, 40)
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

@requer_grupo_ativo
def adicionar_presente_view(request):
    if request.method == 'POST':
        form = PresenteForm(request.POST, request.FILES)
        if form.is_valid():
            presente = form.save(commit=False)
            presente.usuario = request.user
            presente.grupo = request.user.grupo_ativo  # Definir grupo automaticamente

            # Converter imagem para base64 se foi enviada via upload
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

            # Se não houver imagem via upload, tentar baixar da URL (campo url_imagem do formulário)
            elif not presente.imagem_base64:
                url_imagem = request.POST.get('url_imagem', '').strip()
                if url_imagem:
                    logger.info(f"Tentando baixar imagem da URL: {url_imagem}")
                    imagem_base64, nome_arquivo, content_type = baixar_imagem_da_url(url_imagem)

                    if imagem_base64:
                        presente.imagem_base64 = imagem_base64
                        presente.imagem_nome = nome_arquivo
                        presente.imagem_tipo = content_type
                        presente.imagem = None
                        logger.info(f"Imagem baixada e convertida para base64: {nome_arquivo}")
                    else:
                        logger.warning(f"Não foi possível baixar imagem da URL: {url_imagem}")

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

@requer_grupo_ativo
def editar_presente_view(request, pk):
    grupo_ativo = request.user.grupo_ativo
    presente = get_object_or_404(Presente, pk=pk, grupo=grupo_ativo, usuario=request.user)
    if request.method == 'POST':
        form = PresenteForm(request.POST, request.FILES, instance=presente)
        if form.is_valid():
            presente = form.save(commit=False)

            # Converter imagem para base64 se foi enviada uma nova via upload
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

            # Se não houver imagem via upload, tentar baixar da URL
            else:
                url_imagem = request.POST.get('url_imagem', '').strip()
                if url_imagem:
                    logger.info(f"Tentando baixar imagem da URL para edição: {url_imagem}")
                    imagem_base64, nome_arquivo, content_type = baixar_imagem_da_url(url_imagem)

                    if imagem_base64:
                        presente.imagem_base64 = imagem_base64
                        presente.imagem_nome = nome_arquivo
                        presente.imagem_tipo = content_type
                        presente.imagem = None
                        logger.info(f"Imagem baixada e convertida para base64: {nome_arquivo}")

            presente.save()
            messages.success(request, 'Presente atualizado com sucesso!')
            return redirect('meus_presentes')
    else:
        form = PresenteForm(instance=presente)
    return render(request, 'presentes/editar_presente.html', {'form': form, 'presente': presente})

@requer_grupo_ativo
def deletar_presente_view(request, pk):
    grupo_ativo = request.user.grupo_ativo
    presente = get_object_or_404(Presente, pk=pk, grupo=grupo_ativo, usuario=request.user)
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

@requer_grupo_ativo
def buscar_sugestoes_ia_view(request, pk):
    grupo_ativo = request.user.grupo_ativo
    presente = get_object_or_404(Presente, pk=pk, grupo=grupo_ativo, usuario=request.user)

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

@requer_grupo_ativo
def ver_sugestoes_view(request, pk):
    grupo_ativo = request.user.grupo_ativo

    # Otimizar query com select_related - FILTRADO POR GRUPO
    presente = get_object_or_404(
        Presente.objects.select_related('usuario'),
        pk=pk,
        grupo=grupo_ativo,
        usuario=request.user
    )

    # Sugestões já vem ordenadas por preço (definido no model) - FILTRADAS POR GRUPO
    sugestoes = SugestaoCompra.objects.filter(
        grupo=grupo_ativo,
        presente=presente
    ).select_related('presente')

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

@requer_grupo_ativo
def lista_usuarios_view(request):
    from django.db.models import Min, Q

    grupo_ativo = request.user.grupo_ativo

    # Pegar parâmetros de filtro e ordenação
    ordenar_por = request.GET.get('ordenar', '-data_cadastro')
    preco_min = request.GET.get('preco_min', '')
    preco_max = request.GET.get('preco_max', '')

    # Otimizar query - PEGAR APENAS MEMBROS DO GRUPO ATIVO
    membros_grupo = GrupoMembro.objects.filter(grupo=grupo_ativo).select_related('usuario')
    usuarios_ids = membros_grupo.values_list('usuario_id', flat=True)

    usuarios_list = Usuario.objects.filter(
        id__in=usuarios_ids,
        ativo=True
    ).exclude(id=request.user.id).prefetch_related(
        'presentes',
        'presentes__sugestoes'
    )

    # Adicionar estatísticas para cada usuário - APENAS PRESENTES DO GRUPO
    usuarios_com_stats = []
    for usuario in usuarios_list:
        # Filtrar presentes pelo grupo ativo
        presentes_grupo = usuario.presentes.filter(grupo=grupo_ativo)
        usuario.total_presentes = presentes_grupo.count()
        usuario.presentes_ativos = presentes_grupo.filter(status='ATIVO').count()
        usuario.presentes_comprados = presentes_grupo.filter(status='COMPRADO').count()
        # Adicionar presentes com sugestões como atributo
        usuario.presentes_list = usuario.presentes.filter(status='ATIVO').order_by('-data_cadastro')[:30]
        usuarios_com_stats.append(usuario)

    # Buscar todos os presentes ativos de outros usuários DO GRUPO (para visualização por produto)
    todos_presentes = Presente.objects.filter(
        grupo=grupo_ativo,
        usuario__ativo=True,
        status='ATIVO'
    ).exclude(
        usuario=request.user
    ).select_related('usuario').prefetch_related('sugestoes')

    # Adicionar melhor preço (menor preço das sugestões) para cada presente
    todos_presentes = todos_presentes.annotate(
        melhor_preco=Min('sugestoes__preco_sugerido')
    )

    # Aplicar filtros de preço
    if preco_min:
        try:
            preco_min_valor = float(preco_min)
            todos_presentes = todos_presentes.filter(
                Q(preco__gte=preco_min_valor) | Q(melhor_preco__gte=preco_min_valor)
            )
        except ValueError:
            pass

    if preco_max:
        try:
            preco_max_valor = float(preco_max)
            todos_presentes = todos_presentes.filter(
                Q(preco__lte=preco_max_valor) | Q(melhor_preco__lte=preco_max_valor)
            )
        except ValueError:
            pass

    # Aplicar ordenação
    mapeamento_ordenacao = {
        'produto': 'descricao',
        '-produto': '-descricao',
        'usuario': 'usuario__first_name',
        '-usuario': '-usuario__first_name',
        'preco': 'preco',
        '-preco': '-preco',
        'melhor_preco': 'melhor_preco',
        '-melhor_preco': '-melhor_preco',
        'data': 'data_cadastro',
        '-data': '-data_cadastro',
    }

    ordem_final = mapeamento_ordenacao.get(ordenar_por, '-data_cadastro')
    todos_presentes = todos_presentes.order_by(ordem_final)

    # Paginação (40 usuários por página)
    paginator = Paginator(usuarios_com_stats, 40)
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
        'ordenar_por': ordenar_por,
        'preco_min': preco_min,
        'preco_max': preco_max,
    })

@requer_grupo_ativo
def presentes_usuario_view(request, user_id):
    grupo_ativo = request.user.grupo_ativo
    usuario = get_object_or_404(Usuario, pk=user_id)

    # Verificar se usuario e membro do grupo
    if not GrupoMembro.objects.filter(grupo=grupo_ativo, usuario=usuario).exists():
        messages.error(request, 'Usuario nao e membro do grupo ativo.')
        return redirect('lista_usuarios')

    # Otimizar query com select_related e prefetch_related - FILTRADO POR GRUPO
    presentes_list = Presente.objects.filter(
        grupo=grupo_ativo,
        usuario=usuario
    ).select_related('usuario').prefetch_related('sugestoes', 'compra')

    # Estatísticas
    total_presentes = presentes_list.count()
    presentes_ativos = presentes_list.filter(status='ATIVO').count()
    presentes_comprados = presentes_list.filter(status='COMPRADO').count()

    # Paginação (40 presentes por página)
    paginator = Paginator(presentes_list, 40)
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

@requer_grupo_ativo
@transaction.atomic
def marcar_comprado_view(request, pk):
    grupo_ativo = request.user.grupo_ativo

    # Usar select_for_update para criar um lock no banco de dados
    # Isso previne race condition quando dois usuários tentam comprar o mesmo presente
    try:
        presente = Presente.objects.select_for_update().get(pk=pk, grupo=grupo_ativo)
    except Presente.DoesNotExist:
        messages.error(request, 'Presente não encontrado neste grupo!')
        return redirect('lista_usuarios')

    # Não pode comprar seu próprio presente
    if presente.usuario == request.user:
        messages.error(request, 'Você não pode marcar seu próprio presente como comprado!')
        # Retornar para a página anterior ou lista_usuarios
        referer = request.META.get('HTTP_REFERER')
        if referer and 'usuarios' in referer:
            return redirect('lista_usuarios')
        return redirect('presentes_usuario', user_id=presente.usuario.id)

    # Verificar se já foi comprado
    if presente.status == 'COMPRADO':
        messages.warning(request, 'Este presente já foi comprado por outra pessoa!')
        # Retornar para a página anterior ou lista_usuarios
        referer = request.META.get('HTTP_REFERER')
        if referer and 'usuarios' in referer:
            return redirect('lista_usuarios')
        return redirect('presentes_usuario', user_id=presente.usuario.id)

    # Marcar como comprado
    presente.status = 'COMPRADO'
    presente.save()

    # Registrar compra
    Compra.objects.create(
        grupo=grupo_ativo,
        presente=presente,
        comprador=request.user
    )

    # Criar notificação
    Notificacao.objects.create(
        grupo=grupo_ativo,
        usuario=presente.usuario,
        mensagem=f'🎁 Um dos seus presentes foi comprado: {presente.descricao[:50]}!'
    )

    messages.success(request, 'Presente marcado como comprado!')

    # Retornar para a página anterior (lista_usuarios se veio de lá)
    referer = request.META.get('HTTP_REFERER')
    if referer and 'usuarios' in referer:
        return redirect('lista_usuarios')
    return redirect('presentes_usuario', user_id=presente.usuario.id)

@requer_grupo_ativo
def notificacoes_view(request):
    grupo_ativo = request.user.grupo_ativo

    # Otimizar query com select_related - FILTRADO POR GRUPO
    notificacoes_list = Notificacao.objects.filter(
        grupo=grupo_ativo,
        usuario=request.user
    ).select_related('usuario').order_by('-data_notificacao')

    # Contar notificações não lidas antes de marcar como lidas
    total_nao_lidas = notificacoes_list.filter(lida=False).count()
    total_lidas = notificacoes_list.filter(lida=True).count()

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

    return render(request, 'presentes/notificacoes.html', {
        'notificacoes': notificacoes,
        'total_nao_lidas': total_nao_lidas,
        'total_lidas': total_lidas,
    })

@requer_grupo_ativo
def notificacoes_nao_lidas_json(request):
    """API para buscar notificações não lidas"""
    grupo_ativo = request.user.grupo_ativo

    count = Notificacao.objects.filter(
        grupo=grupo_ativo,
        usuario=request.user,
        lida=False
    ).count()

    notificacoes = Notificacao.objects.filter(
        grupo=grupo_ativo,
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
        from .scrapers import ScraperFactory

        logger.info(f"Extraindo informações de: {url}")

        # Usar o factory para obter o scraper apropriado
        result = ScraperFactory.extract_product_info(url)

        if result:
            titulo, preco, imagem_url = result

            response_data = {
                'success': True,
                'titulo': titulo or '',
                'imagem_url': imagem_url or '',
                'preco': preco if preco else '',
            }

            logger.info(f"Extração bem-sucedida: título={bool(titulo)}, imagem={bool(imagem_url)}, preco={preco}")
            return JsonResponse(response_data)
        else:
            logger.warning(f"Não foi possível extrair informações de {url}")
            return JsonResponse({
                'error': 'Não foi possível extrair informações desta página.',
                'success': False
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


# =====================================================================
# VIEW DE SETUP (PARA RENDER E OUTRAS PLATAFORMAS SEM SHELL)
# =====================================================================

@login_required
def setup_grupos_view(request):
    """
    Interface web para executar setup do grupo padrao.
    Util para plataformas como Render onde nao ha acesso SSH.
    Apenas superusuarios podem acessar.
    """
    # Verificar se usuario e superusuario
    if not request.user.is_superuser:
        messages.error(request, 'Acesso negado. Apenas administradores podem executar o setup.')
        return redirect('dashboard')

    if request.method == 'POST':
        acao = request.POST.get('acao')

        try:
            if acao == 'migrations':
                # Executar migrations
                from django.core.management import call_command
                from io import StringIO

                output = StringIO()

                # Makemigrations
                call_command('makemigrations', stdout=output, interactive=False)
                output_make = output.getvalue()

                # Migrate
                output = StringIO()
                call_command('migrate', stdout=output, interactive=False)
                output_migrate = output.getvalue()

                messages.success(request, 'Migrations executadas com sucesso!')
                messages.info(request, f'Makemigrations: {output_make}')
                messages.info(request, f'Migrate: {output_migrate}')

            elif acao == 'criar_grupo':
                # Criar grupo padrao
                from django.core.management import call_command
                from io import StringIO

                output = StringIO()
                call_command('criar_grupo_padrao', stdout=output)
                resultado = output.getvalue()

                messages.success(request, 'Comando criar_grupo_padrao executado!')

                # Parsear resultado para exibir em mensagens separadas
                for linha in resultado.split('\n'):
                    if linha.strip():
                        if '✓' in linha or '✅' in linha:
                            messages.success(request, linha)
                        elif '⚠' in linha or '❌' in linha:
                            messages.warning(request, linha)
                        else:
                            messages.info(request, linha)

            elif acao == 'migrar_dados':
                # Migrar dados existentes
                from django.core.management import call_command
                from io import StringIO

                output = StringIO()
                call_command('migrar_dados_para_grupo', stdout=output)
                resultado = output.getvalue()

                messages.success(request, 'Comando migrar_dados_para_grupo executado!')

                # Parsear resultado
                for linha in resultado.split('\n'):
                    if linha.strip():
                        if '✓' in linha or '✅' in linha:
                            messages.success(request, linha)
                        elif '⚠' in linha or '❌' in linha:
                            messages.warning(request, linha)
                        else:
                            messages.info(request, linha)

            elif acao == 'setup_completo':
                # Executar setup completo
                from django.core.management import call_command
                from io import StringIO

                # 1. Migrations
                output = StringIO()
                call_command('makemigrations', stdout=output, interactive=False)
                call_command('migrate', stdout=output, interactive=False)
                messages.success(request, '1/3 Migrations aplicadas')

                # 2. Criar grupo
                output = StringIO()
                call_command('criar_grupo_padrao', stdout=output)
                resultado_grupo = output.getvalue()
                messages.success(request, '2/3 Grupo criado e usuarios adicionados')

                # 3. Migrar dados
                output = StringIO()
                call_command('migrar_dados_para_grupo', stdout=output)
                resultado_dados = output.getvalue()
                messages.success(request, '3/3 Dados migrados para o grupo')

                messages.success(request, '✅ SETUP COMPLETO EXECUTADO COM SUCESSO!')

                # Exibir resumo
                for linha in resultado_grupo.split('\n'):
                    if 'Resumo:' in linha or '•' in linha:
                        messages.info(request, linha)

        except Exception as e:
            logger.error(f"Erro ao executar setup: {str(e)}")
            messages.error(request, f'Erro ao executar: {str(e)}')

    # Buscar informacoes do sistema
    try:
        total_usuarios = Usuario.objects.count()
        total_grupos = Grupo.objects.count()
        total_presentes = Presente.objects.count()
        presentes_sem_grupo = Presente.objects.filter(grupo__isnull=True).count()
        compras_sem_grupo = Compra.objects.filter(grupo__isnull=True).count()
        notificacoes_sem_grupo = Notificacao.objects.filter(grupo__isnull=True).count()

        # Verificar se existe grupo padrao
        grupo_padrao = None
        try:
            grupo_padrao = Grupo.objects.get(nome='Natal Família Cruz e Credos 2025')
            membros_grupo = grupo_padrao.membros.count()
        except Grupo.DoesNotExist:
            membros_grupo = 0

    except Exception as e:
        total_usuarios = 0
        total_grupos = 0
        total_presentes = 0
        presentes_sem_grupo = 0
        compras_sem_grupo = 0
        notificacoes_sem_grupo = 0
        grupo_padrao = None
        membros_grupo = 0

    context = {
        'total_usuarios': total_usuarios,
        'total_grupos': total_grupos,
        'total_presentes': total_presentes,
        'presentes_sem_grupo': presentes_sem_grupo,
        'compras_sem_grupo': compras_sem_grupo,
        'notificacoes_sem_grupo': notificacoes_sem_grupo,
        'grupo_padrao': grupo_padrao,
        'membros_grupo': membros_grupo,
    }

    return render(request, 'presentes/setup_grupos.html', context)


# =====================================================================
# VIEWS DE GRUPOS
# =====================================================================

@login_required
def grupos_lista_view(request):
    """
    Lista todos os grupos do usuario.
    Permite selecionar grupo ativo.
    """
    grupos = request.user.get_grupos()
    grupo_ativo = request.user.grupo_ativo

    # Se usuario nao tem grupos, redirecionar para criar
    if not grupos.exists():
        messages.info(request, 'Voce ainda nao faz parte de nenhum grupo. Crie ou junte-se a um!')
        return redirect('criar_grupo')

    context = {
        'grupos': grupos,
        'grupo_ativo': grupo_ativo,
    }
    return render(request, 'presentes/grupos/lista.html', context)


@login_required
def criar_grupo_view(request):
    """Cria um novo grupo e adiciona o usuario como mantenedor"""
    if request.method == 'POST':
        form = GrupoForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Criar grupo
                    grupo = form.save()

                    # Processar imagem se URL fornecida
                    url_imagem = request.POST.get('url_imagem', '').strip()
                    if url_imagem:
                        imagem_base64, imagem_nome, imagem_tipo = baixar_imagem_da_url(url_imagem)
                        if imagem_base64:
                            grupo.imagem_base64 = imagem_base64
                            grupo.imagem_nome = imagem_nome
                            grupo.imagem_tipo = imagem_tipo
                            grupo.save()

                    # Adicionar usuario como mantenedor
                    GrupoMembro.objects.create(
                        grupo=grupo,
                        usuario=request.user,
                        e_mantenedor=True
                    )

                    # Definir como grupo ativo
                    request.user.grupo_ativo = grupo
                    request.user.save()

                    messages.success(request, f'Grupo "{grupo.nome}" criado com sucesso!')
                    logger.info(f"Grupo {grupo.id} criado por {request.user.email}")
                    return redirect('grupos_lista')

            except Exception as e:
                logger.error(f"Erro ao criar grupo: {str(e)}")
                messages.error(request, f'Erro ao criar grupo: {str(e)}')
    else:
        form = GrupoForm()

    return render(request, 'presentes/grupos/criar.html', {'form': form})


@login_required
def editar_grupo_view(request, pk):
    """Edita informacoes do grupo (apenas mantenedores)"""
    grupo = get_object_or_404(Grupo, pk=pk)

    # Verificar se usuario e mantenedor
    if not GrupoMembro.objects.filter(grupo=grupo, usuario=request.user, e_mantenedor=True).exists():
        messages.error(request, 'Apenas mantenedores podem editar o grupo.')
        return redirect('grupos_lista')

    if request.method == 'POST':
        form = GrupoForm(request.POST, instance=grupo)
        if form.is_valid():
            grupo = form.save()

            # Processar imagem se URL fornecida
            url_imagem = request.POST.get('url_imagem', '').strip()
            if url_imagem:
                imagem_base64, imagem_nome, imagem_tipo = baixar_imagem_da_url(url_imagem)
                if imagem_base64:
                    grupo.imagem_base64 = imagem_base64
                    grupo.imagem_nome = imagem_nome
                    grupo.imagem_tipo = imagem_tipo
                    grupo.save()

            messages.success(request, f'Grupo "{grupo.nome}" atualizado com sucesso!')
            logger.info(f"Grupo {grupo.id} editado por {request.user.email}")
            return redirect('gerenciar_membros', pk=grupo.pk)
    else:
        form = GrupoForm(instance=grupo)

    context = {
        'form': form,
        'grupo': grupo,
    }
    return render(request, 'presentes/grupos/editar.html', context)


@login_required
def ativar_grupo_view(request, pk):
    """Define o grupo ativo do usuario"""
    grupo = get_object_or_404(Grupo, pk=pk)

    # Verificar se usuario e membro
    if not GrupoMembro.objects.filter(grupo=grupo, usuario=request.user).exists():
        messages.error(request, 'Voce nao e membro deste grupo.')
        return redirect('grupos_lista')

    # Verificar se grupo esta ativo
    if not grupo.ativo:
        messages.error(request, 'Este grupo esta desativado.')
        return redirect('grupos_lista')

    # Definir como grupo ativo
    request.user.grupo_ativo = grupo
    request.user.save()

    messages.success(request, f'Grupo "{grupo.nome}" ativado!')
    logger.info(f"Usuario {request.user.email} ativou grupo {grupo.id}")

    # Redirecionar para dashboard ou de onde veio
    next_url = request.GET.get('next', 'dashboard')
    return redirect(next_url)


@login_required
def gerenciar_membros_view(request, pk):
    """Gerencia membros do grupo (apenas mantenedores)"""
    grupo = get_object_or_404(Grupo, pk=pk)

    # Verificar se usuario e mantenedor
    e_mantenedor = GrupoMembro.objects.filter(
        grupo=grupo,
        usuario=request.user,
        e_mantenedor=True
    ).exists()

    if not e_mantenedor:
        messages.error(request, 'Apenas mantenedores podem gerenciar membros.')
        return redirect('grupos_lista')

    # Listar membros
    membros = grupo.membros.select_related('usuario').all()
    link_convite = grupo.get_link_convite()

    context = {
        'grupo': grupo,
        'membros': membros,
        'link_convite': link_convite,
        'e_mantenedor': e_mantenedor,
    }
    return render(request, 'presentes/grupos/membros.html', context)


@login_required
def remover_membro_view(request, pk, user_id):
    """Remove um membro do grupo (apenas mantenedores)"""
    grupo = get_object_or_404(Grupo, pk=pk)
    usuario_remover = get_object_or_404(Usuario, pk=user_id)

    # Verificar se usuario e mantenedor
    if not GrupoMembro.objects.filter(grupo=grupo, usuario=request.user, e_mantenedor=True).exists():
        messages.error(request, 'Apenas mantenedores podem remover membros.')
        return redirect('grupos_lista')

    # Nao pode remover a si mesmo
    if usuario_remover == request.user:
        messages.error(request, 'Voce nao pode remover a si mesmo. Use a opcao de sair do grupo.')
        return redirect('gerenciar_membros', pk=pk)

    try:
        membro = GrupoMembro.objects.get(grupo=grupo, usuario=usuario_remover)
        membro.delete()

        # Se o usuario removido tinha esse grupo como ativo, limpar
        if usuario_remover.grupo_ativo == grupo:
            usuario_remover.grupo_ativo = None
            usuario_remover.save()

        messages.success(request, f'Usuario {usuario_remover} removido do grupo.')
        logger.info(f"Usuario {usuario_remover.email} removido do grupo {grupo.id} por {request.user.email}")
    except GrupoMembro.DoesNotExist:
        messages.error(request, 'Usuario nao e membro deste grupo.')

    return redirect('gerenciar_membros', pk=pk)


@login_required
def toggle_mantenedor_view(request, pk, user_id):
    """Alterna status de mantenedor de um membro (apenas mantenedores)"""
    grupo = get_object_or_404(Grupo, pk=pk)
    usuario_alvo = get_object_or_404(Usuario, pk=user_id)

    # Verificar se usuario e mantenedor
    if not GrupoMembro.objects.filter(grupo=grupo, usuario=request.user, e_mantenedor=True).exists():
        messages.error(request, 'Apenas mantenedores podem alterar permissoes.')
        return redirect('grupos_lista')

    try:
        membro = GrupoMembro.objects.get(grupo=grupo, usuario=usuario_alvo)

        # Alternar status
        membro.e_mantenedor = not membro.e_mantenedor
        membro.save()

        status = "mantenedor" if membro.e_mantenedor else "membro comum"
        messages.success(request, f'Usuario {usuario_alvo} agora e {status}.')
        logger.info(f"Usuario {usuario_alvo.email} agora e {status} do grupo {grupo.id}")
    except GrupoMembro.DoesNotExist:
        messages.error(request, 'Usuario nao e membro deste grupo.')

    return redirect('gerenciar_membros', pk=pk)


@login_required
def toggle_ativo_grupo_view(request, pk):
    """Ativa/Desativa um grupo (apenas mantenedores)"""
    grupo = get_object_or_404(Grupo, pk=pk)

    # Verificar se usuario e mantenedor
    if not GrupoMembro.objects.filter(grupo=grupo, usuario=request.user, e_mantenedor=True).exists():
        messages.error(request, 'Apenas mantenedores podem ativar/desativar o grupo.')
        return redirect('grupos_lista')

    # Alternar status
    grupo.ativo = not grupo.ativo
    grupo.save()

    status = "ativado" if grupo.ativo else "desativado"
    messages.success(request, f'Grupo "{grupo.nome}" {status}.')
    logger.info(f"Grupo {grupo.id} {status} por {request.user.email}")

    return redirect('gerenciar_membros', pk=pk)


@login_required
def sair_grupo_view(request, pk):
    """Usuario sai do grupo"""
    grupo = get_object_or_404(Grupo, pk=pk)

    try:
        membro = GrupoMembro.objects.get(grupo=grupo, usuario=request.user)

        # Verificar se e o ultimo mantenedor
        if membro.e_mantenedor:
            mantenedores_count = GrupoMembro.objects.filter(grupo=grupo, e_mantenedor=True).count()
            if mantenedores_count == 1:
                messages.error(request, 'Voce e o ultimo mantenedor. Promova outro membro antes de sair.')
                return redirect('gerenciar_membros', pk=pk)

        membro.delete()

        # Limpar grupo ativo se for este
        if request.user.grupo_ativo == grupo:
            request.user.grupo_ativo = None
            request.user.save()

        messages.success(request, f'Voce saiu do grupo "{grupo.nome}".')
        logger.info(f"Usuario {request.user.email} saiu do grupo {grupo.id}")
    except GrupoMembro.DoesNotExist:
        messages.error(request, 'Voce nao e membro deste grupo.')

    return redirect('grupos_lista')


@login_required
def convite_grupo_view(request, codigo):
    """Aceita convite para entrar em um grupo"""
    grupo = get_object_or_404(Grupo, codigo_convite=codigo)

    # Verificar se grupo esta ativo
    if not grupo.ativo:
        messages.error(request, 'Este grupo esta desativado.')
        return redirect('grupos_lista')

    # Verificar se ja e membro
    if GrupoMembro.objects.filter(grupo=grupo, usuario=request.user).exists():
        messages.info(request, f'Voce ja e membro do grupo "{grupo.nome}".')
        return redirect('grupos_lista')

    # Adicionar como membro
    GrupoMembro.objects.create(
        grupo=grupo,
        usuario=request.user,
        e_mantenedor=False
    )

    # Se usuario nao tem grupo ativo, definir este
    if not request.user.grupo_ativo:
        request.user.grupo_ativo = grupo
        request.user.save()

    messages.success(request, f'Bem-vindo ao grupo "{grupo.nome}"!')
    logger.info(f"Usuario {request.user.email} entrou no grupo {grupo.id} via convite")

    return redirect('grupos_lista')


def servir_imagem_grupo_view(request, pk):
    """Serve a imagem do grupo em base64"""
    grupo = get_object_or_404(Grupo, pk=pk)

    if not grupo.imagem_base64:
        return HttpResponse('Sem imagem', status=404)

    try:
        # Decodificar base64
        imagem_data = base64.b64decode(grupo.imagem_base64)

        # Retornar imagem com content-type correto
        content_type = grupo.imagem_tipo or 'image/jpeg'
        return HttpResponse(imagem_data, content_type=content_type)
    except Exception as e:
        logger.error(f"Erro ao servir imagem do grupo {pk}: {str(e)}")
        return HttpResponse('Erro ao carregar imagem', status=500)
