"""
Context processors para disponibilizar dados em todos os templates.
"""
from .models import GrupoMembro


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
