"""
serializers.py — Serializers da API REST do Sem Espera.
Converte os models Django em JSON para o app Flutter.
Não altera nenhuma funcionalidade existente do sistema web.
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from consultas.models import Empresa, Especialidade, Agenda, Paciente, Consulta


# ──────────────────────────────────────────
# EMPRESA
# ──────────────────────────────────────────

class EmpresaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empresa
        fields = ['id', 'nome', 'nome_fantasia', 'telefone', 'endereco',
                  'cor_principal', 'logo', 'ativo']


# ──────────────────────────────────────────
# ESPECIALIDADE
# ──────────────────────────────────────────

class EspecialidadeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Especialidade
        fields = ['id', 'nome', 'icone', 'empresa']


# ──────────────────────────────────────────
# AGENDA
# ──────────────────────────────────────────

class AgendaSerializer(serializers.ModelSerializer):
    especialidade_nome = serializers.CharField(source='especialidade.nome', read_only=True)
    especialidade_icone = serializers.CharField(source='especialidade.icone', read_only=True)
    empresa_nome = serializers.CharField(source='empresa.__str__', read_only=True)

    class Meta:
        model = Agenda
        fields = [
            'id', 'data', 'horario_inicio',
            'vagas_total', 'vagas_restantes',
            'especialidade', 'especialidade_nome', 'especialidade_icone',
            'empresa', 'empresa_nome',
        ]


# ──────────────────────────────────────────
# PACIENTE
# ──────────────────────────────────────────

class PacienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Paciente
        fields = ['id', 'nome', 'telefone']


# ──────────────────────────────────────────
# CONSULTA — listagem na fila
# ──────────────────────────────────────────

class ConsultaFilaSerializer(serializers.ModelSerializer):
    paciente_nome = serializers.CharField(source='paciente.nome', read_only=True)

    class Meta:
        model = Consulta
        fields = ['id', 'ficha', 'status', 'paciente_nome', 'ordem_chamada']


# ──────────────────────────────────────────
# CONSULTA — detalhe para o paciente
# ──────────────────────────────────────────

class ConsultaDetalheSerializer(serializers.ModelSerializer):
    paciente_nome = serializers.CharField(source='paciente.nome', read_only=True)
    paciente_telefone = serializers.CharField(source='paciente.telefone', read_only=True)
    agenda_data = serializers.DateField(source='agenda.data', read_only=True)
    agenda_horario = serializers.TimeField(source='agenda.horario_inicio', read_only=True)
    especialidade_nome = serializers.CharField(
        source='agenda.especialidade.nome', read_only=True)
    especialidade_icone = serializers.CharField(
        source='agenda.especialidade.icone', read_only=True)
    empresa_nome = serializers.CharField(
        source='agenda.empresa.__str__', read_only=True)
    empresa_cor = serializers.CharField(
        source='agenda.empresa.cor_principal', read_only=True)

    class Meta:
        model = Consulta
        fields = [
            'id', 'ficha', 'status',
            'paciente_nome', 'paciente_telefone',
            'agenda_data', 'agenda_horario',
            'especialidade_nome', 'especialidade_icone',
            'empresa_nome', 'empresa_cor',
        ]


# ──────────────────────────────────────────
# MARCAR CONSULTA — input do app
# ──────────────────────────────────────────

class MarcarConsultaSerializer(serializers.Serializer):
    agenda_id = serializers.IntegerField()
    nome = serializers.CharField(max_length=100)
    telefone = serializers.CharField(max_length=20)


# ──────────────────────────────────────────
# FILA — estado completo para o app
# ──────────────────────────────────────────

class FilaSerializer(serializers.Serializer):
    agenda_id = serializers.IntegerField()
    especialidade = serializers.CharField()
    empresa = serializers.CharField()
    data = serializers.DateField()
    em_atendimento = ConsultaFilaSerializer(allow_null=True)
    proximos = ConsultaFilaSerializer(many=True)
    total_espera = serializers.IntegerField()
    total_atendidos = serializers.IntegerField()
