from django.urls import path
from . import views
from . import views_master

urlpatterns = [
    # ── Tela 1 – Agendar Dia
    path('', views.agendar_dia, name='agendar_dia'),
    path('excluir-agenda/<int:agenda_id>/', views.excluir_agenda, name='excluir_agenda'),

    # ── Tela 2 – Marcar Consulta
    path('marcar/', views.marcar_consulta, name='marcar_consulta'),
    path('agenda-info/<int:agenda_id>/', views.get_agenda_info, name='get_agenda_info'),

    # ── Tela 3 – Atendimento
    path('atendimento/', views.atendimento, name='atendimento'),
    path('atendimento/<int:agenda_id>/', views.fila_atendimento, name='fila_atendimento'),
    path('chamar-proximo/<int:agenda_id>/', views.chamar_proximo, name='chamar_proximo'),
    path('paciente-ausente/<int:consulta_id>/', views.paciente_ausente, name='paciente_ausente'),
    path('finalizar/<int:consulta_id>/', views.finalizar_atendimento, name='finalizar_atendimento'),
    path('chamar-ausente/<int:consulta_id>/', views.chamar_ausente, name='chamar_ausente'),

    # ── Acompanhar (público)
    path('acompanhar/<int:consulta_id>/', views.acompanhar, name='acompanhar'),

    # ── Logout
    path('logout/', views.logout_view, name='logout'),

    # ── Menu do usuário
    path('perfil/', views.meu_perfil, name='meu_perfil'),
    path('perfil/usuarios/', views.empresa_usuarios, name='empresa_usuarios'),
    path('perfil/especialidades/', views.empresa_especialidades, name='empresa_especialidades'),
    path('perfil/alterar-senha/', views.alterar_senha, name='alterar_senha'),

    # ── Admin empresa (mantido)
    path('admin-se/empresas/', views.admin_empresas, name='admin_empresas'),
    path('admin-se/empresas/nova/', views.admin_empresa_form, name='admin_empresa_nova'),
    path('admin-se/empresas/<int:empresa_id>/editar/', views.admin_empresa_form, name='admin_empresa_editar'),
    path('admin-se/empresas/<int:empresa_id>/excluir/', views.admin_excluir_empresa, name='admin_excluir_empresa'),
    path('admin-se/especialidades/', views.admin_especialidades, name='admin_especialidades'),
    path('admin-se/especialidades/<int:esp_id>/excluir/', views.admin_excluir_especialidade, name='admin_excluir_especialidade'),
    path('admin-se/usuarios/', views.admin_usuarios, name='admin_usuarios'),
    path('admin-se/usuarios/<int:perfil_id>/excluir/', views.admin_excluir_usuario, name='admin_excluir_usuario'),

    # ══════════════════════════════════════
    # PAINEL MASTER (somente superusuário)
    # ══════════════════════════════════════
    path('master/', views_master.master_dashboard, name='master_dashboard'),
    path('master/empresas/', views_master.master_empresas, name='master_empresas'),
    path('master/empresas/nova/', views_master.master_empresa_form, name='master_empresa_nova'),
    path('master/empresas/<int:empresa_id>/editar/', views_master.master_empresa_form, name='master_empresa_editar'),
    path('master/empresas/<int:empresa_id>/ativar/', views_master.master_empresa_ativar, name='master_empresa_ativar'),
    path('master/empresas/<int:empresa_id>/desativar/', views_master.master_empresa_desativar, name='master_empresa_desativar'),
    path('master/empresas/<int:empresa_id>/excluir/', views_master.master_empresa_excluir, name='master_empresa_excluir'),
    path('master/usuarios/', views_master.master_usuarios, name='master_usuarios'),
    path('master/usuarios/<int:perfil_id>/editar/', views_master.master_usuario_editar, name='master_usuario_editar'),
    path('master/usuarios/<int:perfil_id>/resetar-senha/', views_master.master_usuario_resetar_senha, name='master_usuario_resetar_senha'),
    path('master/usuarios/<int:perfil_id>/bloquear/', views_master.master_usuario_bloquear, name='master_usuario_bloquear'),
    path('master/usuarios/<int:perfil_id>/desbloquear/', views_master.master_usuario_desbloquear, name='master_usuario_desbloquear'),
    path('master/usuarios/<int:perfil_id>/excluir/', views_master.master_usuario_excluir, name='master_usuario_excluir'),
    path('master/especialidades/', views_master.master_especialidades, name='master_especialidades'),
    path('master/estatisticas/', views_master.master_estatisticas, name='master_estatisticas'),
]
