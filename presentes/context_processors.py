"""
Context processors para disponibilizar dados em todos os templates.
"""
from .models import GrupoMembro

try:
    from version import __version__, __build__, __commit__
except ImportError:
    __version__ = "1.0.0"
    __build__ = 0
    __commit__ = ""


def grupos_usuario(request):
    """
    Disponibiliza os grupos do usuário e o grupo ativo em todos os templates.
    """
    if request.user.is_authenticated:
        # Buscar grupos do usuário
        user_grupos = GrupoMembro.objects.filter(
            usuario=request.user,
            grupo__ativo=True
        ).select_related('grupo').order_by('grupo__nome')

        return {
            'user_grupos': user_grupos,
            'grupo_ativo': request.user.grupo_ativo,
        }

    return {
        'user_grupos': [],
        'grupo_ativo': None,
    }


def app_version(request):
    """
    Disponibiliza a versão da aplicação em todos os templates.
    """
    return {
        'app_version': __version__,
        'app_build': __build__,
        'app_commit': __commit__,
    }
