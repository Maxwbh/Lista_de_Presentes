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
from .models import Usuario, Presente, Compra, Notificacao, SugestaoCompra
from .forms import UsuarioRegistroForm, PresenteForm, LoginForm
from .services import IAService
import base64
import logging
import secrets
import hashlib
from datetime import timedelta

logger = logging.getLogger(__name__)

# Dicionário para armazenar tokens de recuperação de senha (em produção, usar banco de dados)
password_reset_tokens = {}

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

@login_required
def editar_presente_view(request, pk):
    presente = get_object_or_404(Presente, pk=pk, usuario=request.user)
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
    from django.db.models import Min, Q

    # Pegar parâmetros de filtro e ordenação
    ordenar_por = request.GET.get('ordenar', '-data_cadastro')
    preco_min = request.GET.get('preco_min', '')
    preco_max = request.GET.get('preco_max', '')

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
        'ordenar_por': ordenar_por,
        'preco_min': preco_min,
        'preco_max': preco_max,
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
        presente=presente,
        comprador=request.user
    )

    # Criar notificação
    Notificacao.objects.create(
        usuario=presente.usuario,
        mensagem=f'🎁 Um dos seus presentes foi comprado: {presente.descricao[:50]}!'
    )

    messages.success(request, 'Presente marcado como comprado!')

    # Retornar para a página anterior (lista_usuarios se veio de lá)
    referer = request.META.get('HTTP_REFERER')
    if referer and 'usuarios' in referer:
        return redirect('lista_usuarios')
    return redirect('presentes_usuario', user_id=presente.usuario.id)

@login_required
def notificacoes_view(request):
    # Otimizar query com select_related
    notificacoes_list = Notificacao.objects.filter(usuario=request.user).select_related('usuario').order_by('-data_notificacao')

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
