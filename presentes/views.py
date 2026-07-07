from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.db.models import Count, Prefetch, Q
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from .models import Usuario, Presente, Compra, Notificacao, SugestaoCompra, Grupo, GrupoMembro, PrecoHistorico, PesquisaPrecoLog, PushSubscription
from .forms import UsuarioRegistroForm, PresenteForm, LoginForm, GrupoForm, EditarPerfilForm
from .services import IAService
from .github_helper import criar_issue_falha_imagem
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
        form = UsuarioRegistroForm(request.POST, request.FILES)
        if form.is_valid():
            usuario = form.save()
            # Processar foto se enviada
            if 'foto' in request.FILES:
                foto_file = request.FILES['foto']
                if foto_file.content_type.startswith('image/'):
                    import base64
                    foto_data = base64.b64encode(foto_file.read()).decode('utf-8')
                    usuario.foto_base64 = foto_data
                    usuario.foto_tipo = foto_file.content_type
                    usuario.save(update_fields=['foto_base64', 'foto_tipo'])
            login(request, usuario)
            messages.success(request, 'Cadastro realizado com sucesso!')
            return redirect('dashboard')
    else:
        form = UsuarioRegistroForm()
    return render(request, 'presentes/registro.html', {'form': form})

@login_required
def editar_perfil_view(request):
    """Permite ao usuário editar seu perfil: dados, avatar e foto."""
    if request.method == 'POST':
        form = EditarPerfilForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            usuario = form.save()
            # Remover foto (volta a usar avatar emoji)
            if form.cleaned_data.get('remover_foto'):
                usuario.foto_base64 = None
                usuario.foto_tipo = None
                usuario.save(update_fields=['foto_base64', 'foto_tipo'])
            # Nova foto enviada
            elif 'foto' in request.FILES:
                foto_file = request.FILES['foto']
                if foto_file.content_type.startswith('image/'):
                    foto_data = base64.b64encode(foto_file.read()).decode('utf-8')
                    usuario.foto_base64 = foto_data
                    usuario.foto_tipo = foto_file.content_type
                    usuario.save(update_fields=['foto_base64', 'foto_tipo'])
            messages.success(request, 'Perfil atualizado com sucesso!')
            return redirect('editar_perfil')
    else:
        form = EditarPerfilForm(instance=request.user)
    return render(request, 'presentes/editar_perfil.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            usuario = authenticate(request, username=email, password=password)
            if usuario:
                login(request, usuario)
                # Respeitar ?next= (ex.: links de convite de grupo abertos deslogado)
                from django.utils.http import url_has_allowed_host_and_scheme
                next_url = request.POST.get('next') or request.GET.get('next')
                if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                    return redirect(next_url)
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
    ).select_related('usuario').prefetch_related('sugestoes', 'historico_precos')

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
                        # Falha ao baixar imagem - marcar para criar issue no GitHub depois
                        logger.warning(f"Não foi possível baixar imagem da URL: {url_imagem}")
                        # Guardar info para criar issue depois (após salvar presente)
                        falha_imagem = {
                            'url': url_imagem,
                            'erro': "Falha ao baixar imagem da URL fornecida. Possíveis causas: URL inacessível, formato não suportado, timeout, restrições de CORS."
                        }
                else:
                    falha_imagem = None
            else:
                falha_imagem = None

            # Salvar presente
            presente.save()

            # Registrar preço de cadastro no histórico (temperatura de preços)
            if presente.preco:
                presente.registrar_preco(presente.preco, loja='Cadastro', fonte='cadastro')

            # Se houve falha no download da imagem, criar issue no GitHub
            if 'falha_imagem' in locals() and falha_imagem:
                try:
                    resultado_issue = criar_issue_falha_imagem(
                        presente=presente,
                        url_imagem=falha_imagem['url'],
                        erro_descricao=falha_imagem['erro'],
                        usuario=request.user
                    )

                    if resultado_issue and resultado_issue.get('success'):
                        issue_url = resultado_issue.get('issue_url')
                        issue_num = resultado_issue.get('issue_number')
                        logger.info(f"Issue #{issue_num} criada automaticamente: {issue_url}")
                        messages.info(
                            request,
                            f'⚠️ Imagem não pôde ser carregada. '
                            f'Uma <a href="{issue_url}" target="_blank">issue #{issue_num}</a> '
                            f'foi criada automaticamente para investigação.'
                        )
                except Exception as e:
                    logger.error(f"Erro ao criar issue no GitHub: {str(e)}")

            # Buscar precos em background (nao bloqueia o request)
            import threading
            def _buscar_precos_background(presente_id):
                try:
                    from presentes.models import Presente as PresenteModel
                    p = PresenteModel.objects.get(pk=presente_id)
                    IAService.buscar_sugestoes_reais(p)
                except Exception as e:
                    logger.error(f"Erro ao buscar precos em background: {e}")

            thread = threading.Thread(target=_buscar_precos_background, args=(presente.id,), daemon=True)
            thread.start()

            messages.success(request, 'Presente adicionado com sucesso! Sugestoes de preco serao buscadas em background.')

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

            # Registrar alteração de preço no histórico (temperatura de preços)
            if presente.preco:
                presente.registrar_preco(presente.preco, loja='Cadastro', fonte='cadastro')

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

    # Um único botão: os motores de IA são tentados em sequência
    # (Gemini -> Claude -> ChatGPT), com fallback automático.
    try:
        sucesso, mensagem = IAService.buscar_sugestoes_com_fallback(presente)
        if sucesso:
            messages.success(request, mensagem)
        else:
            messages.warning(request, mensagem)
    except Exception as e:
        logger.error(f"Erro ao buscar sugestões: {str(e)}")
        messages.warning(request, "Não foi possível buscar sugestões no momento. Tente novamente mais tarde.")

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

    # Temperatura de preços + histórico para o sparkline (estilo LPII)
    historico = list(presente.historico_precos.all())
    sparkline = _montar_sparkline(historico)

    # Economia: melhor sugestão vs preço cadastrado
    melhor_sugestao = sugestoes.filter(preco_sugerido__isnull=False).order_by('preco_sugerido').first()
    economia = None
    if melhor_sugestao and presente.preco and melhor_sugestao.preco_sugerido < presente.preco:
        economia = presente.preco - melhor_sugestao.preco_sugerido

    return render(request, 'presentes/ver_sugestoes.html', {
        'presente': presente,
        'sugestoes': sugestoes,
        'temperatura': presente.temperatura(),
        'historico': historico,
        'sparkline': sparkline,
        'melhor_sugestao': melhor_sugestao,
        'economia': economia,
    })


def _montar_sparkline(historico, largura=600, altura=220):
    """
    Calcula as coordenadas SVG do gráfico de histórico de preços,
    no estilo do PriceComparisonModal do LPII: grade horizontal com
    valores, área em gradiente rose, linha 2.5px e pontos brancos.
    """
    pontos_validos = [h for h in historico if h.preco][-12:]
    if len(pontos_validos) < 2:
        return None

    pad_esq, pad_dir, pad_top, pad_inf = 64, 20, 16, 34
    plot_largura = largura - pad_esq - pad_dir
    plot_altura = altura - pad_top - pad_inf
    y_base = altura - pad_inf

    precos = [float(h.preco) for h in pontos_validos]
    p_min = min(precos) * 0.95
    p_max = max(precos) * 1.05
    faixa = (p_max - p_min) or 1.0

    def get_y(valor):
        return y_base - ((valor - p_min) * plot_altura) / faixa

    n = len(pontos_validos)
    # Rotular no máximo ~4 datas (primeira, intermediárias e última)
    passo_rotulo = max(1, (n - 1) // 3 or 1)
    indices_rotulo = set(range(0, n, passo_rotulo)) | {n - 1}

    # IMPORTANTE: coordenadas formatadas como string em Python (ponto decimal).
    # Com LANGUAGE_CODE=pt-br o Django renderiza floats com vírgula no template
    # ("217,5"), o que é inválido como atributo SVG e quebra o gráfico.
    pontos = []
    for i, h in enumerate(pontos_validos):
        x = pad_esq + i * plot_largura / (n - 1)
        pontos.append({
            'x': f'{x:.1f}',
            'y': f'{get_y(float(h.preco)):.1f}',
            'preco': h.preco, 'loja': h.loja, 'data': h.data,
            'data_fmt': h.data.strftime('%d/%m'),
            'rotulo': i in indices_rotulo,
        })

    # Grade horizontal com 4 níveis de preço (valores já formatados)
    grades = []
    for i in range(4):
        valor = p_min + faixa * i / 3
        grades.append({
            'y': f'{get_y(valor):.1f}',
            'y_texto': f'{get_y(valor) + 4:.1f}',
            'valor_fmt': f'R$ {valor:,.0f}'.replace(',', '.'),
        })

    polyline = ' '.join(f"{p['x']},{p['y']}" for p in pontos)
    area = f"M {pontos[0]['x']},{y_base} L " + ' L '.join(
        f"{p['x']},{p['y']}" for p in pontos
    ) + f" L {pontos[-1]['x']},{y_base} Z"

    return {
        'pontos': pontos, 'grades': grades,
        'polyline': polyline, 'area': area,
        'largura': largura, 'altura': altura,
        'pad_esq': pad_esq, 'grade_x2': largura - pad_dir,
        'pad_esq_texto': pad_esq - 8,
        'y_base': y_base, 'y_rotulo': y_base + 22,
        'min': min(precos), 'max': max(precos),
    }


@requer_grupo_ativo
def aplicar_preco_view(request, pk, sugestao_id):
    """Aplica o preço de uma sugestão ao presente e registra no histórico (LPII 'Aplicar')."""
    if request.method != 'POST':
        return redirect('ver_sugestoes', pk=pk)

    grupo_ativo = request.user.grupo_ativo
    presente = get_object_or_404(Presente, pk=pk, grupo=grupo_ativo, usuario=request.user)
    sugestao = get_object_or_404(SugestaoCompra, pk=sugestao_id, presente=presente)

    if not sugestao.preco_sugerido:
        messages.warning(request, 'Esta sugestão não possui preço para aplicar.')
        return redirect('ver_sugestoes', pk=pk)

    presente.preco = sugestao.preco_sugerido
    presente.save(update_fields=['preco'])
    presente.registrar_preco(sugestao.preco_sugerido, loja=sugestao.local_compra, fonte='aplicado')

    messages.success(request, f'Preço atualizado para R$ {sugestao.preco_sugerido} ({sugestao.local_compra}).')
    return redirect('ver_sugestoes', pk=pk)

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

    presentes_grupo_qs = Presente.objects.filter(grupo=grupo_ativo).select_related('usuario').prefetch_related('sugestoes', 'historico_precos')

    usuarios_list = Usuario.objects.filter(
        id__in=usuarios_ids,
        ativo=True
    ).exclude(id=request.user.id).prefetch_related(
        Prefetch('presentes', queryset=presentes_grupo_qs, to_attr='presentes_do_grupo')
    )

    usuarios_com_stats = []
    for usuario in usuarios_list:
        presentes = usuario.presentes_do_grupo
        usuario.total_presentes = len(presentes)
        usuario.presentes_ativos = sum(1 for p in presentes if p.status == 'ATIVO')
        usuario.presentes_comprados = sum(1 for p in presentes if p.status == 'COMPRADO')
        # Mostrar todos os presentes (ativos e comprados); ativos primeiro
        ordenados = sorted(presentes, key=lambda p: (p.status != 'ATIVO', -p.id))
        usuario.presentes_list = ordenados[:60]
        usuarios_com_stats.append(usuario)

    # Buscar todos os presentes do grupo (ativos e comprados) para a visualização por produto
    todos_presentes = Presente.objects.filter(
        grupo=grupo_ativo,
        usuario__ativo=True
    ).exclude(
        usuario=request.user
    ).select_related('usuario').prefetch_related('sugestoes', 'historico_precos')

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

    # Disponíveis sempre antes dos comprados, depois a ordenação escolhida
    ordem_final = mapeamento_ordenacao.get(ordenar_por, '-data_cadastro')
    from django.db.models import Case, When, IntegerField
    todos_presentes = list(
        todos_presentes.annotate(
            ordem_status=Case(
                When(status='ATIVO', then=0), default=1, output_field=IntegerField()
            )
        ).order_by('ordem_status', ordem_final)
    )

    # Gráfico de evolução de preço (LPII) para o modal de cada produto
    for p in todos_presentes:
        p.sparkline = _montar_sparkline(list(p.historico_precos.all()), largura=500, altura=190)

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
    ).select_related('usuario').prefetch_related('sugestoes', 'compra', 'historico_precos')

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
def compras_grupo_json(request):
    """
    API: dados de compra do grupo ativo (presentes já comprados), para
    consulta e para evitar compra em duplicidade.

    Preserva a surpresa: NÃO retorna compras dos presentes do próprio
    solicitante (a pessoa não deve descobrir o que compraram para ela).
    Filtro opcional ?tipo=minhas retorna apenas as compras feitas por você.
    """
    grupo_ativo = request.user.grupo_ativo
    if not grupo_ativo:
        return JsonResponse({'total': 0, 'compras': [], 'erro': 'Sem grupo ativo'}, status=400)

    tipo = request.GET.get('tipo', 'grupo')

    compras = Compra.objects.filter(
        grupo=grupo_ativo
    ).select_related('presente', 'presente__usuario', 'comprador')

    if tipo == 'minhas':
        # Compras que EU fiz (posso ver tudo)
        compras = compras.filter(comprador=request.user)
    else:
        # Compras do grupo, exceto as dos meus presentes (protege a surpresa)
        compras = compras.exclude(presente__usuario=request.user)

    compras = compras.order_by('-data_compra')[:100]

    dados = [{
        'presente': c.presente.descricao[:80],
        'para': c.presente.usuario.get_full_name() or c.presente.usuario.first_name,
        'comprador': c.comprador.get_full_name() or c.comprador.first_name,
        'foi_voce': c.comprador_id == request.user.id,
        'preco': str(c.presente.preco) if c.presente.preco else None,
        'data': c.data_compra.isoformat(),
    } for c in compras]

    return JsonResponse({'tipo': tipo, 'total': len(dados), 'compras': dados})


@csrf_exempt
def cron_pesquisar_precos(request):
    """
    Endpoint de cron para a pesquisa semanal de preços. Protegido por token
    (header 'X-Cron-Token' ou ?token=). Chamado por um agendador externo
    (GitHub Actions) — mais confiável e observável que depender só do tráfego.

    Respeita o intervalo de 7 dias (use ?forcar=1 para ignorar). Dispara em
    background e responde imediatamente.
    """
    from django.conf import settings
    from .pesquisa_precos import pesquisa_em_atraso, executar_pesquisa

    token_esperado = getattr(settings, 'CRON_TOKEN', '') or ''
    token_recebido = request.headers.get('X-Cron-Token') or request.GET.get('token', '')

    if not token_esperado:
        return JsonResponse({'erro': 'CRON_TOKEN não configurado no servidor'}, status=503)
    if token_recebido != token_esperado:
        return JsonResponse({'erro': 'Token inválido'}, status=403)

    forcar = request.GET.get('forcar') in ('1', 'true', 'sim')
    if not forcar and not pesquisa_em_atraso():
        return JsonResponse({'status': 'ignorado', 'motivo': 'Última pesquisa tem menos de 7 dias'})

    import threading
    threading.Thread(
        target=executar_pesquisa,
        kwargs={'origem': 'comando'},
        daemon=True
    ).start()

    return JsonResponse({'status': 'iniciado', 'mensagem': 'Pesquisa de preços disparada em background'})


@login_required
def extrair_info_produto_view(request):
    """
    Extrai informações de um produto a partir de uma URL.
    Retorna JSON com título, imagem e preço do produto.

    Em caso de falha de scraping (site acessível mas dados não extraídos),
    cria automaticamente uma issue no GitHub.
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
        from .github_helper import criar_issue_falha_scraping

        logger.info(f"Extraindo informações de: {url}")

        # Usar o factory para obter o scraper apropriado (retorna dict agora)
        result = ScraperFactory.extract_product_info(url)

        if result.get('success'):
            # Extração bem-sucedida
            response_data = {
                'success': True,
                'titulo': result.get('titulo', ''),
                'imagem_url': result.get('imagem_url', ''),
                'preco': result.get('preco', ''),
            }

            logger.info(f"Extração bem-sucedida: título={bool(result.get('titulo'))}, imagem={bool(result.get('imagem_url'))}, preco={result.get('preco')}")
            return JsonResponse(response_data)

        else:
            # Extração falhou
            error_type = result.get('error_type')
            error_message = result.get('error_message', 'Erro desconhecido')

            if error_type == 'network':
                # Erro de rede/HTTP (404, 500, timeout, etc.)
                # Apenas informar ao usuário, NÃO criar issue
                logger.warning(f"Erro de rede ao acessar {url}: {error_message}")
                return JsonResponse({
                    'success': False,
                    'error': f'Não foi possível acessar o site: {error_message}',
                    'error_type': 'network'
                }, status=400)

            elif error_type == 'parsing':
                # Erro de parsing (site acessível mas dados não extraídos)
                # Criar issue no GitHub
                logger.warning(f"Falha de scraping para {url}: {error_message}")

                # Criar issue no GitHub
                partial_data = result.get('partial_data', {})
                dados_extraidos = {
                    'titulo': partial_data.get('titulo'),
                    'preco': partial_data.get('preco'),
                    'imagem_url': partial_data.get('imagem_url')
                }

                resultado_issue = criar_issue_falha_scraping(
                    url_produto=url,
                    dados_extraidos=dados_extraidos,
                    usuario=request.user,
                    grupo=request.user.grupo_ativo if hasattr(request.user, 'grupo_ativo') else None
                )

                # Preparar mensagem de resposta
                mensagem_erro = 'Não foi possível extrair as informações desta página. '

                if resultado_issue and resultado_issue.get('success'):
                    issue_number = resultado_issue.get('issue_number')
                    issue_url = resultado_issue.get('issue_url')
                    mensagem_erro += f'Uma <a href="{issue_url}" target="_blank">issue #{issue_number}</a> foi criada automaticamente para investigação.'
                    logger.info(f"Issue #{issue_number} criada para falha de scraping: {url}")
                else:
                    mensagem_erro += 'Tente preencher os campos manualmente.'

                return JsonResponse({
                    'success': False,
                    'error': mensagem_erro,
                    'error_type': 'parsing',
                    'issue_created': bool(resultado_issue and resultado_issue.get('success'))
                }, status=400)

            else:
                # Erro desconhecido
                logger.error(f"Erro desconhecido ao extrair {url}: {error_message}")
                return JsonResponse({
                    'success': False,
                    'error': 'Erro ao processar a página. Tente preencher os campos manualmente.',
                    'error_type': 'unknown',
                    'details': error_message
                }, status=500)

    except Exception as e:
        logger.error(f"Erro inesperado ao extrair informações de {url}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return JsonResponse({
            'error': 'Erro ao processar a página. Tente preencher os campos manualmente.',
            'details': str(e)
        }, status=500)

def gerar_dados_teste_view(request):
    """
    View para gerar dados de teste.
    IMPORTANTE: Acesso público permitido (útil para Render Free sem SSH).
    Acesso via: /gerar-dados-teste/
    """
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

            # Log com email se usuário autenticado, senão "público"
            user_identifier = request.user.email if request.user.is_authenticated else 'acesso público'
            logger.info(f"Dados de teste gerados por {user_identifier}")
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
    grupos_count = Grupo.objects.count()
    membros_count = GrupoMembro.objects.count()

    return render(request, 'presentes/gerar_dados_teste.html', {
        'usuarios_count': usuarios_count,
        'presentes_count': presentes_count,
        'presentes_ativos': presentes_ativos,
        'presentes_comprados': presentes_comprados,
        'grupos_count': grupos_count,
        'membros_count': membros_count,
    })


# =====================================================================
# VIEW DE SETUP (PARA RENDER E OUTRAS PLATAFORMAS SEM SHELL)
# =====================================================================

def setup_grupos_view(request):
    """
    Interface web para executar setup do grupo padrao.
    Util para plataformas como Render onde nao ha acesso SSH.
    IMPORTANTE: Acesso público permitido (útil para Render Free sem SSH).
    """
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
    # Buscar membros de grupos (não apenas grupos) para ter acesso a e_mantenedor
    membros = GrupoMembro.objects.filter(
        usuario=request.user,
        grupo__ativo=True
    ).select_related('grupo').order_by('-grupo__data_criacao')

    grupo_ativo = request.user.grupo_ativo

    # Se usuario nao tem grupos, redirecionar para criar
    if not membros.exists():
        messages.info(request, 'Voce ainda nao faz parte de nenhum grupo. Crie ou junte-se a um!')
        return redirect('criar_grupo')

    context = {
        'grupos': membros,  # Na verdade são GrupoMembro objects
        'grupo_ativo': grupo_ativo,
    }
    return render(request, 'presentes/grupos_lista.html', context)


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

    return render(request, 'presentes/criar_grupo.html', {'form': form})


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
    return render(request, 'presentes/editar_grupo.html', context)


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

    # Construir link de convite usando a URL atual (funciona em qualquer ambiente)
    from django.urls import reverse
    link_convite_path = reverse('convite_grupo', args=[grupo.codigo_convite])
    link_convite = request.build_absolute_uri(link_convite_path)

    context = {
        'grupo': grupo,
        'membros': membros,
        'link_convite': link_convite,
        'e_mantenedor': e_mantenedor,
    }
    return render(request, 'presentes/gerenciar_membros.html', context)


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
def adicionar_membro_view(request, pk):
    """Adiciona um membro ao grupo pelo e-mail (apenas mantenedores)."""
    grupo = get_object_or_404(Grupo, pk=pk)

    e_mantenedor = GrupoMembro.objects.filter(
        grupo=grupo, usuario=request.user, e_mantenedor=True
    ).exists()
    if not e_mantenedor:
        messages.error(request, 'Apenas mantenedores podem adicionar membros.')
        return redirect('grupos_lista')

    if request.method == 'POST':
        email = (request.POST.get('email') or '').strip().lower()
        if not email:
            messages.error(request, 'Informe o e-mail do membro.')
            return redirect('gerenciar_membros', pk=pk)

        usuario = Usuario.objects.filter(email__iexact=email).first()
        if not usuario:
            messages.warning(
                request,
                f'Nenhum usuário cadastrado com o e-mail {email}. '
                f'Envie o link de convite — ao se cadastrar, a pessoa entra direto no grupo.'
            )
            return redirect('gerenciar_membros', pk=pk)

        _, criado = GrupoMembro.objects.get_or_create(
            grupo=grupo, usuario=usuario, defaults={'e_mantenedor': False}
        )
        if not criado:
            messages.info(request, f'{usuario.get_full_name() or email} já é membro do grupo.')
        else:
            if not usuario.grupo_ativo:
                usuario.grupo_ativo = grupo
                usuario.save(update_fields=['grupo_ativo'])
            Notificacao.objects.create(
                grupo=grupo,
                usuario=usuario,
                mensagem=f'👥 Você foi adicionado ao grupo "{grupo.nome}" por {request.user.get_full_name()}.'
            )
            messages.success(request, f'{usuario.get_full_name() or email} adicionado ao grupo!')
            logger.info(f"Usuario {usuario.email} adicionado ao grupo {grupo.id} por {request.user.email}")

    return redirect('gerenciar_membros', pk=pk)


@login_required
def entrar_com_codigo_view(request):
    """Permite ao usuário entrar em um grupo informando o código de convite."""
    if request.method != 'POST':
        return redirect('grupos_lista')

    codigo = (request.POST.get('codigo') or '').strip()
    if not codigo:
        messages.error(request, 'Informe o código de convite.')
        return redirect('grupos_lista')

    # Aceitar tanto o código puro quanto o link completo colado
    if '/convite/' in codigo:
        codigo = codigo.rstrip('/').split('/')[-1]

    if not Grupo.objects.filter(codigo_convite=codigo).exists():
        messages.error(request, 'Código de convite inválido. Confira com quem te convidou.')
        return redirect('grupos_lista')

    return redirect('convite_grupo', codigo=codigo)


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


def servir_foto_usuario_view(request, pk):
    """Serve a foto do usuario a partir do base64 no banco"""
    try:
        usuario = get_object_or_404(Usuario, pk=pk)
        if not usuario.foto_base64:
            return HttpResponse(status=404)
        imagem_data = base64.b64decode(usuario.foto_base64)
        content_type = usuario.foto_tipo or 'image/jpeg'
        return HttpResponse(imagem_data, content_type=content_type)
    except Exception as e:
        logger.error(f"Erro ao servir foto do usuario {pk}: {str(e)}")
        return HttpResponse('Erro ao carregar foto', status=500)


@login_required
def push_subscription_save(request):
    """Salvar push subscription do navegador"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Metodo nao permitido'}, status=405)
    try:
        import json as _json
        data = _json.loads(request.body)
        endpoint = data.get('endpoint')
        keys = data.get('keys', {})
        p256dh = keys.get('p256dh')
        auth = keys.get('auth')
        if not endpoint or not p256dh or not auth:
            return JsonResponse({'error': 'Dados incompletos'}, status=400)
        PushSubscription.objects.update_or_create(
            endpoint=endpoint,
            defaults={'usuario': request.user, 'p256dh': p256dh, 'auth': auth}
        )
        return JsonResponse({'success': True})
    except Exception as e:
        logger.error(f"Erro ao salvar push subscription: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def push_subscription_delete(request):
    """Remover push subscription"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Metodo nao permitido'}, status=405)
    try:
        import json as _json
        data = _json.loads(request.body)
        endpoint = data.get('endpoint')
        if endpoint:
            PushSubscription.objects.filter(usuario=request.user, endpoint=endpoint).delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def vapid_public_key_view(request):
    """Retorna a chave publica VAPID para o frontend"""
    return JsonResponse({'public_key': settings.VAPID_PUBLIC_KEY})
