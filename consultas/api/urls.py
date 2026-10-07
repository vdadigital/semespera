from django.urls import path
from . import views

urlpatterns = [
    # ── Auth paciente (Flutter)
    path('auth/login-paciente/',    views.api_login_paciente,    name='api_login_paciente'),
    path('auth/cadastro-paciente/', views.api_cadastro_paciente, name='api_cadastro_paciente'),
    path('auth/logout-paciente/',   views.api_logout_paciente,   name='api_logout_paciente'),

    # ── Auth geral (mantido para compatibilidade)
    path('auth/login/',  views.api_login,  name='api_login'),
    path('auth/logout/', views.api_logout, name='api_logout'),

    # ── Dados públicos
    path('empresas/',       views.api_empresas,       name='api_empresas'),
    path('especialidades/', views.api_especialidades, name='api_especialidades'),
    path('agendas/',        views.api_agendas,        name='api_agendas'),

    # ── Consultas
    path('consultas/',                   views.api_marcar_consulta,  name='api_marcar_consulta'),
    path('consultas/<int:consulta_id>/', views.api_consulta_detalhe, name='api_consulta_detalhe'),

    # ── Fila
    path('fila/<int:agenda_id>/', views.api_fila, name='api_fila'),

    # ── Paciente logado
    path('perfil-paciente/',   views.api_perfil_paciente,  name='api_perfil_paciente'),
    path('minhas-consultas/',  views.api_minhas_consultas, name='api_minhas_consultas'),
    path('consultas/<int:consulta_id>/cancelar/', views.api_cancelar_consulta, name='api_cancelar_consulta'),

    # ── Busca por especialidade
    path('busca/', views.api_busca, name='api_busca'),
    path('cidades/', views.api_cidades, name='api_cidades'),
]
