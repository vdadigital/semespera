import calendar
from datetime import date, datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout, update_session_auth_hash
from django.contrib import messages

from .models import Empresa, PerfilUsuario, Especialidade, Agenda, Paciente, Consulta


# ──────────────────────────────────────────
# HELPER
# ──────────────────────────────────────────

def get_empresa(request):
    try:
        return request.user.perfil.empresa
    except Exception:
        return None


def is_admin(user):
    return user.is_superuser


# ──────────────────────────────────────────
# TELA 1 – AGENDAR DIA
# ──────────────────────────────────────────

@login_required
def agendar_dia(request):
    empresa = get_empresa(request)
    if not empresa:
        return redirect('master_dashboard')

    especialidades = Especialidade.objects.filter(empresa=empresa, ativo=True)
    modal_aberto   = False

    if request.method == 'POST':
        acao = request.POST.get('acao')

        # ── Cadastrar nova especialidade via modal inline
        if acao == 'especialidade':
            nome_esp = request.POST.get('nome_esp', '').strip()
            icone    = request.POST.get('icone', '🩺').strip() or '🩺'
            if nome_esp:
                Especialidade.objects.create(empresa=empresa, nome=nome_esp, icone=icone)
                return redirect('agendar_dia')
            # Se faltar nome, reabre o modal
            modal_aberto = True

        # ── Salvar nova agenda
        elif acao == 'agenda':
            esp_id   = request.POST.get('especialidade_id')
            data_str = request.POST.get('data')
            vagas    = int(request.POST.get('vagas', 0))
            horario  = request.POST.get('horario_inicio') or None

            if esp_id and data_str and vagas > 0:
                especialidade = get_object_or_404(Especialidade, id=esp_id, empresa=empresa)
                data_obj = datetime.strptime(data_str, '%Y-%m-%d').date()
                Agenda.objects.create(
                    empresa=empresa,
                    especialidade=especialidade,
                    data=data_obj,
                    vagas_total=vagas,
                    vagas_restantes=vagas,
                    horario_inicio=horario,
                )
                return redirect('agendar_dia')

    agendas = Agenda.objects.filter(empresa=empresa).order_by('data')

    return render(request, 'consultas/agendar_dia.html', {
        'agendas':       agendas,
        'especialidades': especialidades,
        'active_tab':    'agendar',
        'modal_aberto':  modal_aberto,
    })


@login_required
def excluir_agenda(request, agenda_id):
    empresa = get_empresa(request)
    agenda  = get_object_or_404(Agenda, id=agenda_id, empresa=empresa)
    agenda.delete()
    return redirect('agendar_dia')


# ──────────────────────────────────────────
# TELA 2 – MARCAR CONSULTA
# ──────────────────────────────────────────

@login_required
def marcar_consulta(request):
    empresa = get_empresa(request)
    if not empresa:
        return redirect('master_dashboard')

    especialidades = Especialidade.objects.filter(empresa=empresa, ativo=True)

    if request.method == 'POST':
        agenda_id = request.POST.get('agenda_id')
        nome      = request.POST.get('nome', '').strip()
        telefone  = request.POST.get('telefone', '').strip()

        if not agenda_id or not nome or not telefone:
            return redirect('marcar_consulta')

        agenda = get_object_or_404(Agenda, id=agenda_id, empresa=empresa)

        if agenda.vagas_restantes <= 0:
            return redirect('marcar_consulta')

        # ── BUG CORRIGIDO: sempre cria novo paciente.
        # Telefone NÃO identifica paciente — cada marcação é independente.
        paciente = Paciente.objects.create(
            empresa=empresa,
            nome=nome,
            telefone=telefone,
        )

        ultima = Consulta.objects.filter(agenda=agenda).order_by('-ficha').first()
        ficha  = (ultima.ficha + 1) if ultima else 1

        consulta = Consulta.objects.create(
            paciente=paciente,
            agenda=agenda,
            ficha=ficha,
        )

        agenda.vagas_restantes -= 1
        agenda.save()

        return render(request, 'consultas/sucesso.html', {
            'consulta': consulta,
            'agenda':   agenda,
            'ficha':    ficha,
        })

    # GET – monta calendário
    esp_id          = request.GET.get('especialidade_id')
    especialidade_sel = None
    if esp_id:
        especialidade_sel = especialidades.filter(id=esp_id).first()
    if not especialidade_sel and especialidades.exists():
        especialidade_sel = especialidades.first()

    hoje = date.today()
    ano  = int(request.GET.get('ano', hoje.year))
    mes  = int(request.GET.get('mes', hoje.month))

    agenda_por_dia = {}
    if especialidade_sel:
        for ag in Agenda.objects.filter(
            empresa=empresa,
            especialidade=especialidade_sel,
            data__year=ano,
            data__month=mes,
        ):
            agenda_por_dia[ag.data.day] = ag

    cal          = calendar.monthcalendar(ano, mes)
    mes_anterior = (ano - 1, 12) if mes == 1  else (ano, mes - 1)
    mes_proximo  = (ano + 1,  1) if mes == 12 else (ano, mes + 1)
    nomes_meses  = ['','Janeiro','Fevereiro','Março','Abril','Maio','Junho',
                    'Julho','Agosto','Setembro','Outubro','Novembro','Dezembro']

    return render(request, 'consultas/marcar_consulta.html', {
        'especialidades':   especialidades,
        'especialidade_sel': especialidade_sel,
        'cal':              cal,
        'ano':              ano,
        'mes':              mes,
        'nome_mes':         nomes_meses[mes],
        'agenda_por_dia':   agenda_por_dia,
        'mes_anterior':     mes_anterior,
        'mes_proximo':      mes_proximo,
        'hoje':             hoje,
        'active_tab':       'marcar',
    })


@login_required
def get_agenda_info(request, agenda_id):
    empresa = get_empresa(request)
    agenda  = get_object_or_404(Agenda, id=agenda_id, empresa=empresa)
    return JsonResponse({
        'id':              agenda.id,
        'data':            str(agenda.data),
        'vagas_restantes': agenda.vagas_restantes,
        'especialidade':   agenda.especialidade.nome,
    })


# ──────────────────────────────────────────
# TELA 3 – ATENDIMENTO
# ──────────────────────────────────────────

@login_required
def atendimento(request):
    empresa = get_empresa(request)
    if not empresa:
        return redirect('master_dashboard')

    agendas = Agenda.objects.filter(empresa=empresa).order_by('data')
    return render(request, 'consultas/atendimento_lista.html', {
        'agendas':    agendas,
        'active_tab': 'atendimento',
    })


@login_required
def fila_atendimento(request, agenda_id):
    empresa = get_empresa(request)
    agenda  = get_object_or_404(Agenda, id=agenda_id, empresa=empresa)

    em_atendimento = Consulta.objects.filter(agenda=agenda, status='em_atendimento').first()
    fila           = Consulta.objects.filter(agenda=agenda, status='esperando').order_by('ficha')
    proximo        = fila.first()
    ausentes       = Consulta.objects.filter(agenda=agenda, status='ausente').order_by('ficha')

    return render(request, 'consultas/fila_atendimento.html', {
        'agenda':          agenda,
        'em_atendimento':  em_atendimento,
        'proximo':         proximo,
        'fila':            fila,
        'ausentes':        ausentes,
        'total_agendados': Consulta.objects.filter(agenda=agenda).count(),
        'total_atendidos': Consulta.objects.filter(agenda=agenda, status='atendido').count(),
        'total_faltaram':  Consulta.objects.filter(agenda=agenda, status='faltou').count(),
        'active_tab':      'atendimento',
    })


@login_required
def chamar_proximo(request, agenda_id):
    empresa = get_empresa(request)
    agenda  = get_object_or_404(Agenda, id=agenda_id, empresa=empresa)

    Consulta.objects.filter(agenda=agenda, status='em_atendimento').update(status='atendido')

    proximo = (
        Consulta.objects.filter(agenda=agenda, status='esperando').order_by('ficha').first()
        or Consulta.objects.filter(agenda=agenda, status='ausente').order_by('ficha').first()
    )

    if proximo:
        ultima = Consulta.objects.filter(agenda=agenda).order_by('-ordem_chamada').first()
        proximo.ordem_chamada = (ultima.ordem_chamada + 1) if ultima else 1
        proximo.status = 'em_atendimento'
        proximo.save()

    return redirect('fila_atendimento', agenda_id=agenda.id)


@login_required
def paciente_ausente(request, consulta_id):
    empresa  = get_empresa(request)
    consulta = get_object_or_404(Consulta, id=consulta_id, agenda__empresa=empresa)
    consulta.tentativas += 1
    consulta.status = 'faltou' if consulta.tentativas >= 3 else 'ausente'
    consulta.save()
    return redirect('fila_atendimento', agenda_id=consulta.agenda.id)


@login_required
def finalizar_atendimento(request, consulta_id):
    empresa  = get_empresa(request)
    consulta = get_object_or_404(Consulta, id=consulta_id, agenda__empresa=empresa)
    consulta.status = 'atendido'
    consulta.save()
    return redirect('fila_atendimento', agenda_id=consulta.agenda.id)


@login_required
def chamar_ausente(request, consulta_id):
    empresa  = get_empresa(request)
    consulta = get_object_or_404(Consulta, id=consulta_id, agenda__empresa=empresa)
    if not Consulta.objects.filter(agenda=consulta.agenda, status='em_atendimento').exists():
        consulta.status = 'em_atendimento'
        consulta.save()
    return redirect('fila_atendimento', agenda_id=consulta.agenda.id)


# ──────────────────────────────────────────
# ACOMPANHAR (público)
# ──────────────────────────────────────────

def acompanhar(request, consulta_id):
    consulta       = get_object_or_404(Consulta, id=consulta_id)
    em_atendimento = Consulta.objects.filter(agenda=consulta.agenda, status='em_atendimento').first()
    fila           = Consulta.objects.filter(agenda=consulta.agenda, status='esperando').order_by('ficha')
    pessoas_frente = fila.filter(ficha__lt=consulta.ficha).count()

    return render(request, 'consultas/acompanhar.html', {
        'consulta':       consulta,
        'em_atendimento': em_atendimento,
        'pessoas_frente': pessoas_frente,
    })


# ──────────────────────────────────────────
# LOGOUT
# ──────────────────────────────────────────

@login_required
def logout_view(request):
    logout(request)
    return redirect('/login/')


# ──────────────────────────────────────────
# MENU DO USUÁRIO (perfil, usuários, especialidades, senha)
# ──────────────────────────────────────────

@login_required
def meu_perfil(request):
    return render(request, 'consultas/perfil/meu_perfil.html', {'active_tab': ''})


@login_required
def empresa_usuarios(request):
    empresa = get_empresa(request)
    perfis  = PerfilUsuario.objects.filter(empresa=empresa).select_related('usuario') if empresa else []
    return render(request, 'consultas/perfil/usuarios.html', {
        'perfis':     perfis,
        'active_tab': '',
    })


@login_required
def empresa_especialidades(request):
    empresa       = get_empresa(request)
    especialidades = Especialidade.objects.filter(empresa=empresa).order_by('nome') if empresa else []
    return render(request, 'consultas/perfil/especialidades.html', {
        'especialidades': especialidades,
        'active_tab':     '',
    })


@login_required
def alterar_senha(request):
    erro    = None
    sucesso = False

    if request.method == 'POST':
        senha_atual = request.POST.get('senha_atual', '')
        nova_senha  = request.POST.get('nova_senha', '')
        confirmar   = request.POST.get('confirmar', '')

        if not request.user.check_password(senha_atual):
            erro = 'Senha atual incorreta.'
        elif len(nova_senha) < 6:
            erro = 'A nova senha deve ter no mínimo 6 caracteres.'
        elif nova_senha != confirmar:
            erro = 'As senhas não coincidem.'
        else:
            request.user.set_password(nova_senha)
            request.user.save()
            update_session_auth_hash(request, request.user)  # mantém sessão ativa
            sucesso = True

    return render(request, 'consultas/perfil/alterar_senha.html', {
        'erro':       erro,
        'sucesso':    sucesso,
        'active_tab': '',
    })


# ══════════════════════════════════════════
# ADMINISTRAÇÃO (admin empresa — mantido para compatibilidade)
# ══════════════════════════════════════════

@login_required
def admin_empresas(request):
    if not is_admin(request.user):
        return redirect('agendar_dia')
    empresas = Empresa.objects.all().order_by('nome')
    return render(request, 'consultas/admin/empresas.html', {
        'empresas':   empresas,
        'active_tab': 'admin',
    })


@login_required
def admin_empresa_form(request, empresa_id=None):
    if not is_admin(request.user):
        return redirect('agendar_dia')
    empresa = get_object_or_404(Empresa, id=empresa_id) if empresa_id else None

    if request.method == 'POST':
        nome          = request.POST.get('nome', '').strip()
        nome_fantasia = request.POST.get('nome_fantasia', '').strip()
        telefone      = request.POST.get('telefone', '').strip()
        endereco      = request.POST.get('endereco', '').strip()
        cor_principal = request.POST.get('cor_principal', '#1a3a8f').strip()
        ativo         = request.POST.get('ativo') == 'on'

        if nome:
            if empresa:
                empresa.nome = nome; empresa.nome_fantasia = nome_fantasia
                empresa.telefone = telefone; empresa.endereco = endereco
                empresa.cor_principal = cor_principal; empresa.ativo = ativo
                if 'logo' in request.FILES:
                    empresa.logo = request.FILES['logo']
                empresa.save()
            else:
                empresa = Empresa.objects.create(
                    nome=nome, nome_fantasia=nome_fantasia,
                    telefone=telefone, endereco=endereco,
                    cor_principal=cor_principal, ativo=ativo,
                )
                if 'logo' in request.FILES:
                    empresa.logo = request.FILES['logo']; empresa.save()
            return redirect('admin_empresas')

    return render(request, 'consultas/admin/empresa_form.html', {
        'empresa': empresa, 'active_tab': 'admin',
    })


@login_required
def admin_excluir_empresa(request, empresa_id):
    if not is_admin(request.user):
        return redirect('agendar_dia')
    get_object_or_404(Empresa, id=empresa_id).delete()
    return redirect('admin_empresas')


@login_required
def admin_especialidades(request):
    empresa = get_empresa(request)
    if not empresa and not is_admin(request.user):
        return redirect('agendar_dia')

    if is_admin(request.user):
        especialidades = Especialidade.objects.all().order_by('empresa__nome', 'nome')
        empresas       = Empresa.objects.filter(ativo=True)
    else:
        especialidades = Especialidade.objects.filter(empresa=empresa).order_by('nome')
        empresas       = [empresa]

    if request.method == 'POST':
        nome   = request.POST.get('nome', '').strip()
        icone  = request.POST.get('icone', '🩺').strip()
        emp_id = request.POST.get('empresa_id')
        esp_id = request.POST.get('especialidade_id')

        if nome:
            emp = get_object_or_404(Empresa, id=emp_id) if is_admin(request.user) else empresa
            if esp_id:
                esp = get_object_or_404(Especialidade, id=esp_id, empresa=emp)
                esp.nome = nome; esp.icone = icone; esp.save()
            else:
                Especialidade.objects.create(empresa=emp, nome=nome, icone=icone)
            return redirect('admin_especialidades')

    return render(request, 'consultas/admin/especialidades.html', {
        'especialidades': especialidades,
        'empresas':       empresas,
        'empresa_atual':  empresa,
        'active_tab':     'admin',
        'is_admin':       is_admin(request.user),
    })


@login_required
def admin_excluir_especialidade(request, esp_id):
    empresa = get_empresa(request)
    esp = (get_object_or_404(Especialidade, id=esp_id) if is_admin(request.user)
           else get_object_or_404(Especialidade, id=esp_id, empresa=empresa))
    esp.delete()
    return redirect('admin_especialidades')


@login_required
def admin_usuarios(request):
    empresa = get_empresa(request)
    if not empresa and not is_admin(request.user):
        return redirect('agendar_dia')

    from django.contrib.auth.models import User

    if is_admin(request.user):
        perfis   = PerfilUsuario.objects.select_related('usuario', 'empresa').order_by('empresa__nome', 'usuario__username')
        empresas = Empresa.objects.filter(ativo=True)
    else:
        perfis   = PerfilUsuario.objects.filter(empresa=empresa).select_related('usuario')
        empresas = [empresa]

    erro = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        senha    = request.POST.get('senha', '').strip()
        emp_id   = request.POST.get('empresa_id')

        if username and senha:
            if User.objects.filter(username=username).exists():
                erro = f'Usuário "{username}" já existe.'
            else:
                emp = get_object_or_404(Empresa, id=emp_id) if is_admin(request.user) else empresa
                novo = User.objects.create_user(username=username, password=senha)
                PerfilUsuario.objects.create(usuario=novo, empresa=emp)
                return redirect('admin_usuarios')

    return render(request, 'consultas/admin/usuarios.html', {
        'perfis':        perfis,
        'empresas':      empresas,
        'empresa_atual': empresa,
        'active_tab':    'admin',
        'is_admin':      is_admin(request.user),
        'erro':          erro,
    })


@login_required
def admin_excluir_usuario(request, perfil_id):
    empresa = get_empresa(request)
    perfil  = (get_object_or_404(PerfilUsuario, id=perfil_id) if is_admin(request.user)
               else get_object_or_404(PerfilUsuario, id=perfil_id, empresa=empresa))
    user = perfil.usuario
    perfil.delete()
    user.delete()
    return redirect('admin_usuarios')
