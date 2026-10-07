from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    """
    Torna empresa opcional no Paciente.
    Necessário para suportar pacientes criados pelo app
    que ainda não têm empresa definida no cadastro.
    Não altera dados existentes.
    """

    dependencies = [
        ('consultas', '0003_consulta_preferencial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='paciente',
            name='empresa',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='pacientes',
                to='consultas.empresa',
            ),
        ),
    ]
