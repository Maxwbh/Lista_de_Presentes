"""
Custom error handlers para debugging em produção
"""
import logging
import traceback
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

logger = logging.getLogger(__name__)


def handler500(request):
    """
    Handler customizado para erro 500 que loga detalhes do erro
    """
    # Capturar informações do erro
    import sys
    exc_type, exc_value, exc_traceback = sys.exc_info()

    # Logar erro completo
    if exc_type:
        error_message = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        logger.error(f"500 Internal Server Error: {error_message}")
        logger.error(f"Request path: {request.path}")
        logger.error(f"Request method: {request.method}")
        logger.error(f"User: {request.user if hasattr(request, 'user') else 'Anonymous'}")

    # Retornar página de erro simples
    return render(request, '500.html', status=500)


def handler404(request, exception):
    """
    Handler customizado para erro 404
    """
    logger.warning(f"404 Not Found: {request.path}")
    return render(request, '404.html', status=404)


def handler403(request, exception):
    """
    Handler customizado para erro 403
    """
    logger.warning(f"403 Forbidden: {request.path}")
    return render(request, '403.html', status=403)


def handler400(request, exception):
    """
    Handler customizado para erro 400
    """
    logger.warning(f"400 Bad Request: {request.path}")
    return render(request, '400.html', status=400)
