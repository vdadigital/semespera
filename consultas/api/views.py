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
    if ano
