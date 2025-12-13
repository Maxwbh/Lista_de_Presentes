from django.urls import path
from . import views

urlpatterns = [
    # Health check
    path('health/', views.health_check, name='health_check'),

    # Autenticação
    path('', views.login_view, name='login'),
    path('registro/', views.registro_view, name='registro'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('esqueceu-senha/', views.esqueceu_senha_view, name='esqueceu_senha'),
    path('redefinir-senha/<str:token>/', views.redefinir_senha_view, name='redefinir_senha'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # Meus presentes
    path('meus-presentes/', views.meus_presentes_view, name='meus_presentes'),
    path('adicionar-presente/', views.adicionar_presente_view, name='adicionar_presente'),
    path('editar-presente/<int:pk>/', views.editar_presente_view, name='editar_presente'),
    path('deletar-presente/<int:pk>/', views.deletar_presente_view, name='deletar_presente'),
    path('presente/<int:pk>/imagem/', views.servir_imagem_view, name='servir_imagem'),
    path('buscar-sugestoes/<int:pk>/', views.buscar_sugestoes_ia_view, name='buscar_sugestoes'),
    path('ver-sugestoes/<int:pk>/', views.ver_sugestoes_view, name='ver_sugestoes'),
    path('atualizar-todos-precos/', views.atualizar_todos_precos_view, name='atualizar_todos_precos'),
    
    # Presentes de outros usuários
    path('usuarios/', views.lista_usuarios_view, name='lista_usuarios'),
    path('presentes-usuario/<int:user_id>/', views.presentes_usuario_view, name='presentes_usuario'),
    path('marcar-comprado/<int:pk>/', views.marcar_comprado_view, name='marcar_comprado'),
    
    # Notificações
    path('notificacoes/', views.notificacoes_view, name='notificacoes'),
    path('api/notificacoes/', views.notificacoes_nao_lidas_json, name='notificacoes_json'),

    # Dados de teste (apenas superusuários)
    path('gerar-dados-teste/', views.gerar_dados_teste_view, name='gerar_dados_teste'),

    # Setup de Grupos (para Render e outras plataformas)
    path('setup/', views.setup_grupos_view, name='setup_grupos'),

    # API para extrair informações de produto via URL
    path('api/extrair-info-produto/', views.extrair_info_produto_view, name='extrair_info_produto'),

    # Grupos
    path('grupos/', views.grupos_lista_view, name='grupos_lista'),
    path('grupos/criar/', views.criar_grupo_view, name='criar_grupo'),
    path('grupos/editar/<int:pk>/', views.editar_grupo_view, name='editar_grupo'),
    path('grupos/ativar/<int:pk>/', views.ativar_grupo_view, name='ativar_grupo'),
    path('grupos/<int:pk>/membros/', views.gerenciar_membros_view, name='gerenciar_membros'),
    path('grupos/<int:pk>/membros/remover/<int:user_id>/', views.remover_membro_view, name='remover_membro'),
    path('grupos/<int:pk>/membros/toggle-mantenedor/<int:user_id>/', views.toggle_mantenedor_view, name='toggle_mantenedor'),
    path('grupos/<int:pk>/toggle-ativo/', views.toggle_ativo_grupo_view, name='toggle_ativo_grupo'),
    path('grupos/<int:pk>/sair/', views.sair_grupo_view, name='sair_grupo'),
    path('grupos/convite/<str:codigo>/', views.convite_grupo_view, name='convite_grupo'),
    path('grupo/<int:pk>/imagem/', views.servir_imagem_grupo_view, name='servir_imagem_grupo'),
]
