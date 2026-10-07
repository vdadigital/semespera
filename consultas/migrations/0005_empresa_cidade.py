from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('consultas', '0004_paciente_empresa_opcional'),
    ]

    operations = [
        migrations.AddField(
            model_name='empresa',
            name='cidade',
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
