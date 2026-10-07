from django.db import models
from django.contrib.auth.models import User


# ──────────────────────────────────────────
# EMPRESA
# ──────────────────────────────────────────

class Empresa(models.Model):
    nome = models.CharField(max_length=200)
    nome_fantasia = models.CharField(max_length=200, blank=True, null=True)
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True)
    endereco = models.CharField(max_length=300, blank=True)
    cidade = models.CharField(max_length=100, blank=True)
    cor_principal = models.CharField(max_length=7, default='#1a3a8f')
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome_fantasia or self.nome

    class Meta:
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'


# ──────────────────────────────────────────
# PERFIL DO USUÁRIO (vincula User à Empresa)
# ──────────────────────────────────────────

class PerfilUsuario(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='usuarios')

    def __str__(self):
        return f'{self.usuario.username} – {self.empresa}'

    class Meta:
        verbose_name = 'Perfil de Usuário'
        verbose_name_plural = 'Perfis de Usuários'


# ──────────────────────────────────────────
# ESPECIALIDADE (dinâmica por empresa)
# ──────────────────────────────────────────

class Especialidade(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='especialidades')
    nome = models.CharField(max_length=100)
    icone = models.CharField(max_length=10, default='🩺')
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.nome} ({self.empresa})'

    class Meta:
        verbose_name = 'Especialidade'
        verbose_name_plural = 'Especialidades'
        ordering = ['nome']


# ──────────────────────────────────────────
# AGENDA
# ──────────────────────────────────────────

class Agenda(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='agendas')
    especialidade = models.ForeignKey(Especialidade, on_delete=models.CASCADE, related_name='agendas')
    data = models.DateField()
    vagas_total = models.IntegerField()
    vagas_restantes = models.IntegerField()
    horario_inicio = models.TimeField(null=True, blank=True)

    def __str__(self):
        return f'{self.especialidade.nome} – {self.data}'

    class Meta:
        verbose_name = 'Agenda'
        verbose_name_plural = 'Agendas'


# ──────────────────────────────────────────
# PACIENTE
# ──────────────────────────────────────────

class Paciente(models.Model):
    empresa = models.ForeignKey(
        Empresa, on_delete=models.CASCADE,
        related_name='pacientes', null=True, blank=True
    )
    nome = models.CharField(max_length=100)
    telefone = models.CharField(max_length=20)

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = 'Paciente'
        verbose_name_plural = 'Pacientes'


# ──────────────────────────────────────────
# CONSULTA
# ──────────────────────────────────────────

class Consulta(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)
    agenda = models.ForeignKey(Agenda, on_delete=models.CASCADE)
    ficha = models.IntegerField()

    STATUS = [
        ('esperando', 'Esperando'),
        ('em_atendimento', 'Em Atendimento'),
        ('ausente', 'Ausente Temporário'),
        ('atendido', 'Atendido'),
        ('faltou', 'Faltou'),
    ]

    status = models.CharField(max_length=20, choices=STATUS, default='esperando')
    tentativas = models.IntegerField(default=0)
    ordem_chamada = models.IntegerField(default=0)
    preferencial = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.paciente} – Ficha {self.ficha}'

    class Meta:
        verbose_name = 'Consulta'
        verbose_name_plural = 'Consultas'
        constraints = [
            models.UniqueConstraint(
                fields=['agenda', 'ficha'],
                name='ficha_unica_por_agenda'
            )
        ]


# ──────────────────────────────────────────
# PACIENTE CONTA (login do paciente no app)
# ──────────────────────────────────────────

class PacienteConta(models.Model):
    """
    Vincula um User Django a um Paciente.
    Separado do PerfilUsuario (que vincula User a Empresa/atendente).
    Um User com PacienteConta NÃO deve ter PerfilUsuario.
    """
    usuario = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='paciente_conta'
    )
    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE,
        related_name='conta',
        null=True,
        blank=True,
    )
    telefone = models.CharField(max_length=20, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Paciente: {self.usuario.username}'

    class Meta:
        verbose_name = 'Conta de Paciente'
        verbose_name_plural = 'Contas de Pacientes'
