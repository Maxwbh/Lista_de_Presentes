"""
Registro de quando o servidor acorda e de quantos acessos ha por hora.

No Render Free o servidor dorme depois de 15 minutos sem trafego. Com estes
dados da para descobrir os horarios em que os usuarios realmente usam o
sistema e manter o servidor acordado (ping do keep-alive) so nesses periodos.
"""
import logging
from datetime import timedelta
from zoneinfo import ZoneInfo

from django.conf import settings
from django.db import IntegrityError
from django.db.models import F
from django.utils import timezone

logger = logging.getLogger(__name__)

# Com preload_app no gunicorn o modulo e importado uma vez no processo mestre:
# este horario muda so quando o servidor sobe de novo (ex.: ao acordar)
PROCESSO_INICIADO_EM = timezone.now()

# Requisicoes que nao representam uso do sistema por uma pessoa
CAMINHOS_IGNORADOS = (
    '/static/', '/media/', '/health/', '/favicon', '/sw.js', '/serviceworker.js',
    '/manifest.json', '/api/notificacoes/', '/api/push/', '/api/cron/',
)
USER_AGENTS_MONITOR = (
    'render/', 'github', 'uptimerobot', 'cron-job', 'curl/', 'wget/',
    'python-requests', 'go-http-client', 'bot', 'spider', 'crawler',
)


def eh_monitor(request):
    user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
    return not user_agent or any(m in user_agent for m in USER_AGENTS_MONITOR)


def _registrar_despertar(request, monitor):
    from .models import DespertarServidor

    DespertarServidor.objects.get_or_create(
        iniciado_em=PROCESSO_INICIADO_EM,
        defaults={
            'primeiro_acesso_em': timezone.now(),
            'caminho': request.path[:300],
            'origem': 'MONITOR' if monitor else 'USUARIO',
            'user_agent': request.META.get('HTTP_USER_AGENT', '')[:200],
        },
    )


def _contar_acesso():
    from .models import AcessoHora

    agora = timezone.localtime()
    filtro = {'data': agora.date(), 'hora': agora.hour}
    if AcessoHora.objects.filter(**filtro).update(acessos=F('acessos') + 1):
        return
    try:
        AcessoHora.objects.create(acessos=1, **filtro)
    except IntegrityError:
        # Outra requisicao criou a linha ao mesmo tempo
        AcessoHora.objects.filter(**filtro).update(acessos=F('acessos') + 1)


class RegistroAcessoMiddleware:
    """Registra o despertar do servidor e conta os acessos de pessoas por hora."""
    _despertar_registrado = False

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        # O health check do proprio Render chega logo que o servidor sobe:
        # nao foi ele que acordou o servidor
        if not user_agent.startswith('Render/'):
            try:
                monitor = eh_monitor(request)
                if not RegistroAcessoMiddleware._despertar_registrado:
                    RegistroAcessoMiddleware._despertar_registrado = True
                    _registrar_despertar(request, monitor)
                if not monitor and not request.path.startswith(CAMINHOS_IGNORADOS):
                    _contar_acesso()
            except Exception:
                # Banco indisponivel/migracao pendente nao pode derrubar o request
                logger.exception("[ACESSOS] Erro ao registrar acesso")
        return self.get_response(request)


def _faixas(horas):
    """[7, 8, 9, 13, 14] -> [(7, 9), (13, 14)]"""
    faixas = []
    for hora in sorted(set(horas)):
        if faixas and hora == faixas[-1][1] + 1:
            faixas[-1] = (faixas[-1][0], hora)
        else:
            faixas.append((hora, hora))
    return faixas


def _crons_utc(faixas_locais, intervalo_minutos=14):
    """Converte faixas de horas locais em linhas cron UTC (o GitHub Actions usa UTC)."""
    agora_local = timezone.now().astimezone(ZoneInfo(settings.TIME_ZONE))
    deslocamento = int(agora_local.utcoffset().total_seconds() // 3600)

    horas_utc = sorted({(h - deslocamento) % 24
                        for inicio, fim in faixas_locais for h in range(inicio, fim + 1)})
    crons = []
    for inicio, fim in _faixas(horas_utc):
        horas = str(inicio) if inicio == fim else f'{inicio}-{fim}'
        crons.append(f'*/{intervalo_minutos} {horas} * * *')
    return crons


def resumo_acessos(dias=30, limite_percentual=5.0, horas_antes=1):
    """
    Resumo dos acessos e despertares dos ultimos `dias`.

    Horario de pico: hora com pelo menos `limite_percentual`% dos acessos.
    As faixas sugeridas comecam `horas_antes` antes do pico, para o servidor
    ja estar acordado quando as pessoas chegarem.
    """
    from .models import AcessoHora, DespertarServidor

    inicio = timezone.localdate() - timedelta(days=dias)
    por_hora = [0] * 24
    por_dia_semana = {d: [0] * 24 for d in range(7)}
    for registro in AcessoHora.objects.filter(data__gte=inicio):
        por_hora[registro.hora] += registro.acessos
        por_dia_semana[registro.data.weekday()][registro.hora] += registro.acessos

    total = sum(por_hora)
    horas_pico = [h for h, n in enumerate(por_hora) if total and n * 100 / total >= limite_percentual]
    horas_manter = {(h - d) % 24 for h in horas_pico for d in range(horas_antes + 1)}
    faixas = _faixas(horas_manter)

    despertares = DespertarServidor.objects.filter(iniciado_em__date__gte=inicio)
    despertares_por_hora = [0] * 24
    for despertar in despertares:
        despertares_por_hora[timezone.localtime(despertar.primeiro_acesso_em).hour] += 1

    return {
        'periodo_dias': dias,
        'total_acessos': total,
        'acessos_por_hora': por_hora,
        'acessos_por_dia_semana': {
            nome: por_dia_semana[d]
            for d, nome in enumerate(['seg', 'ter', 'qua', 'qui', 'sex', 'sab', 'dom'])
        },
        'horas_pico': horas_pico,
        'faixas_sugeridas_local': [f'{i:02d}:00-{f:02d}:59' for i, f in faixas],
        'cron_keep_alive_utc': _crons_utc(faixas),
        'despertares': {
            'total': despertares.count(),
            'por_usuario': despertares.filter(origem='USUARIO').count(),
            'por_monitor': despertares.filter(origem='MONITOR').count(),
            'por_hora': despertares_por_hora,
        },
    }
