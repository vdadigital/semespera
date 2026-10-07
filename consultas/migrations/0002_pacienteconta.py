from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('consultas', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PacienteConta',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                    serialize=False, verbose_name='ID')),
                ('telefone', models.CharField(blank=True, max_length=20)),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('usuario', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='paciente_conta',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('paciente', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='conta',
                    to='consultas.paciente',
                )),
            ],
            options={
                'verbose_name': 'Conta de Paciente',
                'verbose_name_plural': 'Contas de Pacientes',
            },
        ),
    ]
