from django.contrib import admin
from .models import Empresa, PerfilUsuario, Especialidade, Agenda, Paciente, Consulta, PacienteConta


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display  = ['nome', 'nome_fantasia', 'cidade', 'telefone', 'ativo']
    list_filter   = ['ativo', 'cidade']
    search_fields = ['nome', 'nome_fantasia', 'cidade']
    fields = [
        'nome', 'nome_fantasia', 'logo',
        'telefone', 'endereco', 'cidade',
        'cor_principal', 'ativo',
    ]


admin.site.register(PerfilUsuario)
admin.site.register(PacienteConta)
admin.site.register(Especialidade)
admin.site.register(Agenda)
admin.site.register(Paciente)
admin.site.register(Consulta)
