"""
api/views.py — API REST do Sem Espera.
Separação clara: atendente (sistema web) ≠ paciente (app Flutter).
"""

from datetime import date
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token

from consultas.models import (
    Empresa, Especialidade, Agenda,
    Paciente, Consulta, PacienteConta
)


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def _is_paciente(user):
    """Retorna True se o User tem conta de paciente (não é atendente)."""
    return hasattr(user, 'paciente_conta')


def _is_atendente(user):
    """Retorna True se o User tem perfil de atendente."""
    return hasattr(user, 'perfil')


# ─────────────────────────────────────────────
# AUTH — LOGIN PACIENTE
# ─────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([AllowAny])
def api_login_paciente(request):
    """
    POST /api/auth/login-paciente/
    Body: { "username": "...", "password": "..." }

    Aceita SOMENTE contas de paciente.
    Atendentes são recusados com erro claro.
    """
    username = request.data.get('username', '').strip()
    password = request.data.get('password', '').strip()

    if not username or not password:
        return Response(
            {'erro': 'Informe usuário e senha.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = authenticate(username=username, password=password)

    if not user:
        return Response(
            {'erro': 'Usuário ou senha incorretos.'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    if not user.is_active:
        return Response(
            {'erro': 'Conta bloqueada. Entre em contato com a clínica.'},
            status=status.HTTP_403_FORBIDDEN
        )

    # Bloqueia atendentes — eles usam o sistema web
    if _is_atendente(user) and not _is_paciente(user):
        return Response(
            {'erro': 'Esta conta é de atendente. Use o sistema web.'},
            status=status.HTTP_403_FORBIDDEN
        )

    # Exige que seja conta de paciente
    if not _is_paciente(user):
        return Response(
            {'erro': 'Conta sem perfil de paciente. Cadastre-se primeiro.'},
            status=status.HTTP_403_FORBIDDEN
        )

    token, _ = Token.objects.get_or_create(user=user)
    conta = user.paciente_conta

    return Response({
        'token': token.key,
        'username': user.username,
        'tipo': 'paciente',
        'paciente_id': conta.paciente.id if conta.paciente else None,
        'paciente_nome': conta.paciente.nome if conta.paciente else user.username,
        'telefone': conta.telefone,
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def api_cadastro_paciente(request):
    """
    POST /api/auth/cadastro-paciente/
    Body: { "username": "...", "password": "...", "nome": "...", "telefone": "..." }

    Cria User + PacienteConta + Paciente permanente.
    O Paciente é criado junto e fica vinculado à conta para sempre.
    """
    username = request.data.get('username', '').strip()
    password = request.data.get('password', '').strip()
    nome     = request.data.get('nome', '').strip()
    telefone = request.data.get('telefone', '').strip()

    if not username or not password or not nome or not telefone:
        return Response(
            {'erro': 'Preencha todos os campos: username, password, nome, telefone.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if len(password) < 6:
        return Response(
            {'erro': 'A senha deve ter no mínimo 6 caracteres.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if User.objects.filter(username=username).exists():
        return Response(
            {'erro': f'Usuário "{username}" já existe. Escolha outro.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    with transaction.atomic():
        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=nome,
        )
        # Cria Paciente permanente vinculado a esta conta.
        # empresa=None pois paciente não pertence a uma empresa específica no cadastro.
        # O paciente será vinculado à empresa no momento da marcação de consulta.
        paciente = Paciente.objects.create(
            empresa=None,
            nome=nome,
            telefone=telefone,
        )
        conta = PacienteConta.objects.create(
            usuario=user,
            telefone=telefone,
            paciente=paciente,
        )

    token, _ = Token.objects.get_or_create(user=user)

    return Response({
        'token': token.key,
        'username': user.username,
        'tipo': 'paciente',
        'paciente_id': conta.paciente.id,
        'paciente_nome': nome,
        'telefone': telefone,
        'mensagem': 'Conta criada com sucesso!',
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_logout_paciente(request):
    """POST /api/auth/logout-paciente/ — Remove o token."""
    try:
        request.user.auth_token.delete()
    except Exception:
        pass
    return Response({'mensagem': 'Logout realizado.'})


# ─────────────────────────────────────────────
# AUTH — LOGIN ATENDENTE (sistema web, mantido)
# ─────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([AllowAny])
def api_login(request):
    """
    POST /api/auth/login/
    Login geral — mantido para compatibilidade.
    """
    username = request.data.get('username', '').strip()
    password = request.data.get('password', '').strip()

    if not username or not password:
        return Response(
            {'erro': 'Informe usuário e senha.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = authenticate(username=username, password=password)

    if not user:
        return Response(
            {'erro': 'Usuário ou senha incorretos.'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    if not user.is_active:
        return Response(
            {'erro': 'Conta bloqueada.'},
            status=status.HTTP_403_FORBIDDEN
        )

    token, _ = Token.objects.get_or_create(user=user)

    empresa_data = None
    try:
        emp = user.perfil.empresa
        empresa_data = {
            'id': emp.id,
            'nome': str(emp),
            'cor_principal': emp.cor_principal,
        }
    except Exception:
        pass

    return Response({
        'token': token.key,
        'username': user.username,
        'empresa': empresa_data,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_logout(request):
    try:
        request.user.auth_token.delete()
    except Exception:
        pass
    return Response({'mensagem': 'Logout realizado.'})


# ─────────────────────────────────────────────
# EMPRESAS
# ─────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([AllowAny])
def api_empresas(request):
    """GET /api/empresas/ — Lista empresas ativas."""
    empresas = Empresa.objects.filter(ativo=True).order_by('nome')
    data = []
    for emp in empresas:
        data.append({
            'id': emp.id,
            'nome': emp.nome,
            'nome_fantasia': emp.nome_fantasia,
            'nome_exibicao': str(emp),
            'telefone': emp.telefone,
            'endereco': emp.endereco,
            'cidade': emp.cidade or '',
            'cor_principal': emp.cor_principal,
        })
    return Response(data)


# ─────────────────────────────────────────────
# ESPECIALIDADES
# ─────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([AllowAny])
def api_especialidades(request):
    """GET /api/especialidades/?empresa_id=X"""
    empresa_id = request.query_params.get('empresa_id')
    qs = Especialidade.objects.filter(ativo=True)

    # SEGURANÇA: atendente só vê especialidades da sua empresa
    if request.user.is_authenticated and _is_atendente(request.user):
        try:
            empresa_id = str(request.user.perfil.empresa.id)
        except Exception:
            pass

    if empresa_id:
        qs = qs.filter(empresa_id=empresa_id)

    data = []
    for esp in qs:
        data.append({
            'id': esp.id,
            'nome': esp.nome,
            'icone': esp.icone,
            'empresa': esp.empresa_id,
            'empresa_nome': str(esp.empresa),
        })
    return Response(data)


# ─────────────────────────────────────────────
# AGENDAS
# ─────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([AllowAny])
def api_agendas(request):
    """GET /api/agendas/?empresa_id=X&especialidade_id=Y"""
    hoje = date.today()
    qs = Agenda.objects.filter(
        vagas_restantes__gt=0,
        data__gte=hoje,          # Nunca retorna datas passadas
    ).select_related('especialidade', 'empresa').order_by('data')

    empresa_id       = request.query_params.get('empresa_id')
    especialidade_id = request.query_params.get('especialidade_id')
    ano              = request.query_params.get('ano')
    mes              = request.query_params.get('mes')

    # SEGURANÇA: atendente só vê agendas da sua empresa
    if request.user.is_authenticated and _is_atendente(request.user):
        try:
            empresa_id = str(request.user.perfil.empresa.id)
        except Exception:
            pass

    if empresa_id:
        qs = qs.filter(empresa_id=empresa_id)
    if especialidade_id:
        qs = qs.filter(especialidade_id=especialidade_id)
    if ano:
        qs = qs.filter(data__year=ano)
    if mes:
        qs = qs.filter(data__month=mes)

    data = []
    for ag in qs:
        data.append({
            'id': ag.id,
            'data': str(ag.data),
            'horario_inicio': str(ag.horario_inicio) if ag.horario_inicio else None,
            'vagas_total': ag.vagas_total,
            'vagas_restantes': ag.vagas_restantes,
            'especialidade': ag.especialidade_id,
            'especialidade_nome': ag.especialidade.nome,
            'especialidade_icone': ag.especialidade.icone,
            'empresa': ag.empresa_id,
            'empresa_nome': str(ag.empresa),
        })
    return Response(data)


# ─────────────────────────────────────────────
# MARCAR CONSULTA
# ─────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([AllowAny])
def api_marcar_consulta(request):
    """
    POST /api/consultas/
    Body: { "agenda_id": X, "nome": "...", "telefone": "..." }

    Se o usuário estiver logado como paciente, vincula a consulta
    ao Paciente da conta dele e atualiza o registro.
    Se não estiver logado, cria normalmente (fluxo atual).
    """
    agenda_id = request.data.get('agenda_id')
    nome      = str(request.data.get('nome', '')).strip()
    telefone  = str(request.data.get('telefone', '')).strip()

    if not agenda_id:
        return Response(
            {'erro': 'agenda_id é obrigatório.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    if not nome:
        return Response(
            {'erro': 'nome é obrigatório.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    if not telefone:
        return Response(
            {'erro': 'telefone é obrigatório.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # SEGURANÇA: atendente não pode marcar consulta via API do paciente
    if request.user.is_authenticated and _is_atendente(request.user) and not _is_paciente(request.user):
        return Response(
            {'erro': 'Atendentes devem usar o sistema web.'},
            status=status.HTTP_403_FORBIDDEN
        )

    try:
        agenda = Agenda.objects.get(id=agenda_id)
    except Agenda.DoesNotExist:
        return Response(
            {'erro': 'Agenda não encontrada.'},
            status=status.HTTP_404_NOT_FOUND
        )

    if agenda.vagas_restantes <= 0:
        return Response(
            {'erro': 'Sem vagas disponíveis.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Backend impede marcação em data passada
    if agenda.data < date.today():
        return Response(
            {'erro': 'Não é possível marcar consulta em data passada.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    with transaction.atomic():
        agenda = Agenda.objects.select_for_update().get(id=agenda_id)
        if agenda.vagas_restantes <= 0:
            return Response(
                {'erro': 'Sem vagas disponíveis.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # SEGURANÇA + RELAÇÃO CORRETA:
        # Se paciente está logado, reutiliza o Paciente permanente da sua conta.
        # Se não está logado, cria novo Paciente (fluxo sem conta).
        paciente = None

        if request.user.is_authenticated and _is_paciente(request.user):
            conta = request.user.paciente_conta

            # Bloqueia marcação em nome de outro paciente
            if conta.paciente:
                # Reutiliza o mesmo Paciente permanente
                paciente = conta.paciente
                # Atualiza nome/telefone se necessário
                atualizado = False
                if paciente.nome != nome:
                    paciente.nome = nome
                    atualizado = True
                if paciente.telefone != telefone:
                    paciente.telefone = telefone
                    atualizado = True
                if atualizado:
                    paciente.save()
            else:
                # Cria Paciente e vincula permanentemente à conta
                paciente = Paciente.objects.create(
                    empresa=agenda.empresa,
                    nome=nome,
                    telefone=telefone,
                )
                conta.paciente = paciente
                conta.save()
     
            else:
                # Sem login: busca paciente existente pelo telefone e nome, ou cria um novo
                paciente, created = Paciente.objects.get_or_create(
                    telefone=telefone,
                    nome=nome,
                    defaults={'empresa': agenda.empresa}
                )

        ultima = Consulta.objects.filter(agenda=agenda).order_by('-ficha').first()
        ficha = (ultima.ficha + 1) if ultima else 1

        consulta = Consulta.objects.create(
            paciente=paciente,
            agenda=agenda,
            ficha=ficha,
            status='esperando',
        )

        agenda.vagas_restantes -= 1
        agenda.save()

    return Response({
        'consulta_id': consulta.id,
        'ficha': ficha,
        'nome': nome,
        'telefone': telefone,
        'status': consulta.status,
        'agenda_id': agenda.id,
        'agenda_data': str(agenda.data),
        'especialidade': agenda.especialidade.nome,
        'especialidade_icone': agenda.especialidade.icone,
        'empresa': str(agenda.empresa),
        'vagas_restantes': agenda.vagas_restantes,
    }, status=status.HTTP_201_CREATED)


# ─────────────────────────────────────────────
# DETALHE DA CONSULTA
# ─────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_consulta_detalhe(request, consulta_id):
    """GET /api/consultas/<id>/ — Detalhe + posição na fila.
    Requer autenticação. Paciente só acessa sua própria consulta.
    Atendente só acessa consultas da sua empresa."""
    try:
        consulta = Consulta.objects.select_related(
            'paciente', 'agenda', 'agenda__especialidade', 'agenda__empresa'
        ).get(id=consulta_id)
    except Consulta.DoesNotExist:
        return Response(
            {'erro': 'Consulta não encontrada.'},
            status=status.HTTP_404_NOT_FOUND
        )

    # SEGURANÇA: paciente autenticado só acessa sua própria consulta
    if request.user.is_authenticated and _is_paciente(request.user):
        conta = request.user.paciente_conta
        if conta.paciente and consulta.paciente != conta.paciente:
            return Response(
                {'erro': 'Acesso negado.'},
                status=status.HTTP_403_FORBIDDEN
            )

    fila = Consulta.objects.filter(
        agenda=consulta.agenda, status='esperando'
    ).order_by('ficha')
    pessoas_frente = fila.filter(ficha__lt=consulta.ficha).count()

    em_atendimento = Consulta.objects.filter(
        agenda=consulta.agenda, status='em_atendimento'
    ).first()

    return Response({
        'id': consulta.id,
        'ficha': consulta.ficha,
        'status': consulta.status,
        'paciente_nome': consulta.paciente.nome,
        'paciente_telefone': consulta.paciente.telefone,
        'agenda_id': consulta.agenda.id,
        'agenda_data': str(consulta.agenda.data),
        'agenda_horario': str(consulta.agenda.horario_inicio)
            if consulta.agenda.horario_inicio else None,
        'especialidade_nome': consulta.agenda.especialidade.nome,
        'especialidade_icone': consulta.agenda.especialidade.icone,
        'empresa_nome': str(consulta.agenda.empresa),
        'empresa_cor': consulta.agenda.empresa.cor_principal,
        'pessoas_frente': pessoas_frente,
        'ficha_em_atendimento': em_atendimento.ficha if em_atendimento else None,
    })


# ─────────────────────────────────────────────
# FILA
# ─────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_fila(request, agenda_id):
    """GET /api/fila/<agenda_id>/ — Estado atual da fila.
    Requer autenticação. Atendente só acessa fila da sua empresa."""
    try:
        agenda = Agenda.objects.select_related(
            'especialidade', 'empresa'
        ).get(id=agenda_id)
    except Agenda.DoesNotExist:
        return Response(
            {'erro': 'Agenda não encontrada.'},
            status=status.HTTP_404_NOT_FOUND
        )

    # SEGURANÇA: atendente autenticado só acessa agenda da sua empresa
    if request.user.is_authenticated and _is_atendente(request.user):
        try:
            empresa_user = request.user.perfil.empresa
            if agenda.empresa != empresa_user:
                return Response(
                    {'erro': 'Acesso negado.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        except Exception:
            pass

    em_atendimento = Consulta.objects.filter(
        agenda=agenda, status='em_atendimento'
    ).select_related('paciente').first()

    proximos = Consulta.objects.filter(
        agenda=agenda, status='esperando'
    ).select_related('paciente').order_by('ficha')[:5]

    return Response({
        'agenda_id': agenda.id,
        'especialidade': agenda.especialidade.nome,
        'empresa': str(agenda.empresa),
        'data': str(agenda.data),
        'em_atendimento': {
            'id': em_atendimento.id,
            'ficha': em_atendimento.ficha,
            'paciente_nome': em_atendimento.paciente.nome,
        } if em_atendimento else None,
        'proximos': [
            {'id': c.id, 'ficha': c.ficha, 'paciente_nome': c.paciente.nome}
            for c in proximos
        ],
        'total_espera': Consulta.objects.filter(
            agenda=agenda, status='esperando').count(),
        'total_atendidos': Consulta.objects.filter(
            agenda=agenda, status='atendido').count(),
    })


# ─────────────────────────────────────────────
# PERFIL DO PACIENTE LOGADO
# ─────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_perfil_paciente(request):
    """
    GET /api/perfil-paciente/
    Retorna dados do paciente logado.
    Só funciona para contas de paciente.
    """
    user = request.user

    if not _is_paciente(user):
        return Response(
            {'erro': 'Acesso negado. Esta rota é exclusiva para pacientes.'},
            status=status.HTTP_403_FORBIDDEN
        )

    conta = user.paciente_conta
    paciente = conta.paciente

    return Response({
        'username': user.username,
        'nome': paciente.nome if paciente else user.first_name,
        'telefone': conta.telefone,
        'paciente_id': paciente.id if paciente else None,
    })


# ─────────────────────────────────────────────
# MINHAS CONSULTAS
# ─────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_minhas_consultas(request):
    """
    GET /api/minhas-consultas/
    Lista consultas do paciente logado.
    Só funciona para contas de paciente.
    """
    user = request.user

    if not _is_paciente(user):
        return Response(
            {'erro': 'Acesso negado.'},
            status=status.HTTP_403_FORBIDDEN
        )

    conta = user.paciente_conta
    if not conta.paciente:
        return Response([])

    consultas = Consulta.objects.filter(
        paciente=conta.paciente
    ).select_related(
        'paciente', 'agenda', 'agenda__especialidade', 'agenda__empresa'
    ).order_by('-agenda__data', '-ficha')[:20]

    data = []
    for c in consultas:
        pode_cancelar = c.status in ('esperando', 'ausente')
        data.append({
            'id': c.id,
            'ficha': c.ficha,
            'status': c.status,
            'agenda_id': c.agenda.id,
            'agenda_data': str(c.agenda.data),
            'agenda_horario': str(c.agenda.horario_inicio) if c.agenda.horario_inicio else None,
            'especialidade_nome': c.agenda.especialidade.nome,
            'especialidade_icone': c.agenda.especialidade.icone,
            'empresa_nome': str(c.agenda.empresa),
            'pode_cancelar': pode_cancelar,
        })
    return Response(data)


# ─────────────────────────────────────────────
# BUSCA — Pesquisa por especialidade
# ─────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_busca(request):
    """
    GET /api/busca/?q=ultrassom
    Busca agendas disponíveis por nome de especialidade.
    Retorna resultados ordenados pela data mais próxima.
    Requer autenticação (paciente logado).
    """
    q = request.query_params.get('q', '').strip()

    if not q or len(q) < 2:
        return Response(
            {'erro': 'Informe ao menos 2 caracteres para pesquisar.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    cidade = request.query_params.get('cidade', '').strip()

    # Busca agendas com vagas onde a especialidade bate com a pesquisa
    hoje = date.today()
    qs = Agenda.objects.filter(
        vagas_restantes__gt=0,
        data__gte=hoje,                      # Nunca retorna datas passadas
        especialidade__nome__icontains=q,
    ).select_related(
        'especialidade', 'empresa'
    )

    # Filtro opcional por cidade
    if cidade:
        qs = qs.filter(empresa__cidade__icontains=cidade)

    agendas = qs.order_by('data')  # Data mais próxima primeiro

    data = []
    for ag in agendas:
        data.append({
            'agenda_id': ag.id,
            'data': str(ag.data),
            'horario_inicio': str(ag.horario_inicio) if ag.horario_inicio else None,
            'vagas_restantes': ag.vagas_restantes,
            'especialidade_id': ag.especialidade_id,
            'especialidade_nome': ag.especialidade.nome,
            'especialidade_icone': ag.especialidade.icone,
            'empresa_id': ag.empresa_id,
            'empresa_nome': str(ag.empresa),
            'empresa_endereco': ag.empresa.endereco or '',
            'empresa_cidade': ag.empresa.cidade or '',
        })

    return Response(data)


# ─────────────────────────────────────────────
# CANCELAR CONSULTA
# ─────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_cancelar_consulta(request, consulta_id):
    """
    POST /api/consultas/<id>/cancelar/
    Cancela a consulta do paciente autenticado.
    Segurança: só o dono da consulta pode cancelar.
    Libera a vaga na agenda correspondente.
    """
    user = request.user

    if not _is_paciente(user):
        return Response(
            {'erro': 'Acesso negado.'},
            status=status.HTTP_403_FORBIDDEN
        )

    conta = user.paciente_conta
    if not conta.paciente:
        return Response(
            {'erro': 'Paciente não encontrado.'},
            status=status.HTTP_404_NOT_FOUND
        )

    try:
        consulta = Consulta.objects.select_related('agenda').get(id=consulta_id)
    except Consulta.DoesNotExist:
        return Response(
            {'erro': 'Consulta não encontrada.'},
            status=status.HTTP_404_NOT_FOUND
        )

    # SEGURANÇA: verifica que a consulta pertence ao paciente autenticado
    if consulta.paciente != conta.paciente:
        return Response(
            {'erro': 'Acesso negado.'},
            status=status.HTTP_403_FORBIDDEN
        )

    # Só permite cancelar consultas que ainda estão na fila
    if consulta.status not in ('esperando', 'ausente'):
        return Response(
            {'erro': f'Não é possível cancelar uma consulta com status "{consulta.status}".'},
            status=status.HTTP_400_BAD_REQUEST
        )

    with transaction.atomic():
        # Libera a vaga na agenda
        agenda = consulta.agenda
        agenda.vagas_restantes += 1
        agenda.save()

        # Marca a consulta como cancelada
        consulta.status = 'faltou'
        consulta.save()

    return Response({'mensagem': 'Consulta cancelada com sucesso.'})


# ─────────────────────────────────────────────
# CIDADES — lista de cidades com agendas disponíveis
# ─────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_cidades(request):
    """
    GET /api/cidades/?q=medico
    Retorna lista de cidades distintas que possuem agendas
    disponíveis para a especialidade pesquisada.
    """
    q = request.query_params.get('q', '').strip()
    hoje = date.today()

    qs = Agenda.objects.filter(
        vagas_restantes__gt=0,
        data__gte=hoje,
    )
    if q and len(q) >= 2:
        qs = qs.filter(especialidade__nome__icontains=q)

    cidades = (
        qs.select_related('empresa')
        .values_list('empresa__cidade', flat=True)
        .distinct()
        .order_by('empresa__cidade')
    )

    return Response([c for c in cidades if c])  # remove vazios
