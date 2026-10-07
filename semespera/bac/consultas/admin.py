from django.contrib import admin
from .models import Empresa, PerfilUsuario, Especialidade, Agenda, Paciente, Consulta

admin.site.register(Empresa)
admin.site.register(PerfilUsuario)
admin.site.register(Especialidade)
admin.site.register(Agenda)
admin.site.register(Paciente)
admin.site.register(Consulta)
