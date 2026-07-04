"""
Pesquisa periódica de preços (temperatura de preços).

A cada semana o sistema refaz a busca de sugestões/preços de todos os
presentes ativos, alimentando o histórico (PrecoHistorico) usado pelo
indicador de temperatura e pelo gráfico de evolução.

Como o Render Free Tier não possui cron, a pesquisa é disparada de duas formas:
- Automática: middleware verifica a cada request (com throttle de 1h por
  processo) se a última execução tem mais de 7 dias e dispara em background.
- Externa: comando `python manage.py pesquisar_precos` para cron/agendador.
"""
import logging
import threading
import time

from datetime import timedelta

from django.utils import timezone

logger = logging.getLogger(__name__)

INTERVALO_PESQUISA = timedelta(days=7)

_lock = threading.Lock()


def pesquisa_em_atraso():
    """True se nunca houve pesquisa ou a última tem mais de 7 dias."""
    from .models import PesquisaPrecoLog
    ultima = PesquisaPrecoLog.objects.order_by('-data_inicio').first()
    return ultima is None or timezone.now() - ultima.data_inicio >= INTERVALO_PESQUISA


def executar_pesquisa(origem='automatica', log=None):
    """
    Executa a pesquisa de preços para todos os presentes ativos (síncrono).
    Cada presente tem suas sugestões atualizadas e o melhor preço gravado
    no histórico (via IAService._registrar_historico).
    """
    from .models import Presente, PesquisaPrecoLog
    from .services import IAService

    if log is None:
        log = PesquisaPrecoLog.objects.create(origem=origem)

    presentes = Presente.objects.filter(status='ATIVO').select_related('usuario')
    log.total_presentes = presentes.count()
    log.save(update_fields=['total_presentes'])

    logger.info(f"[PESQUISA-PRECOS] Iniciando ({origem}) para {log.total_presentes} presentes")

    sucessos = erros = 0
    for presente in presentes:
        try:
            sucesso, mensagem = IAService.buscar_sugestoes_reais(presente)
            if sucesso:
                sucessos += 1
            else:
                erros += 1
                logger.warning(f"[PESQUISA-PRECOS] Presente {presente.id}: {mensagem}")
        except Exception as e:
            erros += 1
            logger.error(f"[PESQUISA-PRECOS] Erro no presente {presente.id}: {str(e)}")

    log.sucessos = sucessos
    log.erros = erros
    log.data_fim = timezone.now()
    log.save(update_fields=['sucessos', 'erros', 'data_fim'])

    logger.info(f"[PESQUISA-PRECOS] Concluída: {sucessos} sucessos, {erros} erros")
    return log


def disparar_pesquisa_se_necessario():
    """
    Dispara a pesquisa semanal em background se estiver em atraso.
    O log é criado antes da thread iniciar para evitar disparos duplicados.
    Retorna True se uma pesquisa foi disparada.
    """
    from .models import PesquisaPrecoLog

    with _lock:
        if not pesquisa_em_atraso():
            return False
        log = PesquisaPrecoLog.objects.create(origem='automatica')

    thread = threading.Thread(
        target=executar_pesquisa,
        kwargs={'origem': 'automatica', 'log': log},
        daemon=True
    )
    thread.start()
    logger.info("[PESQUISA-PRECOS] Pesquisa semanal automática disparada em background")
    return True


class PesquisaPrecoMiddleware:
    """
    Verifica (no máximo 1x por hora por processo) se a pesquisa semanal de
    preços está em atraso e a dispara em background. Substitui o cron no
    Render Free Tier: roda sempre que houver tráfego na aplicação.
    """
    CHECK_INTERVAL_SEGUNDOS = 3600
    _ultima_checagem = 0.0

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        agora = time.monotonic()
        if agora - PesquisaPrecoMiddleware._ultima_checagem > self.CHECK_INTERVAL_SEGUNDOS:
            PesquisaPrecoMiddleware._ultima_checagem = agora
            try:
                disparar_pesquisa_se_necessario()
            except Exception:
                # Banco indisponível/migração pendente não pode derrubar o request
                logger.exception("[PESQUISA-PRECOS] Erro ao verificar pesquisa semanal")
        return self.get_response(request)
