"""
views_master.py — Painel Master do Sem Espera.
Acessível apenas por superusuários.
Completamente separado do painel das empresas.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Count

from .models import Empresa, PerfilUsuario, Especialidade, Consulta, Paciente, Agenda
from .decorators import master_required


# ──────────────────────────────────────────
# DASHBOARD
# ──────────────────────────────────────────

@master_required
def master_dashboard(request):
    total_empresas   = Empresa.objects.count()
    ativas           = Empresa.objects.filter(ativo=True).count()
    inativas         = Empresa.objects.filter(ativo=False).count()
    total_usuarios   = PerfilUsuario.objects.count()
    total_consultas  = Consulta.objects.count()
    total_pacientes  = Paciente.objects.count()
    total_agendas    = Agenda.objects.count()

    empresas_resumo = Empresa.objects.annotate(
        num_usuarios=Count('usuarios', distinct=True),
        num_especialidades=Count('especialidades', distinct=True),
        num_consultas=Count('agendas__consulta', distinct=True),
    ).order_by('nome')

    return render(request, 'consultas/master/dashboard.html', {
        'active_master': 'dashboard',
        'total_empresas': total_empresas,
        'ativas': ativas,
        'inativas': inativas,
        'total_usuarios': total_usuarios,
        'total_consultas': total_consultas,
        'total_pacientes': total_pacientes,
        'total_agendas': total_agendas,
        'empresas_resumo': empresas_resumo,
    })


# ──────────────────────────────────────────
# EMPRESAS
# ──────────────────────────────────────────

@master_required
def master_empresas(request):
    empresas = Empresa.objects.annotate(
        num_usuarios=Count('usuarios', distinct=True),
        num_especialidades=Count('especialidades', distinct=True),
    ).order_by('nome')

    return render(request, 'consultas/master/empresas.html', {
        'active_master': 'empresas',
        'empresas': empresas,
    })


@master_required
def master_empresa_form(request, empresa_id=None):
    empresa = get_object_or_404(Empresa, id=empresa_id) if empresa_id else None

    if request.method == 'POST':
        nome          = request.POST.get('nome', '').strip()
        nome_fantasia = request.POST.get('nome_fantasia', '').strip()
        telefone      = request.POST.get('telefone', '').strip()
        endereco      = request.POST.get('endereco', '').strip()
        cidade        = request.POST.get('cidade', '').strip()
        cor_principal = request.POST.get('cor_principal', '#1a3a8f').strip()
        ativo         = request.POST.get('ativo') == 'on'

        if not nome:
            messages.error(request, 'O nome da empresa é obrigatório.')
        else:
            if empresa:
                empresa.nome          = nome
                empresa.nome_fantasia = nome_fantasia
                empresa.telefone      = telefone
                empresa.endereco      = endereco
                empresa.cidade        = cidade
                empresa.cor_principal = cor_principal
                empresa.ativo         = ativo
                if 'logo' in request.FILES:
                    empresa.logo = request.FILES['logo']
                empresa.save()
                messages.success(request, f'Empresa "{empresa}" atualizada com sucesso.')
            else:
                empresa = Empresa(
                    nome=nome,
                    nome_fantasia=nome_fantasia,
                    telefone=telefone,
                    endereco=endereco,
                    cidade=cidade,
                    cor_principal=cor_principal,
                    ativo=ativo,
                )
                if 'logo' in request.FILES:
                    empresa.logo = request.FILES['logo']
                empresa.save()
                messages.success(request, f'Empresa "{empresa}" cadastrada com sucesso.')
            return redirect('master_empresas')

    return render(request, 'consultas/master/empresa_form.html', {
        'active_master': 'empresas',
        'empresa': empresa,
    })


@master_required
def master_empresa_ativar(request, empresa_id):
    empresa = get_object_or_404(Empresa, id=empresa_id)
    empresa.ativo = True
    empresa.save()
    messages.success(request, f'Empresa "{empresa}" ativada.')
    return redirect('master_empresas')


@master_required
def master_empresa_desativar(request, empresa_id):
    empresa = get_object_or_404(Empresa, id=empresa_id)
    empresa.ativo = False
    empresa.save()
    messages.success(request, f'Empresa "{empresa}" desativada.')
    return redirect('master_empresas')


@master_required
def master_empresa_excluir(request, empresa_id):
    empresa = get_object_or_404(Empresa, id=empresa_id)
    if request.method == 'POST':
        nome = str(empresa)
        empresa.delete()
        messages.success(request, f'Empresa "{nome}" excluída.')
        return redirect('master_empresas')
    return render(request, 'consultas/master/confirmar_exclusao.html', {
        'active_master': 'empresas',
        'objeto': empresa,
        'tipo': 'empresa',
        'voltar_url': 'master_empresas',
    })


# ──────────────────────────────────────────
# USUÁRIOS
# ──────────────────────────────────────────

@master_required
def master_usuarios(request):
    perfis = PerfilUsuario.objects.select_related('usuario', 'empresa').order_by(
        'empresa__nome', 'usuario__username'
    )
    empresas = Empresa.objects.filter(ativo=True).order_by('nome')
    erro = None

    if request.method == 'POST':
        acao = request.POST.get('acao')

        if acao == 'criar':
            username  = request.POST.get('username', '').strip()
            senha     = request.POST.get('senha', '').strip()
            emp_id    = request.POST.get('empresa_id')

            if not username or not senha or not emp_id:
                erro = 'Preencha todos os campos.'
            elif User.objects.filter(username=username).exists():
                erro = f'Usuário "{username}" já existe.'
            else:
                emp = get_object_or_404(Empresa, id=emp_id)
                novo = User.objects.create_user(username=username, password=senha)
                PerfilUsuario.objects.create(usuario=novo, empresa=emp)
                messages.success(request, f'Usuário "{username}" criado para {emp}.')
                return redirect('master_usuarios')

    return render(request, 'consultas/master/usuarios.html', {
        'active_master': 'usuarios',
        'perfis': perfis,
        'empresas': empresas,
        'erro': erro,
    })


@master_required
def master_usuario_editar(request, perfil_id):
    perfil   = get_object_or_404(PerfilUsuario, id=perfil_id)
    empresas = Empresa.objects.filter(ativo=True).order_by('nome')

    if request.method == 'POST':
        emp_id = request.POST.get('empresa_id')
        if emp_id:
            perfil.empresa = get_object_or_404(Empresa, id=emp_id)
            perfil.save()
            messages.success(request, f'Usuário "{perfil.usuario.username}" atualizado.')
            return redirect('master_usuarios')

    return render(request, 'consultas/master/usuario_editar.html', {
        'active_master': 'usuarios',
        'perfil': perfil,
        'empresas': empresas,
    })


@master_required
def master_usuario_resetar_senha(request, perfil_id):
    perfil = get_object_or_404(PerfilUsuario, id=perfil_id)

    if request.method == 'POST':
        nova_senha = request.POST.get('nova_senha', '').strip()
        confirmar  = request.POST.get('confirmar', '').strip()

        if not nova_senha:
            messages.error(request, 'Informe a nova senha.')
        elif nova_senha != confirmar:
            messages.error(request, 'As senhas não coincidem.')
        elif len(nova_senha) < 6:
            messages.error(request, 'A senha deve ter no mínimo 6 caracteres.')
        else:
            perfil.usuario.set_password(nova_senha)
            perfil.usuario.save()
            messages.success(request, f'Senha de "{perfil.usuario.username}" redefinida.')
            return redirect('master_usuarios')

    return render(request, 'consultas/master/usuario_resetar_senha.html', {
        'active_master': 'usuarios',
        'perfil': perfil,
    })


@master_required
def master_usuario_bloquear(request, perfil_id):
    perfil = get_object_or_404(PerfilUsuario, id=perfil_id)
    perfil.usuario.is_active = False
    perfil.usuario.save()
    messages.success(request, f'Usuário "{perfil.usuario.username}" bloqueado.')
    return redirect('master_usuarios')


@master_required
def master_usuario_desbloquear(request, perfil_id):
    perfil = get_object_or_404(PerfilUsuario, id=perfil_id)
    perfil.usuario.is_active = True
    perfil.usuario.save()
    messages.success(request, f'Usuário "{perfil.usuario.username}" desbloqueado.')
    return redirect('master_usuarios')


@master_required
def master_usuario_excluir(request, perfil_id):
    perfil = get_object_or_404(PerfilUsuario, id=perfil_id)
    if request.method == 'POST':
        username = perfil.usuario.username
        user = perfil.usuario
        perfil.delete()
        user.delete()
        messages.success(request, f'Usuário "{username}" excluído.')
        return redirect('master_usuarios')
    return render(request, 'consultas/master/confirmar_exclusao.html', {
        'active_master': 'usuarios',
        'objeto': perfil,
        'tipo': 'usuário',
        'voltar_url': 'master_usuarios',
    })


# ──────────────────────────────────────────
# ESPECIALIDADES (visão master)
# ──────────────────────────────────────────

@master_required
def master_especialidades(request):
    empresas = Empresa.objects.annotate(
        num_especialidades=Count('especialidades', distinct=True)
    ).order_by('nome')

    especialidades = Especialidade.objects.select_related('empresa').order_by(
        'empresa__nome', 'nome'
    )

    return render(request, 'consultas/master/especialidades.html', {
        'active_master': 'especialidades',
        'empresas': empresas,
        'especialidades': especialidades,
    })


# ──────────────────────────────────────────
# ESTATÍSTICAS
# ──────────────────────────────────────────

@master_required
def master_estatisticas(request):
    from django.db.models import Q

    empresas_stats = Empresa.objects.annotate(
        num_usuarios=Count('usuarios', distinct=True),
        num_especialidades=Count('especialidades', distinct=True),
        num_pacientes=Count('pacientes', distinct=True),
        num_consultas=Count('agendas__consulta', distinct=True),
    ).order_by('-num_consultas')

    total_consultas_status = {
        'esperando':      Consulta.objects.filter(status='esperando').count(),
        'em_atendimento': Consulta.objects.filter(status='em_atendimento').count(),
        'atendido':       Consulta.objects.filter(status='atendido').count(),
        'ausente':        Consulta.objects.filter(status='ausente').count(),
        'faltou':         Consulta.objects.filter(status='faltou').count(),
    }

    return render(request, 'consultas/master/estatisticas.html', {
        'active_master': 'estatisticas',
        'empresas_stats': empresas_stats,
        'total_consultas_status': total_consultas_status,
        'total_empresas':   Empresa.objects.count(),
        'ativas':           Empresa.objects.filter(ativo=True).count(),
        'inativas':         Empresa.objects.filter(ativo=False).count(),
        'total_usuarios':   PerfilUsuario.objects.count(),
        'total_consultas':  Consulta.objects.count(),
        'total_pacientes':  Paciente.objects.count(),
    })
